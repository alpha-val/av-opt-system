import { createSlice, createAsyncThunk, createSelector } from '@reduxjs/toolkit';

const API_BASE_URL = 'http://localhost:8000/api/v1';

// Helper functions (keep existing ones)
const getAuthToken = () => {
    return localStorage.getItem('access_token');
};

const getAuthHeaders = (includeContentType = false) => {
    const token = getAuthToken();
    const headers = {
        'Authorization': `Bearer ${token}`,
    };

    if (includeContentType) {
        headers['Content-Type'] = 'application/json';
    }

    return headers;
};

const getUserId = () => {
    const userId = localStorage.getItem('user_id');
    if (userId) return userId;

    const token = getAuthToken();
    if (token) {
        try {
            const payload = JSON.parse(atob(token.split('.')[1]));
            return payload.sub || payload.user_id || payload.id;
        } catch (error) {
            console.warn('Could not decode user ID from token:', error);
        }
    }
    return null;
};

// Async thunks (simplified to work with new structure)
export const uploadProjectDescription = createAsyncThunk(
    'data/uploadProjectDescription',
    async ({ projectId, file, metadata = {} }, { rejectWithValue }) => {
        try {
            const token = getAuthToken();
            if (!token) {
                throw new Error('No authentication token found');
            }

            const userId = getUserId();
            if (!userId) {
                throw new Error('No user ID found');
            }

            if (file.type !== 'application/pdf') {
                throw new Error('Only PDF files are allowed for project descriptions');
            }

            const formData = new FormData();
            formData.append('file', file);
            formData.append('user_id', userId);
            formData.append('project_id', projectId);
            formData.append('document_type', 'base_case'); // Set document type

            if (metadata.description) {
                formData.append('description', metadata.description);
            }

            const response = await fetch(`${API_BASE_URL}/etl_base_case`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                },
                body: formData,
            });

            if (!response.ok) {
                const errorText = await response.text();
                let errorData;
                try {
                    errorData = JSON.parse(errorText);
                } catch (e) {
                    throw new Error(`HTTP error! status: ${response.status}, message: ${errorText}`);
                }
                throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
            }

            const data = await response.json();

            return {
                doc_id: data.doc_id,
                fileName: file.name,
                originalName: file.name,
                fileSize: file.size,
                fileType: 'pdf',
                document_type: 'base_case',
                processing_status: 'completed',
                project_id: projectId,
                user_id: userId,
                created_at: new Date().toISOString(),
                active: true,
            };
        } catch (error) {
            console.error("Upload error:", error);
            return rejectWithValue(error.message);
        }
    }
);

export const uploadStructuredData = createAsyncThunk(
    'data/uploadStructuredData',
    async ({ projectId, file, metadata = {} }, { rejectWithValue }) => {
        try {
            const token = getAuthToken();
            if (!token) {
                throw new Error('No authentication token found');
            }

            const userId = getUserId();
            if (!userId) {
                throw new Error('No user ID found');
            }

            const allowedTypes = [
                'application/pdf',
                'application/vnd.ms-excel',
                'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                'text/csv',
                '.xlsx',
                '.xls',
                '.csv'
            ];

            const isValidType = allowedTypes.some(type =>
                file.type === type || file.name.toLowerCase().endsWith(type)
            );

            if (!isValidType) {
                throw new Error('Only PDF, Excel (.xlsx, .xls), and CSV files are allowed for structured data');
            }

            const formData = new FormData();
            formData.append('file', file);
            formData.append('user_id', userId);
            formData.append('project_id', projectId);
            formData.append('data_type', 'scenario'); // Set document type for structured data

            if (metadata.description) {
                formData.append('description', metadata.description);
            }

            const response = await fetch(`${API_BASE_URL}/etl_ingest_tables`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                },
                body: formData,
            });

            if (!response.ok) {
                const errorText = await response.text();
                let errorData;
                try {
                    errorData = JSON.parse(errorText);
                } catch (e) {
                    throw new Error(`HTTP error! status: ${response.status}, message: ${errorText}`);
                }
                throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
            }

            const data = await response.json();

            return {
                doc_id: data.doc_id,
                fileName: file.name,
                originalName: file.name,
                fileSize: file.size,
                fileType: file.name.toLowerCase().endsWith('.pdf') ? 'pdf' :
                    file.name.toLowerCase().includes('.xls') ? 'xls' : 'csv',
                document_type: 'scenario',
                processing_status: 'completed',
                project_id: projectId,
                user_id: userId,
                created_at: new Date().toISOString(),
                active: true,
            };
        } catch (error) {
            console.error("Upload error:", error);
            return rejectWithValue(error.message);
        }
    }
);

export const fetchProjectDocuments = createAsyncThunk(
    'data/fetchProjectDocuments',
    async ({ projectId, document_type = null, page = 1, limit = 50 }, { rejectWithValue }) => {
        try {
            console.log('Fetching documents for project:', projectId);

            const token = getAuthToken();
            if (!token) {
                throw new Error('No authentication token found');
            }

            const params = new URLSearchParams();
            if (document_type) params.append('document_type', document_type);
            params.append('page', page.toString());
            params.append('limit', limit.toString());

            const response = await fetch(`${API_BASE_URL}/projects/${projectId}/documents?${params}`, {
                method: 'GET',
                headers: getAuthHeaders(true),
            });

            if (!response.ok) {
                const errorData = await response.json();
                console.error('Error response:', errorData);
                throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
            }

            const data = await response.json();

            if (!data) {
                console.warn('Received null response from backend');
                return {
                    projectId,
                    documents: [],
                    totalDocuments: 0,
                };
            }

            return {
                projectId,
                documents: data.documents || [],
                totalDocuments: data.total_documents || 0,
            };

        } catch (error) {
            console.error('fetchProjectDocuments error:', error);
            return rejectWithValue(error.message);
        }
    }
);

export const deleteProjectDocument = createAsyncThunk(
    'data/deleteProjectDocument',
    async ({ projectId, docId }, { rejectWithValue }) => {
        try {
            const token = getAuthToken();
            if (!token) {
                throw new Error('No authentication token found');
            }

            const response = await fetch(`${API_BASE_URL}/projects/${projectId}/documents/${docId}`, {
                method: 'DELETE',
                headers: getAuthHeaders(true),
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
            }

            return { projectId, docId };
        } catch (error) {
            return rejectWithValue(error.message);
        }
    }
);

// Simplified initial state
const initialState = {
    documents: [], // Single array for all documents
    currentProjectId: null,
    loading: {
        uploadBase: false,
        uploadTabularData: false,
        fetchDocuments: false,
        deleteDocument: false,
    },
    progress: {
        upload: 0,
    },
    error: null,
};

// Simplified slice
const dataSlice = createSlice({
    name: 'data',
    initialState,
    reducers: {
        clearError: (state) => {
            state.error = null;
        },
        setCurrentProject: (state, action) => {
            state.currentProjectId = action.payload;
        },
        clearDocuments: (state) => {
            state.documents = [];
            state.currentProjectId = null;
        },
    },
    extraReducers: (builder) => {
        builder
            // Upload base case
            .addCase(uploadProjectDescription.pending, (state) => {
                state.loading.uploadBase = true;
                state.error = null;
                state.progress.upload = 0;
            })
            .addCase(uploadProjectDescription.fulfilled, (state, action) => {
                state.loading.uploadBase = false;
                state.progress.upload = 100;
                state.documents.push(action.payload);
                state.error = null;
            })
            .addCase(uploadProjectDescription.rejected, (state, action) => {
                state.loading.uploadBase = false;
                state.progress.upload = 0;
                state.error = action.payload;
            })

            // Upload scenario
            .addCase(uploadStructuredData.pending, (state) => {
                state.loading.uploadTabularData = true;
                state.error = null;
                state.progress.upload = 0;
            })
            .addCase(uploadStructuredData.fulfilled, (state, action) => {
                state.loading.uploadTabularData = false;
                state.progress.upload = 100;
                state.documents.push(action.payload);
                state.error = null;
            })
            .addCase(uploadStructuredData.rejected, (state, action) => {
                state.loading.uploadTabularData = false;
                state.progress.upload = 0;
                state.error = action.payload;
            })

            // Fetch documents
            .addCase(fetchProjectDocuments.pending, (state) => {
                state.loading.fetchDocuments = true;
                state.error = null;
            })
            .addCase(fetchProjectDocuments.fulfilled, (state, action) => {
                state.loading.fetchDocuments = false;
                state.documents = action.payload.documents;
                state.currentProjectId = action.payload.projectId;
                state.error = null;
            })
            .addCase(fetchProjectDocuments.rejected, (state, action) => {
                state.loading.fetchDocuments = false;
                state.error = action.payload;
            })

            // Delete document
            .addCase(deleteProjectDocument.fulfilled, (state, action) => {
                const { docId } = action.payload;
                state.documents = state.documents.filter(doc => doc.doc_id !== docId);
            });
    },
});

// Export actions
export const { clearError, setCurrentProject, clearDocuments } = dataSlice.actions;

// Simplified selectors
export const selectAllDocuments = (state) => state.data.documents;
export const selectCurrentProjectId = (state) => state.data.currentProjectId;
export const selectDataLoading = (state) => state.data.loading;
export const selectDataProgress = (state) => state.data.progress;
export const selectDataError = (state) => state.data.error;

// Memoized selectors that derive data
export const selectBaseCaseDocuments = createSelector(
    [selectAllDocuments],
    (documents) => documents.filter(doc => doc.document_type === 'base_case')
);

export const selectTabularDataDocuments = createSelector(
    [selectAllDocuments],
    (documents) => documents.filter(doc => doc.document_type === 'scenario')
);

export const selectDocumentsByType = createSelector(
    [selectAllDocuments, (state, documentType) => documentType],
    (documents, documentType) => documents.filter(doc => doc.document_type === documentType)
);

// Additional memoized selectors for document counts
export const selectBaseCaseCount = createSelector(
    [selectBaseCaseDocuments],
    (baseCaseDocuments) => baseCaseDocuments.length
);

export const selectTabularDataCount = createSelector(
    [selectTabularDataDocuments],
    (scenarioDocuments) => scenarioDocuments.length
);

export const selectTotalDocumentCount = createSelector(
    [selectAllDocuments],
    (documents) => documents.length
);

// Selector for documents by processing status
export const selectDocumentsByStatus = createSelector(
    [selectAllDocuments, (state, status) => status],
    (documents, status) => documents.filter(doc => doc.processing_status === status)
);

// Selector for completed documents only
export const selectCompletedDocuments = createSelector(
    [selectAllDocuments],
    (documents) => documents.filter(doc => doc.processing_status === 'completed')
);

export default dataSlice.reducer;