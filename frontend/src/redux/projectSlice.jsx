import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';

// API base URL - adjust as needed
const API_BASE_URL = 'http://localhost:8000/api/v1';

// Async thunks for CRUD operations
export const fetchProjects = createAsyncThunk(
    'projects/fetchProjects',
    async (_, { rejectWithValue }) => {
        try {
            const response = await fetch(`${API_BASE_URL}/projects`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            return data;
        } catch (error) {
            return rejectWithValue(error.message);
        }
    }
);

export const fetchProjectById = createAsyncThunk(
    'projects/fetchProjectById',
    async (projectId, { rejectWithValue }) => {
        try {
            const response = await fetch(`${API_BASE_URL}/projects/${projectId}`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            return data;
        } catch (error) {
            return rejectWithValue(error.message);
        }
    }
);

export const createProject = createAsyncThunk(
    'projects/createProject',
    async (projectData, { rejectWithValue }) => {
        try {
            const response = await fetch(`${API_BASE_URL}/projects`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(projectData),
            });
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
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
            const response = await fetch(`${API_BASE_URL}/projects/${projectId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(projectData),
            });
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
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
    async (projectId, { rejectWithValue }) => {
        try {
            const response = await fetch(`${API_BASE_URL}/projects/${projectId}`, {
                method: 'DELETE',
            });
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return projectId; // Return the deleted project ID
        } catch (error) {
            return rejectWithValue(error.message);
        }
    }
);

// Initial state
const initialState = {
    projects: [],
    currentProject: null,
    loading: false,
    error: null,
    // Loading states for individual operations
    creating: false,
    updating: false,
    deleting: false,
    fetchingById: false,
};

// Slice
const projectsSlice = createSlice({
    name: 'projects',
    initialState,
    reducers: {
        clearError: (state) => {
            state.error = null;
        },
        clearCurrentProject: (state) => {
            state.currentProject = null;
        },
        setCurrentProject: (state, action) => {
            state.currentProject = action.payload;
        },
    },
    extraReducers: (builder) => {
        builder
            // Fetch all projects
            .addCase(fetchProjects.pending, (state) => {
                state.loading = true;
                state.error = null;
            })
            .addCase(fetchProjects.fulfilled, (state, action) => {
                state.loading = false;
                state.projects = action.payload;
                state.error = null;
            })
            .addCase(fetchProjects.rejected, (state, action) => {
                state.loading = false;
                state.error = action.payload;
            })

            // Fetch project by ID
            .addCase(fetchProjectById.pending, (state) => {
                state.fetchingById = true;
                state.error = null;
            })
            .addCase(fetchProjectById.fulfilled, (state, action) => {
                state.fetchingById = false;
                state.currentProject = action.payload;
                state.error = null;
            })
            .addCase(fetchProjectById.rejected, (state, action) => {
                state.fetchingById = false;
                state.error = action.payload;
            })

            // Create project
            .addCase(createProject.pending, (state) => {
                state.creating = true;
                state.error = null;
            })
            .addCase(createProject.fulfilled, (state, action) => {
                state.creating = false;
                state.projects.push(action.payload);
                state.error = null;
            })
            .addCase(createProject.rejected, (state, action) => {
                state.creating = false;
                state.error = action.payload;
            })

            // Update project
            .addCase(updateProject.pending, (state) => {
                state.updating = true;
                state.error = null;
            })
            .addCase(updateProject.fulfilled, (state, action) => {
                state.updating = false;
                const index = state.projects.findIndex(
                    (project) => project.id === action.payload.id
                );
                if (index !== -1) {
                    state.projects[index] = action.payload;
                }
                // Update current project if it's the same one
                if (state.currentProject && state.currentProject.id === action.payload.id) {
                    state.currentProject = action.payload;
                }
                state.error = null;
            })
            .addCase(updateProject.rejected, (state, action) => {
                state.updating = false;
                state.error = action.payload;
            })

            // Delete project
            .addCase(deleteProject.pending, (state) => {
                state.deleting = true;
                state.error = null;
            })
            .addCase(deleteProject.fulfilled, (state, action) => {
                state.deleting = false;
                state.projects = state.projects.filter(
                    (project) => project.id !== action.payload
                );
                // Clear current project if it was deleted
                if (state.currentProject && state.currentProject.id === action.payload) {
                    state.currentProject = null;
                }
                state.error = null;
            })
            .addCase(deleteProject.rejected, (state, action) => {
                state.deleting = false;
                state.error = action.payload;
            });
    },
});

// Export actions
export const { clearError, clearCurrentProject, setCurrentProject } = projectsSlice.actions;

// Selectors
export const selectProjects = (state) => state.projects.projects;
export const selectCurrentProject = (state) => state.projects.currentProject;
export const selectProjectsLoading = (state) => state.projects.loading;
export const selectProjectsError = (state) => state.projects.error;
export const selectProjectCreating = (state) => state.projects.creating;
export const selectProjectUpdating = (state) => state.projects.updating;
export const selectProjectDeleting = (state) => state.projects.deleting;
export const selectProjectFetchingById = (state) => state.projects.fetchingById;

// Export reducer
export default projectsSlice.reducer;