import {
  createSlice,
  createAsyncThunk,
  createSelector,
} from "@reduxjs/toolkit";

import REACT_APP_CONFIG from "../AppConfig";

const API_BASE_URL = REACT_APP_CONFIG.url.API_URL;

// Helper function to get auth token
const getAuthToken = () => {
  return localStorage.getItem("access_token");
};

// Helper function to get user ID
const getUserId = () => {
  return localStorage.getItem("user_id");
};

// Helper function to create auth headers for JSON requests
const getAuthHeaders = () => {
  const token = getAuthToken();
  return {
    "Content-Type": "application/json",
    Authorization: `Bearer ${token}`,
  };
};

// Helper function to create auth headers for file uploads (no Content-Type, browser sets it)
const getAuthHeadersForUpload = () => {
  const token = getAuthToken();
  return {
    Authorization: `Bearer ${token}`,
  };
};

// Fetch all documents
export const fetchDocuments = createAsyncThunk(
  "documents/fetchDocuments",
  async (_, { rejectWithValue }) => {
    try {
      const response = await fetch(`${API_BASE_URL}/documents/`, {
        headers: getAuthHeaders(),
      });
      if (!response.ok) {
        throw new Error("Failed to fetch documents");
      }
      const data = await response.json();
      return data;
    } catch (error) {
      return rejectWithValue(error.message);
    }
  }
);

// Fetch documents by project ID
export const fetchDocumentsByProject = createAsyncThunk(
  "documents/fetchDocumentsByProject",
  async (projectId, { rejectWithValue }) => {
    try {
      // Assuming the backend supports filtering by project_id
      // If not, we'll filter on the frontend after fetching all
      const response = await fetch(`${API_BASE_URL}/documents/`, {
        headers: getAuthHeaders(),
      });
      if (!response.ok) {
        throw new Error("Failed to fetch documents");
      }
      const data = await response.json();
      // Filter by project_id on frontend if backend doesn't support it
      const filteredData = Array.isArray(data)
        ? data.filter((doc) => doc.project_id === projectId)
        : [];
      // Return both the filtered data and projectId so reducer can use it even if array is empty
      return { documents: filteredData, projectId };
    } catch (error) {
      return rejectWithValue(error.message);
    }
  }
);

// Fetch document by ID
export const fetchDocumentById = createAsyncThunk(
  "documents/fetchDocumentById",
  async (documentId, { rejectWithValue }) => {
    try {
      const response = await fetch(`${API_BASE_URL}/documents/${documentId}/`, {
        headers: getAuthHeaders(),
      });
      if (!response.ok) {
        throw new Error("Failed to fetch document");
      }
      const data = await response.json();
      return data;
    } catch (error) {
      return rejectWithValue(error.message);
    }
  }
);

// Ingest base case document
export const ingestBaseCaseDocument = createAsyncThunk(
  "documents/ingestBaseCaseDocument",
  async ({ file, projectId, artifactType, metadata = {} }, { rejectWithValue, dispatch }) => {
    return new Promise((resolve, reject) => {
      try {
        const formData = new FormData();
        formData.append("file", file);
        formData.append("project_id", projectId);
        formData.append("artifact_type", artifactType);
        formData.append("metadata", JSON.stringify(metadata));
        
        const xhr = new XMLHttpRequest();
        const url = `${API_BASE_URL}/etl/base-case`;
        
        // Track upload progress
        xhr.upload.addEventListener("progress", (e) => {
          if (e.lengthComputable) {
            const percentComplete = Math.round((e.loaded / e.total) * 100);
            dispatch(setUploadProgress(percentComplete));
          }
        });
        
        xhr.addEventListener("load", () => {
          if (xhr.status >= 200 && xhr.status < 300) {
            try {
              const data = JSON.parse(xhr.responseText);
              dispatch(setUploadProgress(100));
              resolve(data);
            } catch (e) {
              dispatch(setUploadProgress(0));
              reject(rejectWithValue("Failed to parse response"));
            }
          } else {
            dispatch(setUploadProgress(0));
            let errorData;
            try {
              errorData = JSON.parse(xhr.responseText);
            } catch (e) {
              reject(rejectWithValue(`HTTP error! status: ${xhr.status}`));
              return;
            }
            reject(rejectWithValue(errorData.detail || `HTTP error! status: ${xhr.status}`));
          }
        });
        
        xhr.addEventListener("error", () => {
          dispatch(setUploadProgress(0));
          reject(rejectWithValue("Network error occurred"));
        });
        
        xhr.addEventListener("abort", () => {
          dispatch(setUploadProgress(0));
          reject(rejectWithValue("Upload aborted"));
        });
        
        // Open request first, then set headers
        xhr.open("POST", url);
        
        // Set headers after opening
        const token = getAuthToken();
        if (token) {
          xhr.setRequestHeader("Authorization", `Bearer ${token}`);
        }
        
        xhr.send(formData);
      } catch (error) {
        dispatch(setUploadProgress(0));
        reject(rejectWithValue(error.message));
      }
    });
  }
);

// Upload document with file
export const uploadDocument = createAsyncThunk(
  "documents/uploadDocument",
  async ({ file, projectId, artifactType, metadata = {} }, { rejectWithValue, dispatch }) => {
    return new Promise((resolve, reject) => {
      try {
        const token = getAuthToken();
        if (!token) {
          reject(rejectWithValue("No authentication token found"));
          return;
        }

        const userId = getUserId();

        // Create FormData for file upload
        const formData = new FormData();
        formData.append("file", file);
        formData.append("file_name", file.name);
        formData.append("title", metadata.title || file.name);
        formData.append("project_id", projectId);

        if (userId) {
          formData.append("user_id", userId);
        }

        if (artifactType) {
          formData.append("artifact_type", artifactType);
        }

        if (metadata.type) {
          formData.append("type", metadata.type);
        }

        if (metadata.tags && Array.isArray(metadata.tags)) {
          metadata.tags.forEach((tag) => {
            formData.append("tags", tag);
          });
        }

        // Add any additional metadata
        if (metadata.metadata && typeof metadata.metadata === "object") {
          formData.append("metadata", JSON.stringify(metadata.metadata));
        }

        if (file.size) {
          formData.append("size", file.size.toString());
        }

        const xhr = new XMLHttpRequest();
        const url = `${API_BASE_URL}/documents/`;
        
        // Track upload progress
        xhr.upload.addEventListener("progress", (e) => {
          if (e.lengthComputable) {
            const percentComplete = Math.round((e.loaded / e.total) * 100);
            dispatch(setUploadProgress(percentComplete));
          }
        });
        
        xhr.addEventListener("load", () => {
          if (xhr.status >= 200 && xhr.status < 300) {
            try {
              const data = JSON.parse(xhr.responseText);
              dispatch(setUploadProgress(100));
              resolve(data);
            } catch (e) {
              dispatch(setUploadProgress(0));
              reject(rejectWithValue("Failed to parse response"));
            }
          } else {
            dispatch(setUploadProgress(0));
            let errorData;
            try {
              errorData = JSON.parse(xhr.responseText);
            } catch (e) {
              reject(rejectWithValue(`HTTP error! status: ${xhr.status}`));
              return;
            }
            reject(rejectWithValue(errorData.detail || `HTTP error! status: ${xhr.status}`));
          }
        });
        
        xhr.addEventListener("error", () => {
          dispatch(setUploadProgress(0));
          reject(rejectWithValue("Network error occurred"));
        });
        
        xhr.addEventListener("abort", () => {
          dispatch(setUploadProgress(0));
          reject(rejectWithValue("Upload aborted"));
        });
        
        // Open request first, then set headers
        xhr.open("POST", url);
        
        // Set headers after opening
        xhr.setRequestHeader("Authorization", `Bearer ${token}`);
        
        xhr.send(formData);
      } catch (error) {
        console.error("Upload error:", error);
        dispatch(setUploadProgress(0));
        reject(rejectWithValue(error.message));
      }
    });
  }
);

// Create document (without file, metadata only)
export const createDocument = createAsyncThunk(
  "documents/createDocument",
  async (documentData, { rejectWithValue }) => {
    try {
      const response = await fetch(`${API_BASE_URL}/documents/`, {
        method: "POST",
        headers: getAuthHeaders(),
        body: JSON.stringify(documentData),
      });
      if (!response.ok) {
        const errorText = await response.text();
        let errorData;
        try {
          errorData = JSON.parse(errorText);
        } catch (e) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        throw new Error(
          errorData.detail || `HTTP error! status: ${response.status}`
        );
      }
      const data = await response.json();
      return data;
    } catch (error) {
      return rejectWithValue(error.message);
    }
  }
);

// Update document
export const updateDocument = createAsyncThunk(
  "documents/updateDocument",
  async ({ documentId, documentData }, { rejectWithValue }) => {
    try {
      const response = await fetch(
        `${API_BASE_URL}/documents/${documentId}/`,
        {
          method: "PATCH",
          headers: getAuthHeaders(),
          body: JSON.stringify(documentData),
        }
      );
      if (!response.ok) {
        const errorText = await response.text();
        let errorData;
        try {
          errorData = JSON.parse(errorText);
        } catch (e) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        throw new Error(
          errorData.detail || `HTTP error! status: ${response.status}`
        );
      }
      const data = await response.json();
      return data;
    } catch (error) {
      return rejectWithValue(error.message);
    }
  }
);

// Delete document
export const deleteDocument = createAsyncThunk(
  "documents/deleteDocument",
  async (documentId, { rejectWithValue }) => {
    try {
      const response = await fetch(
        `${API_BASE_URL}/documents/${documentId}/`,
        {
          method: "DELETE",
          headers: getAuthHeaders(),
        }
      );
      if (!response.ok) {
        throw new Error("Failed to delete document");
      }
      return documentId;
    } catch (error) {
      return rejectWithValue(error.message);
    }
  }
);

const documentSlice = createSlice({
  name: "documents",
  initialState: {
    documents: [],
    currentDocument: null,
    loading: {
      fetch: false,
      fetchById: false,
      fetchByProject: false,
      create: false,
      upload: false,
      update: false,
      delete: false,
    },
    error: null,
    uploadProgress: 0,
  },
  reducers: {
    clearCurrentDocument: (state) => {
      state.currentDocument = null;
    },
    clearDocuments: (state) => {
      state.documents = [];
    },
    setUploadProgress: (state, action) => {
      state.uploadProgress = action.payload;
    },
  },
  extraReducers: (builder) => {
    builder
      // fetchDocuments cases
      .addCase(fetchDocuments.pending, (state) => {
        state.loading.fetch = true;
        state.error = null;
      })
      .addCase(fetchDocuments.fulfilled, (state, action) => {
        state.loading.fetch = false;
        state.documents = action.payload;
      })
      .addCase(fetchDocuments.rejected, (state, action) => {
        state.loading.fetch = false;
        state.error = action.payload;
      })

      // fetchDocumentsByProject cases
      .addCase(fetchDocumentsByProject.pending, (state) => {
        state.loading.fetchByProject = true;
        state.error = null;
      })
      .addCase(fetchDocumentsByProject.fulfilled, (state, action) => {
        state.loading.fetchByProject = false;
        
        // Handle both old format (array) and new format ({ documents, projectId })
        let documents, projectId;
        if (Array.isArray(action.payload)) {
          // Old format: array of documents
          documents = action.payload;
          projectId = documents.length > 0 ? documents[0].project_id : null;
        } else {
          // New format: { documents, projectId }
          documents = action.payload.documents || [];
          projectId = action.payload.projectId;
        }
        
        if (projectId) {
          // Remove all existing documents for this project
          state.documents = state.documents.filter(
            (doc) => doc.project_id !== projectId
          );
        }
        
        // Add all documents from the server response (these are already filtered by projectId)
        state.documents = [...state.documents, ...documents];
      })
      .addCase(fetchDocumentsByProject.rejected, (state, action) => {
        state.loading.fetchByProject = false;
        state.error = action.payload;
      })

      // fetchDocumentById cases
      .addCase(fetchDocumentById.pending, (state) => {
        state.loading.fetchById = true;
        state.error = null;
      })
      .addCase(fetchDocumentById.fulfilled, (state, action) => {
        state.loading.fetchById = false;
        state.currentDocument = action.payload;
        // Update in documents array if it exists
        const index = state.documents.findIndex(
          (doc) => doc.id === action.payload.id
        );
        if (index !== -1) {
          state.documents[index] = action.payload;
        } else {
          state.documents.push(action.payload);
        }
      })
      .addCase(fetchDocumentById.rejected, (state, action) => {
        state.loading.fetchById = false;
        state.error = action.payload;
      })

      // uploadDocument cases
      .addCase(uploadDocument.pending, (state) => {
        state.loading.upload = true;
        state.uploadProgress = 0;
        state.error = null;
      })
      .addCase(uploadDocument.fulfilled, (state, action) => {
        state.loading.upload = false;
        state.uploadProgress = 100;
        // Add new document to the array
        state.documents.push(action.payload);
        state.error = null;
      })
      .addCase(uploadDocument.rejected, (state, action) => {
        state.loading.upload = false;
        state.uploadProgress = 0;
        state.error = action.payload;
      })

      // ingestBaseCaseDocument cases
      .addCase(ingestBaseCaseDocument.pending, (state) => {
        state.loading.ingestBaseCase = true;
        state.uploadProgress = 0;
        state.error = null;
      })
      .addCase(ingestBaseCaseDocument.fulfilled, (state, action) => {
        state.loading.ingestBaseCase = false;
        state.uploadProgress = 100;
        // Handle response structure: may be {document, processing} or just document
        const document = action.payload.document || action.payload;
        if (document && document.id) {
          // Check if document already exists
          const existingIndex = state.documents.findIndex(
            (doc) => doc.id === document.id
          );
          if (existingIndex !== -1) {
            state.documents[existingIndex] = document;
          } else {
            state.documents.push(document);
          }
        }
        state.error = null;
      })
      .addCase(ingestBaseCaseDocument.rejected, (state, action) => {
        state.loading.ingestBaseCase = false;
        state.uploadProgress = 0;
        state.error = action.payload;
      })

      // createDocument cases
      .addCase(createDocument.pending, (state) => {
        state.loading.create = true;
        state.error = null;
      })
      .addCase(createDocument.fulfilled, (state, action) => {
        state.loading.create = false;
        state.documents.push(action.payload);
      })
      .addCase(createDocument.rejected, (state, action) => {
        state.loading.create = false;
        state.error = action.payload;
      })

      // updateDocument cases
      .addCase(updateDocument.pending, (state) => {
        state.loading.update = true;
        state.error = null;
      })
      .addCase(updateDocument.fulfilled, (state, action) => {
        state.loading.update = false;
        const index = state.documents.findIndex(
          (doc) => doc.id === action.payload.id
        );
        if (index !== -1) {
          state.documents[index] = action.payload;
        }
        // Update currentDocument if it was the updated one
        if (state.currentDocument?.id === action.payload.id) {
          state.currentDocument = action.payload;
        }
      })
      .addCase(updateDocument.rejected, (state, action) => {
        state.loading.update = false;
        state.error = action.payload;
      })

      // deleteDocument cases
      .addCase(deleteDocument.pending, (state) => {
        state.loading.delete = true;
        state.error = null;
      })
      .addCase(deleteDocument.fulfilled, (state, action) => {
        state.loading.delete = false;
        state.documents = state.documents.filter(
          (doc) => doc.id !== action.payload
        );
        // Clear currentDocument if it was the deleted one
        if (state.currentDocument?.id === action.payload) {
          state.currentDocument = null;
        }
      })
      .addCase(deleteDocument.rejected, (state, action) => {
        state.loading.delete = false;
        state.error = action.payload;
      });
  },
});

export const { clearCurrentDocument, clearDocuments, setUploadProgress } =
  documentSlice.actions;

// Selectors
export const selectDocuments = (state) => state.documents.documents;
export const selectCurrentDocument = (state) => state.documents.currentDocument;
export const selectDocumentsLoading = (state) => state.documents.loading;
export const selectDocumentsError = (state) => state.documents.error;
export const selectUploadProgress = (state) => state.documents.uploadProgress;

// Select documents by project ID
export const selectDocumentsByProject = createSelector(
  [selectDocuments, (state, projectId) => projectId],
  (documents, projectId) => {
    if (!projectId) return [];
    return documents.filter((doc) => doc.project_id === projectId);
  }
);

// Select documents by artifact type
export const selectDocumentsByArtifactType = createSelector(
  [selectDocuments, (state, artifactType) => artifactType],
  (documents, artifactType) => {
    if (!artifactType) return documents;
    return documents.filter((doc) => doc.artifact_type === artifactType);
  }
);

// Select documents by project and artifact type
export const selectDocumentsByProjectAndType = createSelector(
  [
    selectDocuments,
    (state, projectId) => projectId,
    (state, projectId, artifactType) => artifactType,
  ],
  (documents, projectId, artifactType) => {
    if (!projectId) return [];
    let filtered = documents.filter((doc) => doc.project_id === projectId);
    if (artifactType) {
      filtered = filtered.filter((doc) => doc.artifact_type === artifactType);
    }
    return filtered;
  }
);

export default documentSlice.reducer;

