import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import {
  ProjectCreate,
  ProjectUpdate,
  ProjectOut,
  ProjectStatus,
  FileUploadResponse,
  ProjectReportResponse,
  ClearProjectDataResponse,
} from '../types/api';
import { projectApi, deleteAllUserData as deleteAllUserDataApi } from '../services/api';

// Async thunks for project operations
export const fetchProjects = createAsyncThunk(
  'projects/fetchProjects',
  async (_, { rejectWithValue }) => {
    try {
      const data = await projectApi.listAll();
      return data;
    } catch (error) {
      return rejectWithValue(
        error instanceof Error ? error.message : 'Failed to fetch projects'
      );
    }
  }
);

export const fetchProjectById = createAsyncThunk(
  'projects/fetchProjectById',
  async (projectId: string, { rejectWithValue }) => {
    try {
      const data = await projectApi.getById(projectId);
      return data;
    } catch (error) {
      return rejectWithValue(
        error instanceof Error ? error.message : 'Failed to fetch project'
      );
    }
  }
);

export const createProject = createAsyncThunk(
  'projects/createProject',
  async (projectData: ProjectCreate, { rejectWithValue }) => {
    try {
      // Create project (only name and description required)
      // Objective details and files will be added later in SystemBaseDesign view
      const project = await projectApi.create(projectData);
      return project;
    } catch (error) {
      return rejectWithValue(
        error instanceof Error ? error.message : 'Failed to create project'
      );
    }
  }
);

export const updateProject = createAsyncThunk(
  'projects/updateProject',
  async (
    { projectId, projectData }: { projectId: string; projectData: ProjectUpdate },
    { rejectWithValue }
  ) => {
    try {
      const data = await projectApi.update(projectId, projectData);
      return data;
    } catch (error) {
      return rejectWithValue(
        error instanceof Error ? error.message : 'Failed to update project'
      );
    }
  }
);

export const deleteProject = createAsyncThunk(
  'projects/deleteProject',
  async (projectId: string, { rejectWithValue }) => {
    try {
      await projectApi.delete(projectId);
      return projectId;
    } catch (error) {
      return rejectWithValue(
        error instanceof Error ? error.message : 'Failed to delete project'
      );
    }
  }
);

export const uploadProjectFiles = createAsyncThunk(
  'projects/uploadProjectFiles',
  async (
    {
      projectId,
      baseCaseFiles,
      tabularDataFiles,
    }: {
      projectId: string;
      baseCaseFiles: File[];
      tabularDataFiles: File[];
    },
    { rejectWithValue }
  ) => {
    try {
      const data = await projectApi.uploadProjectFiles(
        projectId,
        baseCaseFiles,
        tabularDataFiles
      );
      return { projectId, uploadData: data };
    } catch (error) {
      return rejectWithValue(
        error instanceof Error ? error.message : 'Failed to upload files'
      );
    }
  }
);

export const getProjectReport = createAsyncThunk(
  'projects/getProjectReport',
  async (projectId: string, { rejectWithValue }) => {
    try {
      const data = await projectApi.getProjectReport(projectId);
      return { projectId, report: data };
    } catch (error) {
      return rejectWithValue(
        error instanceof Error ? error.message : 'Failed to fetch report'
      );
    }
  }
);

export const updateProjectStatus = createAsyncThunk(
  'projects/updateProjectStatus',
  async (
    { projectId, status }: { projectId: string; status: ProjectStatus },
    { rejectWithValue }
  ) => {
    try {
      const data = await projectApi.updateProjectStatus(projectId, status);
      return data;
    } catch (error) {
      return rejectWithValue(
        error instanceof Error ? error.message : 'Failed to update project status'
      );
    }
  }
);

export const clearProjectData = createAsyncThunk(
  'projects/clearProjectData',
  async (projectId: string, { rejectWithValue }) => {
    try {
      const data = await projectApi.clearData(projectId);
      return { projectId, clearData: data };
    } catch (error) {
      return rejectWithValue(
        error instanceof Error ? error.message : 'Failed to clear project data'
      );
    }
  }
);

export const runAnalysis = createAsyncThunk(
  'projects/runAnalysis',
  async (projectId: string, { rejectWithValue }) => {
    try {
      const data = await projectApi.runAnalysis(projectId);
      // Fetch updated project to get new status
      const updatedProject = await projectApi.getById(projectId);
      return { projectId, analysisResult: data, project: updatedProject };
    } catch (error) {
      return rejectWithValue(
        error instanceof Error ? error.message : 'Failed to run analysis'
      );
    }
  }
);

export const deleteAllUserData = createAsyncThunk(
  'projects/deleteAllUserData',
  async (_, { rejectWithValue }) => {
    try {
      const result = await deleteAllUserDataApi();
      return result;
    } catch (error) {
      return rejectWithValue(
        error instanceof Error ? error.message : 'Failed to delete all user data'
      );
    }
  }
);

export const listProjectFiles = createAsyncThunk(
  'projects/listProjectFiles',
  async (projectId: string, { rejectWithValue }) => {
    try {
      const data = await projectApi.listProjectFiles(projectId);
      return { projectId, files: data };
    } catch (error) {
      return rejectWithValue(
        error instanceof Error ? error.message : 'Failed to list project files'
      );
    }
  }
);

export const downloadProjectFile = createAsyncThunk(
  'projects/downloadProjectFile',
  async (
    { projectId, fileId, filename }: { projectId: string; fileId: string; filename: string },
    { rejectWithValue }
  ) => {
    try {
      const blob = await projectApi.downloadProjectFile(projectId, fileId);
      // Create download link
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      return { projectId, fileId, filename };
    } catch (error) {
      return rejectWithValue(
        error instanceof Error ? error.message : 'Failed to download file'
      );
    }
  }
);

// Initial state
interface ProjectFiles {
  base_case_files: Array<{
    file_id: string;
    filename: string;
    length: number;
    upload_date: string;
    content_type: string;
    artifact_type: string;
    sha256?: string;
  }>;
  tabular_data_files: Array<{
    file_id: string;
    filename: string;
    length: number;
    upload_date: string;
    content_type: string;
    artifact_type: string;
    sha256?: string;
  }>;
}

interface ProjectsState {
  projects: ProjectOut[];
  currentProject: ProjectOut | null;
  projectReport: { [projectId: string]: ProjectReportResponse } | null;
  projectFiles: { [projectId: string]: ProjectFiles } | null;
  loading: {
    fetch: boolean;
    fetchById: boolean;
    create: boolean;
    update: boolean;
    delete: boolean;
    uploadFiles: boolean;
    getReport: boolean;
    updateStatus: boolean;
    clearData: boolean;
    runAnalysis: boolean;
    listFiles: boolean;
    downloadFile: boolean;
    deleteAllUserData: boolean;
  };
  error: string | null;
}

const initialState: ProjectsState = {
  projects: [],
  currentProject: null,
  projectReport: null,
  projectFiles: null,
  loading: {
    fetch: false,
    fetchById: false,
    create: false,
    update: false,
    delete: false,
    uploadFiles: false,
    getReport: false,
    updateStatus: false,
    clearData: false,
    runAnalysis: false,
    listFiles: false,
    downloadFile: false,
    deleteAllUserData: false,
  },
  error: null,
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
    setCurrentProject: (state, action: PayloadAction<ProjectOut>) => {
      state.currentProject = action.payload;
    },
    clearProjects: (state) => {
      state.projects = [];
    },
    clearProjectReport: (state, action: PayloadAction<string>) => {
      if (state.projectReport) {
        delete state.projectReport[action.payload];
      }
    },
    // Optimistic update for local state (useful for immediate UI updates)
    updateProjectInList: (state, action: PayloadAction<ProjectOut>) => {
      const index = state.projects.findIndex(
        (p) => p.id === action.payload.id
      );
      if (index !== -1) {
        state.projects[index] = action.payload;
      }
      if (state.currentProject?.id === action.payload.id) {
        state.currentProject = action.payload;
      }
    },
  },
  extraReducers: (builder) => {
    builder
      // Fetch all projects
      .addCase(fetchProjects.pending, (state) => {
        state.loading.fetch = true;
        state.error = null;
      })
      .addCase(fetchProjects.fulfilled, (state, action) => {
        state.loading.fetch = false;
        state.projects = action.payload;
        state.error = null;
      })
      .addCase(fetchProjects.rejected, (state, action) => {
        state.loading.fetch = false;
        state.error = action.payload as string;
      })

      // Fetch project by ID
      .addCase(fetchProjectById.pending, (state) => {
        state.loading.fetchById = true;
        state.error = null;
      })
      .addCase(fetchProjectById.fulfilled, (state, action) => {
        state.loading.fetchById = false;
        state.currentProject = action.payload;
        // Also update in projects list if it exists
        const index = state.projects.findIndex(
          (p) => p.id === action.payload.id
        );
        if (index !== -1) {
          state.projects[index] = action.payload;
        } else {
          state.projects.push(action.payload);
        }
        state.error = null;
      })
      .addCase(fetchProjectById.rejected, (state, action) => {
        state.loading.fetchById = false;
        state.error = action.payload as string;
      })

      // Create project
      .addCase(createProject.pending, (state) => {
        state.loading.create = true;
        state.error = null;
      })
      .addCase(createProject.fulfilled, (state, action) => {
        state.loading.create = false;
        state.projects.push(action.payload);
        state.currentProject = action.payload;
        state.error = null;
      })
      .addCase(createProject.rejected, (state, action) => {
        state.loading.create = false;
        state.error = action.payload as string;
      })

      // Update project
      .addCase(updateProject.pending, (state) => {
        state.loading.update = true;
        state.error = null;
      })
      .addCase(updateProject.fulfilled, (state, action) => {
        state.loading.update = false;
        const updatedProject = action.payload;
        
        // Update in projects list
        const index = state.projects.findIndex(
          (p) => p.id === updatedProject.id
        );
        if (index !== -1) {
          state.projects[index] = updatedProject;
        }
        
        // Update current project if it's the same one
        if (state.currentProject?.id === updatedProject.id) {
          state.currentProject = updatedProject;
        }
        
        state.error = null;
      })
      .addCase(updateProject.rejected, (state, action) => {
        state.loading.update = false;
        state.error = action.payload as string;
      })

      // Delete project
      .addCase(deleteProject.pending, (state) => {
        state.loading.delete = true;
        state.error = null;
      })
      .addCase(deleteProject.fulfilled, (state, action) => {
        state.loading.delete = false;
        const deletedProjectId = action.payload;
        
        // Remove from projects list
        state.projects = state.projects.filter(
          (p) => p.id !== deletedProjectId
        );
        
        // Clear current project if it was deleted
        if (state.currentProject?.id === deletedProjectId) {
          state.currentProject = null;
        }
        
        state.error = null;
      })
      .addCase(deleteProject.rejected, (state, action) => {
        state.loading.delete = false;
        state.error = action.payload as string;
      })

      // Upload project files
      .addCase(uploadProjectFiles.pending, (state) => {
        state.loading.uploadFiles = true;
        state.error = null;
      })
      .addCase(uploadProjectFiles.fulfilled, (state, action) => {
        state.loading.uploadFiles = false;
        const { projectId, uploadData } = action.payload;
        
        // Update project with new document IDs
        const project = state.projects.find((p) => p.id === projectId);
        if (project) {
          project.base_case_documents = uploadData.base_case_documents;
          project.tabular_data_documents = uploadData.tabular_data_documents;
        }
        if (state.currentProject?.id === projectId) {
          state.currentProject.base_case_documents = uploadData.base_case_documents;
          state.currentProject.tabular_data_documents = uploadData.tabular_data_documents;
        }
        
        state.error = null;
      })
      .addCase(uploadProjectFiles.rejected, (state, action) => {
        state.loading.uploadFiles = false;
        state.error = action.payload as string;
      })

      // Get project report
      .addCase(getProjectReport.pending, (state) => {
        state.loading.getReport = true;
        state.error = null;
      })
      .addCase(getProjectReport.fulfilled, (state, action) => {
        state.loading.getReport = false;
        const { projectId, report } = action.payload;
        if (!state.projectReport) {
          state.projectReport = {};
        }
        state.projectReport[projectId] = report;
        state.error = null;
      })
      .addCase(getProjectReport.rejected, (state, action) => {
        state.loading.getReport = false;
        state.error = action.payload as string;
      })

      // Update project status
      .addCase(updateProjectStatus.pending, (state) => {
        state.loading.updateStatus = true;
        state.error = null;
      })
      .addCase(updateProjectStatus.fulfilled, (state, action) => {
        state.loading.updateStatus = false;
        const updatedProject = action.payload;
        
        // Update in projects list
        const index = state.projects.findIndex(
          (p) => p.id === updatedProject.id
        );
        if (index !== -1) {
          state.projects[index] = updatedProject;
        }
        
        // Update current project if it's the same one
        if (state.currentProject?.id === updatedProject.id) {
          state.currentProject = updatedProject;
        }
        
        state.error = null;
      })
      .addCase(updateProjectStatus.rejected, (state, action) => {
        state.loading.updateStatus = false;
        state.error = action.payload as string;
      })

      // Clear project data
      .addCase(clearProjectData.pending, (state) => {
        state.loading.clearData = true;
        state.error = null;
      })
      .addCase(clearProjectData.fulfilled, (state) => {
        state.loading.clearData = false;
        state.error = null;
      })
      .addCase(clearProjectData.rejected, (state, action) => {
        state.loading.clearData = false;
        state.error = action.payload as string;
      })

      // Run analysis
      .addCase(runAnalysis.pending, (state) => {
        state.loading.runAnalysis = true;
        state.error = null;
      })
      .addCase(runAnalysis.fulfilled, (state, action) => {
        state.loading.runAnalysis = false;
        const { project } = action.payload;
        
        // Update project in list and current project
        if (project) {
          const index = state.projects.findIndex((p) => p.id === project.id);
          if (index !== -1) {
            state.projects[index] = project;
          }
          if (state.currentProject?.id === project.id) {
            state.currentProject = project;
          }
        }
        
        state.error = null;
      })
          .addCase(runAnalysis.rejected, (state, action) => {
            state.loading.runAnalysis = false;
            state.error = action.payload as string;
          })
          // List project files
          .addCase(listProjectFiles.pending, (state) => {
            state.loading.listFiles = true;
            state.error = null;
          })
          .addCase(listProjectFiles.fulfilled, (state, action) => {
            state.loading.listFiles = false;
            const { projectId, files } = action.payload;
            if (!state.projectFiles) {
              state.projectFiles = {};
            }
            state.projectFiles[projectId] = {
              base_case_files: files.base_case_files,
              tabular_data_files: files.tabular_data_files,
            };
            state.error = null;
          })
          .addCase(listProjectFiles.rejected, (state, action) => {
            state.loading.listFiles = false;
            state.error = action.payload as string;
          })
          // Download project file
          .addCase(downloadProjectFile.pending, (state) => {
            state.loading.downloadFile = true;
            state.error = null;
          })
          .addCase(downloadProjectFile.fulfilled, (state) => {
            state.loading.downloadFile = false;
            state.error = null;
          })
          .addCase(downloadProjectFile.rejected, (state, action) => {
            state.loading.downloadFile = false;
            state.error = action.payload as string;
          })

      // Delete all user data
      .addCase(deleteAllUserData.pending, (state) => {
        state.loading.deleteAllUserData = true;
        state.error = null;
      })
      .addCase(deleteAllUserData.fulfilled, (state) => {
        state.loading.deleteAllUserData = false;
        // Clear all projects, current project, reports, and files
        state.projects = [];
        state.currentProject = null;
        state.projectReport = null;
        state.projectFiles = null;
        state.error = null;
      })
      .addCase(deleteAllUserData.rejected, (state, action) => {
        state.loading.deleteAllUserData = false;
        state.error = action.payload as string;
      });
  },
});

// Export actions
export const {
  clearError,
  clearCurrentProject,
  setCurrentProject,
  clearProjects,
  clearProjectReport,
  updateProjectInList,
} = projectsSlice.actions;

// Selectors
export const selectProjects = (state: { projects: ProjectsState }) =>
  state.projects.projects;
export const selectCurrentProject = (state: { projects: ProjectsState }) =>
  state.projects.currentProject;
export const selectProjectById = (projectId: string) => (state: { projects: ProjectsState }) =>
  state.projects.projects.find((p) => p.id === projectId);
export const selectProjectReport = (projectId: string) => (state: { projects: ProjectsState }) =>
  state.projects.projectReport?.[projectId] || null;
export const selectProjectsLoading = (state: { projects: ProjectsState }) =>
  state.projects.loading;
export const selectProjectsError = (state: { projects: ProjectsState }) =>
  state.projects.error;
export const selectProjectsFetching = (state: { projects: ProjectsState }) =>
  state.projects.loading.fetch;
export const selectProjectCreating = (state: { projects: ProjectsState }) =>
  state.projects.loading.create;
export const selectProjectUpdating = (state: { projects: ProjectsState }) =>
  state.projects.loading.update;
export const selectProjectDeleting = (state: { projects: ProjectsState }) =>
  state.projects.loading.delete;
export const selectProjectUploadingFiles = (state: { projects: ProjectsState }) =>
  state.projects.loading.uploadFiles;
export const selectProjectRunningAnalysis = (state: { projects: ProjectsState }) =>
  state.projects.loading.runAnalysis;

export const selectProjectFiles = (projectId: string) => (state: { projects: ProjectsState }) =>
  state.projects.projectFiles?.[projectId] || null;

export const selectProjectFilesLoading = (state: { projects: ProjectsState }) =>
  state.projects.loading.listFiles;

// Export reducer
export default projectsSlice.reducer;

