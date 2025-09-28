import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';

const API_BASE_URL = 'http://localhost:8000/api/v1';

// Helper function to get auth token
const getAuthToken = () => {
    return localStorage.getItem('access_token');
};

// Helper function to create auth headers
const getAuthHeaders = () => {
    const token = getAuthToken();
    return {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
    };
};

export const createProject = createAsyncThunk(
    'projects/createProject',
    async (projectData, { rejectWithValue }) => {
        try {
            const token = getAuthToken();
            if (!token) {
                throw new Error('No authentication token found');
            }

            const response = await fetch(`${API_BASE_URL}/projects`, {
                method: 'POST',
                headers: getAuthHeaders(),
                body: JSON.stringify(projectData),
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            return data;
        } catch (error) {
            return rejectWithValue(error.message);
        }
    }
);

export const fetchProjects = createAsyncThunk(
    'projects/fetchProjects',
    async ({ page = 1, limit = 10, status_filter, project_type, search } = {}, { rejectWithValue }) => {
        try {
            const token = getAuthToken();
            if (!token) {
                throw new Error('No authentication token found');
            }

            // Build query parameters
            const params = new URLSearchParams({ page: page.toString(), limit: limit.toString() });
            if (status_filter) params.append('status_filter', status_filter);
            if (project_type) params.append('project_type', project_type);
            if (search) params.append('search', search);

            const response = await fetch(`${API_BASE_URL}/projects?${params}`, {
                method: 'GET',
                headers: getAuthHeaders(),
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            return data;
        } catch (error) {
            return rejectWithValue(error.message);
        }
    }
);

export const fetchProject = createAsyncThunk(
    'projects/fetchProject',
    async (projectId, { rejectWithValue }) => {
        try {
            const token = getAuthToken();
            if (!token) {
                throw new Error('No authentication token found');
            }

            const response = await fetch(`${API_BASE_URL}/projects/${projectId}`, {
                method: 'GET',
                headers: getAuthHeaders(),
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            return data;
        } catch (error) {
            return rejectWithValue(error.message);
        }
    }
);

export const updateProject = createAsyncThunk(
    'projects/updateProject',
    async ({ projectId, projectData }, { rejectWithValue }) => {
        try {
            const token = getAuthToken();
            if (!token) {
                throw new Error('No authentication token found');
            }

            const response = await fetch(`${API_BASE_URL}/projects/${projectId}`, {
                method: 'PUT',
                headers: getAuthHeaders(),
                body: JSON.stringify(projectData),
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            return data;
        } catch (error) {
            return rejectWithValue(error.message);
        }
    }
);

export const deleteProject = createAsyncThunk(
    'projects/deleteProject',
    async ({ projectId, hardDelete = false }, { rejectWithValue }) => {
        try {
            const token = getAuthToken();
            if (!token) {
                throw new Error('No authentication token found');
            }

            const params = hardDelete ? '?hard_delete=true' : '';
            const response = await fetch(`${API_BASE_URL}/projects/${projectId}${params}`, {
                method: 'DELETE',
                headers: getAuthHeaders(),
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            return { ...data, projectId };
        } catch (error) {
            return rejectWithValue(error.message);
        }
    }
);

export const archiveProject = createAsyncThunk(
    'projects/archiveProject',
    async (projectId, { rejectWithValue }) => {
        try {
            const token = getAuthToken();
            if (!token) {
                throw new Error('No authentication token found');
            }

            const response = await fetch(`${API_BASE_URL}/projects/${projectId}/archive`, {
                method: 'POST',
                headers: getAuthHeaders(),
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            return { ...data, projectId };
        } catch (error) {
            return rejectWithValue(error.message);
        }
    }
);

export const getProjectStats = createAsyncThunk(
    'projects/getProjectStats',
    async (projectId, { rejectWithValue }) => {
        try {
            const token = getAuthToken();
            if (!token) {
                throw new Error('No authentication token found');
            }

            const response = await fetch(`${API_BASE_URL}/projects/${projectId}/stats`, {
                method: 'GET',
                headers: getAuthHeaders(),
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            return data;
        } catch (error) {
            return rejectWithValue(error.message);
        }
    }
);

// Initial state
const initialState = {
    projects: [],
    currentProject: null,
    projectStats: null,
    pagination: {
        total: 0,
        page: 1,
        limit: 10,
    },
    loading: {
        fetch: false,
        create: false,
        update: false,
        delete: false,
        stats: false,
    },
    error: null,
};

// Slice
const projectSlice = createSlice({
    name: 'projects',
    initialState,
    reducers: {
        clearError: (state) => {
            state.error = null;
        },
        clearCurrentProject: (state) => {
            state.currentProject = null;
        },
        clearProjectStats: (state) => {
            state.projectStats = null;
        },
    },
    extraReducers: (builder) => {
        builder
            // Create project
            .addCase(createProject.pending, (state) => {
                state.loading.create = true;
                state.error = null;
            })
            .addCase(createProject.fulfilled, (state, action) => {
                state.loading.create = false;
                state.projects.unshift(action.payload);
                state.error = null;
            })
            .addCase(createProject.rejected, (state, action) => {
                state.loading.create = false;
                state.error = action.payload;
            })

            // Fetch projects
            .addCase(fetchProjects.pending, (state) => {
                state.loading.fetch = true;
                state.error = null;
            })
            .addCase(fetchProjects.fulfilled, (state, action) => {
                state.loading.fetch = false;
                state.projects = action.payload.projects;
                state.pagination = {
                    total: action.payload.total,
                    page: action.payload.page,
                    limit: action.payload.limit,
                };
                state.error = null;
            })
            .addCase(fetchProjects.rejected, (state, action) => {
                state.loading.fetch = false;
                state.error = action.payload;
            })

            // Fetch single project
            .addCase(fetchProject.pending, (state) => {
                state.loading.fetch = true;
                state.error = null;
            })
            .addCase(fetchProject.fulfilled, (state, action) => {
                state.loading.fetch = false;
                state.currentProject = action.payload;
                state.error = null;
            })
            .addCase(fetchProject.rejected, (state, action) => {
                state.loading.fetch = false;
                state.error = action.payload;
            })

            // Update project
            .addCase(updateProject.pending, (state) => {
                state.loading.update = true;
                state.error = null;
            })
            .addCase(updateProject.fulfilled, (state, action) => {
                state.loading.update = false;
                const index = state.projects.findIndex(p => p.project_id === action.payload.project_id);
                if (index !== -1) {
                    state.projects[index] = action.payload;
                }
                if (state.currentProject?.project_id === action.payload.project_id) {
                    state.currentProject = action.payload;
                }
                state.error = null;
            })
            .addCase(updateProject.rejected, (state, action) => {
                state.loading.update = false;
                state.error = action.payload;
            })

            // Delete project
            .addCase(deleteProject.pending, (state) => {
                state.loading.delete = true;
                state.error = null;
            })
            .addCase(deleteProject.fulfilled, (state, action) => {
                state.loading.delete = false;
                state.projects = state.projects.filter(p => p.project_id !== action.payload.projectId);
                if (state.currentProject?.project_id === action.payload.projectId) {
                    state.currentProject = null;
                }
                state.error = null;
            })
            .addCase(deleteProject.rejected, (state, action) => {
                state.loading.delete = false;
                state.error = action.payload;
            })

            // Archive project
            .addCase(archiveProject.fulfilled, (state, action) => {
                const index = state.projects.findIndex(p => p.project_id === action.payload.projectId);
                if (index !== -1) {
                    state.projects[index].status = 'archived';
                }
            })

            // Get project stats
            .addCase(getProjectStats.pending, (state) => {
                state.loading.stats = true;
                state.error = null;
            })
            .addCase(getProjectStats.fulfilled, (state, action) => {
                state.loading.stats = false;
                state.projectStats = action.payload;
                state.error = null;
            })
            .addCase(getProjectStats.rejected, (state, action) => {
                state.loading.stats = false;
                state.error = action.payload;
            });
    },
});

// Export actions
export const { clearError, clearCurrentProject, clearProjectStats } = projectSlice.actions;

// Selectors
export const selectProjects = (state) => state.projects.projects;
export const selectCurrentProject = (state) => state.projects.currentProject;
export const selectProjectStats = (state) => state.projects.projectStats;
export const selectProjectsPagination = (state) => state.projects.pagination;
export const selectProjectsLoading = (state) => state.projects.loading;
export const selectProjectsError = (state) => state.projects.error;

// Export reducer
export default projectSlice.reducer;