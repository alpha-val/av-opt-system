import { createSlice, createAsyncThunk, createSelector } from '@reduxjs/toolkit';

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

// Smart fetch project thunk
export const fetchProjectSmart = createAsyncThunk(
    'projects/fetchProjectSmart',
    async ({ projectId, forceRefresh = false }, { getState, dispatch, rejectWithValue }) => {
        try {
            const state = getState();

            const hasCached = selectHasCachedProject(state, projectId);
            const isStale = selectIsProjectDataStale(state, projectId);
            const cachedProject = selectCachedProject(state, projectId);

            if (hasCached && !isStale && !forceRefresh && cachedProject) {
                // console.log('Using cached project data for:', projectId);
                return cachedProject;
            }

            // console.log('Fetching fresh project data for:', projectId);
            const result = await dispatch(fetchProject(projectId)).unwrap();
            return result;

        } catch (error) {
            return rejectWithValue(error.message || 'Failed to fetch project');
        }
    }
);

// Initial state
const initialState = {
    projects: [],
    // Add a cache for individual projects by ID
    projectsCache: {}, // Structure: { "project-123": { data: {...}, lastFetched: timestamp } }
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
        clearProjectCache: (state, action) => {
            const projectId = action.payload;
            if (projectId && state.projectsCache[projectId]) {
                delete state.projectsCache[projectId];
            }
        },
        clearAllProjectCache: (state) => {
            state.projectsCache = {};
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

                // Cache the project data with timestamp
                state.projectsCache[action.payload.project_id] = {
                    data: action.payload,
                    lastFetched: Date.now()
                };

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

                // Update cache
                state.projectsCache[action.payload.project_id] = {
                    data: action.payload,
                    lastFetched: Date.now()
                };

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
            })

            // Smart fetch project (with caching)
            .addCase(fetchProjectSmart.pending, (state) => {
                state.loading.fetch = true;
                state.error = null;
            })
            .addCase(fetchProjectSmart.fulfilled, (state, action) => {
                state.loading.fetch = false;
                state.currentProject = action.payload;

                if (action.payload && action.payload.project_id) {
                    state.projectsCache[action.payload.project_id] = {
                        data: action.payload,
                        lastFetched: Date.now()
                    };
                }

                state.error = null;
            })
            .addCase(fetchProjectSmart.rejected, (state, action) => {
                state.loading.fetch = false;
                state.error = action.payload;
            });
    },
});

// Export actions
export const { clearError, clearCurrentProject, clearProjectStats, clearProjectCache, clearAllProjectCache } = projectSlice.actions;

// Selectors
export const selectProjects = (state) => state.projects.projects;
export const selectCurrentProject = (state) => state.projects.currentProject;
export const selectProjectStats = (state) => state.projects.projectStats;
export const selectProjectsPagination = (state) => state.projects.pagination;
export const selectProjectsLoading = (state) => state.projects.loading;
export const selectProjectsError = (state) => state.projects.error;
export const selectProjectsCache = (state) => state.projects.projectsCache;

// Selector to get cached project by ID
export const selectCachedProject = (state, projectId) => {
    const cache = state.projects.projectsCache[projectId];
    return cache ? cache.data : null;
};

// Selector to check if project data exists in cache
export const selectHasCachedProject = (state, projectId) => {
    return !!state.projects.projectsCache[projectId];
};

// Selector to check if cached data is stale (older than 5 minutes)
export const selectIsProjectDataStale = (state, projectId, maxAgeMs = 5 * 60 * 1000) => {
    const cache = state.projects.projectsCache[projectId];
    if (!cache) return true;

    return (Date.now() - cache.lastFetched) > maxAgeMs;
};

// Memoized selector using createSelector for better performance
export const selectProjectById = createSelector(
    [
        selectProjectsCache,
        selectCurrentProject,
        (state, projectId) => projectId
    ],
    (projectsCache, currentProject, projectId) => {
        // First check if current project matches
        if (currentProject && currentProject.project_id === projectId) {
            return currentProject;
        }

        // Then check cache
        const cached = projectsCache[projectId];
        return cached ? cached.data : null;
    }
);

// Export reducer
export default projectSlice.reducer;