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

// Helper function to create auth headers
const getAuthHeaders = () => {
  const token = getAuthToken();
  return {
    "Content-Type": "application/json",
    Authorization: `Bearer ${token}`,
  };
};

export const fetchProjects = createAsyncThunk(
  "projects/fetchProjects",
  async (_, { rejectWithValue }) => {
    try {
      const response = await fetch(`${API_BASE_URL}/projects/`, {
        headers: getAuthHeaders(),
      });
      if (!response.ok) {
        throw new Error("Failed to fetch projects");
      }
      const data = await response.json();
      return data;
    } catch (error) {
      return rejectWithValue(error.message);
    }
  }
);

export const fetchProjectById = createAsyncThunk(
  "projects/fetchProjectById",
  async (projectId, { rejectWithValue }) => {
    try {
      const response = await fetch(`${API_BASE_URL}/projects/${projectId}/`, {
        headers: getAuthHeaders(),
      });
      if (!response.ok) {
        throw new Error("Failed to fetch project");
      }
      const data = await response.json();
      return data;
    } catch (error) {
      return rejectWithValue(error.message);
    }
  }
);

export const createProject = createAsyncThunk(
  "projects/createProject",
  async (projectData, { rejectWithValue }) => {
    try {
      const response = await fetch(`${API_BASE_URL}/projects/`, {
        method: "POST",
        headers: getAuthHeaders(),
        body: JSON.stringify(projectData),
      });
      if (!response.ok) {
        throw new Error("Failed to create project");
      }
      const data = await response.json();
      return data;
    } catch (error) {
      return rejectWithValue(error.message);
    }
  }
);

export const deleteProject = createAsyncThunk(
  "projects/deleteProject",
  async (projectId, { rejectWithValue }) => {
    try {
      const response = await fetch(`${API_BASE_URL}/projects/${projectId}/`, {
        method: "DELETE",
        headers: getAuthHeaders(),
      });
      if (!response.ok) {
        throw new Error("Failed to delete project");
      }
      return projectId;
    } catch (error) {
      return rejectWithValue(error.message);
    }
  }
);

export const updateProject = createAsyncThunk(
  "projects/updateProject",
  async ({ projectId, projectData }, { rejectWithValue }) => {
    try {
      const response = await fetch(`${API_BASE_URL}/projects/${projectId}/`, {
        method: "PATCH",
        headers: getAuthHeaders(),
        body: JSON.stringify(projectData),
      });
      if (!response.ok) {
        throw new Error("Failed to update project");
      }
      const data = await response.json();
      return data;
    } catch (error) {
      return rejectWithValue(error.message);
    }
  }
);

const projectSlice = createSlice({
  name: "projects",
  initialState: {
    projects: [],
    currentProject: null, // Add currentProject to initial state
    loading: {
      fetch: false,
      fetchById: false, // Change loading to object structure
      create: false,
      delete: false,
    },
    error: null,
  },
  reducers: {
    clearCurrentProject: (state) => {
      state.currentProject = null;
    },
  },
  extraReducers: (builder) => {
    builder
      // fetchProjects cases
      .addCase(fetchProjects.pending, (state) => {
        state.loading.fetch = true; // Update to use object structure
        state.error = null;
      })
      .addCase(fetchProjects.fulfilled, (state, action) => {
        state.loading.fetch = false; // Update to use object structure
        state.projects = action.payload;
      })
      .addCase(fetchProjects.rejected, (state, action) => {
        state.loading.fetch = false; // Update to use object structure
        state.error = action.payload;
      })

      // fetchProjectById cases
      .addCase(fetchProjectById.pending, (state) => {
        state.loading.fetchById = true;
        state.error = null;
      })
      .addCase(fetchProjectById.fulfilled, (state, action) => {
        state.loading.fetchById = false;
        state.currentProject = action.payload;
      })
      .addCase(fetchProjectById.rejected, (state, action) => {
        state.loading.fetchById = false;
        state.error = action.payload;
      })

      // createProject cases
      .addCase(createProject.pending, (state) => {
        state.loading.create = true; // Update to use object structure
        state.error = null;
      })
      .addCase(createProject.fulfilled, (state, action) => {
        state.loading.create = false; // Update to use object structure
        state.projects.push(action.payload);
      })
      .addCase(createProject.rejected, (state, action) => {
        state.loading.create = false; // Update to use object structure
        state.error = action.payload;
      })

      // deleteProject cases
      .addCase(deleteProject.pending, (state) => {
        state.loading.delete = true; // Update to use object structure
        state.error = null;
      })
      .addCase(deleteProject.fulfilled, (state, action) => {
        state.loading.delete = false; // Update to use object structure
        state.projects = state.projects.filter(
          (project) => project.id !== action.payload
        );
        // Clear currentProject if it was the deleted one
        if (state.currentProject?.id === action.payload) {
          state.currentProject = null;
        }
      })
      .addCase(deleteProject.rejected, (state, action) => {
        state.loading.delete = false; // Update to use object structure
        state.error = action.payload;
      })

      // updateProject cases
      .addCase(updateProject.pending, (state) => {
        state.loading.update = true;
        state.error = null;
      })
      .addCase(updateProject.fulfilled, (state, action) => {
        state.loading.update = false;
        const index = state.projects.findIndex(
          (project) => project.id === action.payload.id
        );
        if (index !== -1) {
          state.projects[index] = action.payload;
        }
        // Update currentProject if it was the updated one
        if (state.currentProject?.id === action.payload.id) {
          state.currentProject = action.payload;
        }
      })
      .addCase(updateProject.rejected, (state, action) => {
        state.loading.update = false;
        state.error = action.payload;
      });
  },
});

export const { clearCurrentProject } = projectSlice.actions;

export const selectProjects = (state) => state.projects.projects;
export const selectCurrentProject = (state) => state.projects.currentProject;
export const selectLoading = (state) => state.projects.loading;
export const selectError = (state) => state.projects.error;

export default projectSlice.reducer;
