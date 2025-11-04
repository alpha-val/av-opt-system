import {
  createSlice,
  createAsyncThunk,
  createSelector,
  createAction,
} from "@reduxjs/toolkit";

import REACT_APP_CONFIG from "../AppConfig";

const API_BASE_URL = REACT_APP_CONFIG.url.API_URL;

// Helper functions (keep existing ones)
const getAuthToken = () => {
  return localStorage.getItem("access_token");
};

const getAuthHeaders = (includeContentType = false) => {
  const token = getAuthToken();
  const headers = {
    Authorization: `Bearer ${token}`,
  };

  if (includeContentType) {
    headers["Content-Type"] = "application/json";
  }

  return headers;
};

const getUserId = () => {
  const userId = localStorage.getItem("user_id");
  if (userId) return userId;

  const token = getAuthToken();
  if (token) {
    try {
      const payload = JSON.parse(atob(token.split(".")[1]));
      return payload.sub || payload.user_id || payload.id;
    } catch (error) {
      console.warn("Could not decode user ID from token:", error);
    }
  }
  return null;
};

// Async thunks (simplified to work with new structure)
export const uploadProjectDescription = createAsyncThunk(
  "data/uploadProjectDescription",
  async ({ projectId, file, metadata = {} }, { rejectWithValue }) => {
    try {
      const token = getAuthToken();
      if (!token) {
        throw new Error("No authentication token found");
      }

      const userId = getUserId();
      if (!userId) {
        throw new Error("No user ID found");
      }

      if (file.type !== "application/pdf") {
        throw new Error("Only PDF files are allowed for project descriptions");
      }

      const formData = new FormData();
      formData.append("file", file);
      formData.append("user_id", userId);
      formData.append("project_id", projectId);
      formData.append("artifact_type", "base_case"); // Set document type

      if (metadata.description) {
        formData.append("description", metadata.description);
      }

      // const response = await fetch(`${API_BASE_URL}/etl_base_case`, {
      //   method: "POST",
      //   headers: {
      //     Authorization: `Bearer ${token}`,
      //   },
      //   body: formData,
      // });
      const response = await fetch(`${API_BASE_URL}/documents`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
        },
        body: formData,
      });

      if (!response.ok) {
        const errorText = await response.text();
        let errorData;
        try {
          errorData = JSON.parse(errorText);
        } catch (e) {
          throw new Error(
            `HTTP error! status: ${response.status}, message: ${errorText}`
          );
        }
        throw new Error(
          errorData.detail || `HTTP error! status: ${response.status}`
        );
      }

      const data = await response.json();

      return {
        active: true,
        artifact_type: data.artifact_type || "",
        created_at: data.created_at || "",
        doc_id: data.id,
        fileName: data.file_name || file.name,
        fileSize: data.file_size || 0,
        fileType: file.type || "pdf",
        metaData: data.metadata || {},
        originalName: file.name,
        processing_status: "completed",
        project_id: projectId,
        tags: data.tags || [],
        type: data.type || "project_description",
        updatedAt: data.updated_at || "",
        user_id: userId,
      };
    } catch (error) {
      console.error("Upload error:", error);
      return rejectWithValue(error.message);
    }
  }
);

export const uploadStructuredData = createAsyncThunk(
  "data/uploadStructuredData",
  async ({ projectId, file, metadata = {} }, { rejectWithValue }) => {
    try {
      const token = getAuthToken();
      if (!token) {
        throw new Error("No authentication token found");
      }

      const userId = getUserId();
      if (!userId) {
        throw new Error("No user ID found");
      }

      const allowedTypes = [
        "application/pdf",
        "application/vnd.ms-excel",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "text/csv",
        // ".xlsx",
        // ".xls",
        // ".csv",
      ];

      const isValidType = allowedTypes.some(
        (type) => file.type === type || file.name.toLowerCase().endsWith(type)
      );

      if (!isValidType) {
        throw new Error(
          // "Only PDF, Excel (.xlsx, .xls), and CSV files are allowed for structured data"
          "Only PDF files are allowed for structured data"
        );
      }

      const formData = new FormData();
      formData.append("file", file);
      formData.append("user_id", userId);
      formData.append("project_id", projectId);
      formData.append("artifact_type", "tabular_data"); // Set document type for structured data

      if (metadata.description) {
        formData.append("description", metadata.description);
      }

      const response = await fetch(`${API_BASE_URL}/documents`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
        },
        body: formData,
      });

      if (!response.ok) {
        const errorText = await response.text();
        let errorData;
        try {
          errorData = JSON.parse(errorText);
        } catch (e) {
          throw new Error(
            `HTTP error! status: ${response.status}, message: ${errorText}`
          );
        }
        throw new Error(
          errorData.detail || `HTTP error! status: ${response.status}`
        );
      }

      const data = await response.json();

      return {
        doc_id: data.doc_id,
        fileName: file.name,
        originalName: file.name,
        fileSize: file.size,
        fileType: file.name.toLowerCase().endsWith(".pdf")
          ? "pdf" : "pdf",
          // : file.name.toLowerCase().includes(".xls")
          // ? "xls"
          // : "csv",
        artifact_type: "scenario",
        processing_status: "completed",
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
  "data/fetchProjectDocuments",
  async (
    { projectId, artifact_type = null, page = 1, limit = 50 },
    { rejectWithValue }
  ) => {
    try {
      const token = getAuthToken();
      if (!token) {
        throw new Error("No authentication token found");
      }

      const params = new URLSearchParams();
      if (artifact_type) params.append("artifact_type", artifact_type);
      params.append("page", page.toString());
      params.append("limit", limit.toString());

      const response = await fetch(
        `${API_BASE_URL}/documents/project/${projectId}?${params}`,
        {
          method: "GET",
          headers: getAuthHeaders(true),
        }
      );

      if (!response.ok) {
        const errorData = await response.json();
        console.error("Error response:", errorData);
        throw new Error(
          errorData.detail || `HTTP error! status: ${response.status}`
        );
      }

      const data = await response.json();

      if (!data) {
        console.warn("Received null response from backend");
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
        page: data.page || page,
        limit: data.limit || limit,
        totalPages: data.total_pages || 1,
      };
    } catch (error) {
      console.error("fetchProjectDocuments error:", error);
      return rejectWithValue(error.message);
    }
  }
);

export const deleteProjectDocument = createAsyncThunk(
  "data/deleteProjectDocument",
  async (
    { projectId, docId, hard_delete = false },
    { rejectWithValue, dispatch }
  ) => {
    try {
      const token = getAuthToken();
      if (!token) {
        throw new Error("No authentication token found");
      }
      const params = new URLSearchParams();
      if (hard_delete) params.append("hard_delete", "true");
      const response = await fetch(
        `${API_BASE_URL}/projects/${projectId}/documents/${docId}?${params.toString()}`,
        {
          method: "DELETE",
          headers: getAuthHeaders(true),
        }
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(
          errorData.detail || `HTTP error! status: ${response.status}`
        );
      }

      // ✅ Automatically invalidate cache after successful deletion
      dispatch(invalidateEntitiesRelationsCache({ projectId }));

      return { projectId, docId };
    } catch (error) {
      return rejectWithValue(error.message);
    }
  }
);

// Async thunk for fetching entities and relations
export const fetchProjectEntitiesRelations = createAsyncThunk(
  "data/fetchProjectEntitiesRelations",
  async (
    {
      projectId,
      artifact_type = null,
      entity_type = null,
      relation_type = null,
      include_metadata = true,
    },
    { rejectWithValue }
  ) => {
    try {
      const token = getAuthToken();
      if (!token) {
        throw new Error("No authentication token found");
      }

      // Build query parameters
      const params = new URLSearchParams();
      if (artifact_type) params.append("artifact_type", artifact_type);
      if (entity_type) params.append("entity_type", entity_type);
      if (relation_type) params.append("relation_type", relation_type);
      params.append("include_metadata", include_metadata.toString());

      const url = `${API_BASE_URL}/projects/${projectId}/entities_relations${
        params.toString() ? "?" + params.toString() : ""
      }`;

      const response = await fetch(url, {
        method: "GET",
        headers: getAuthHeaders(true),
      });

      if (!response.ok) {
        const errorData = await response.json();
        console.error("Error response:", errorData);
        throw new Error(
          errorData.detail || `HTTP error! status: ${response.status}`
        );
      }

      const data = await response.json();

      if (!data) {
        console.warn("Received null response from backend");
        return {
          projectId,
          artifact_type,
          entities: [],
          relations: [],
          summary: {
            entity_count: 0,
            relation_count: 0,
            document_count: 0,
          },
        };
      }

      return {
        projectId,
        artifact_type,
        entities: data.entities || [],
        relations: data.relations || [],
        summary: data.summary || {
          entity_count: 0,
          relation_count: 0,
          document_count: 0,
          entity_types: {},
          relation_types: {},
          document_ids: [],
        },
      };
    } catch (error) {
      console.error("fetchProjectEntitiesRelations error:", error);
      return rejectWithValue(error.message);
    }
  }
);

// Separate thunks for entities and relations only (optional, for when you need just one)
export const fetchProjectEntities = createAsyncThunk(
  "data/fetchProjectEntities",
  async (
    {
      projectId,
      artifact_type = null,
      entity_type = null,
      limit = 100,
      offset = 0,
    },
    { rejectWithValue }
  ) => {
    try {
      const token = getAuthToken();
      if (!token) {
        throw new Error("No authentication token found");
      }

      const params = new URLSearchParams();
      if (artifact_type) params.append("artifact_type", artifact_type);
      if (entity_type) params.append("entity_type", entity_type);
      params.append("limit", limit.toString());
      params.append("offset", offset.toString());

      const url = `${API_BASE_URL}/projects/${projectId}/entities?${params.toString()}`;

      const response = await fetch(url, {
        method: "GET",
        headers: getAuthHeaders(true),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(
          errorData.detail || `HTTP error! status: ${response.status}`
        );
      }

      const data = await response.json();
      return data;
    } catch (error) {
      console.error("fetchProjectEntities error:", error);
      return rejectWithValue(error.message);
    }
  }
);

export const fetchProjectRelations = createAsyncThunk(
  "data/fetchProjectRelations",
  async (
    {
      projectId,
      artifact_type = null,
      relation_type = null,
      limit = 100,
      offset = 0,
    },
    { rejectWithValue }
  ) => {
    try {
      const token = getAuthToken();
      if (!token) {
        throw new Error("No authentication token found");
      }

      const params = new URLSearchParams();
      if (artifact_type) params.append("artifact_type", artifact_type);
      if (relation_type) params.append("relation_type", relation_type);
      params.append("limit", limit.toString());
      params.append("offset", offset.toString());

      const url = `${API_BASE_URL}/projects/${projectId}/relations?${params.toString()}`;

      const response = await fetch(url, {
        method: "GET",
        headers: getAuthHeaders(true),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(
          errorData.detail || `HTTP error! status: ${response.status}`
        );
      }

      const data = await response.json();
      return data;
    } catch (error) {
      console.error("fetchProjectRelations error:", error);
      return rejectWithValue(error.message);
    }
  }
);

export const clearAllProjectData = createAsyncThunk(
  "data/clearAllProjectData",
  async ({ projectId }, { rejectWithValue }) => {
    try {
      const token = getAuthToken();
      if (!token) {
        throw new Error("No authentication token found");
      }

      const response = await fetch(
        `${API_BASE_URL}/projects/${projectId}/data`,
        {
          method: "DELETE",
          headers: getAuthHeaders(true),
        }
      );

      if (!response.ok) {
        const errorText = await response.text();
        let errorData;
        try {
          errorData = JSON.parse(errorText);
        } catch (e) {
          throw new Error(
            `HTTP error! status: ${response.status}, message: ${errorText}`
          );
        }
        throw new Error(
          errorData.detail || `HTTP error! status: ${response.status}`
        );
      }

      // Handle 204 No Content or 200 OK with JSON
      let data = {};
      const contentType = response.headers.get("content-type");
      if (contentType && contentType.includes("application/json")) {
        data = await response.json();
      }

      return {
        projectId,
        ...data,
      };
    } catch (error) {
      console.error("Clear all project data error:", error);
      return rejectWithValue(error.message);
    }
  }
);

// Update the initial state to better structure the data
const initialState = {
  documents: [],
  entitiesRelationsData: {}, // Structure: { "project-123": { entities: [], relations: [], summary: {}, lastFetched: timestamp } }
  currentProjectId: null,
  loading: {
    uploadBase: false,
    uploadTabularData: false,
    fetchDocuments: false,
    deleteDocument: false,
    fetchEntitiesRelations: false,
    fetchEntities: false,
    fetchRelations: false,
  },
  progress: {
    upload: 0,
  },
  error: null,
};

// Create the action OUTSIDE the slice, before the slice definition
export const invalidateEntitiesRelationsCache = createAction(
  "data/invalidateEntitiesRelationsCache"
);

// Simplified slice
const dataSlice = createSlice({
  name: "data",
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
    // Add this action to dataSlice.jsx
    clearProjectEntitiesRelations: (state, action) => {
      const { projectId, artifactType } = action.payload || {};

      if (projectId && artifactType) {
        // Clear specific project and artifact type
        if (state.entitiesRelationsData[projectId]) {
          delete state.entitiesRelationsData[projectId][artifactType];
        }
      } else if (projectId) {
        // Clear all data for a project
        delete state.entitiesRelationsData[projectId];
      } else {
        // Clear all cached data
        state.entitiesRelationsData = {};
      }
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
        state.documents = state.documents.filter((doc) => doc.doc_id !== docId);
      })

      // Fetch entities and relations - UPDATED
      .addCase(fetchProjectEntitiesRelations.pending, (state) => {
        state.loading.fetchEntitiesRelations = true;
        state.error = null;
      })
      .addCase(fetchProjectEntitiesRelations.fulfilled, (state, action) => {
        state.loading.fetchEntitiesRelations = false;

        const { projectId, entities, relations, summary } = action.payload;

        // Store data directly at project level (not nested by artifact_type)
        state.entitiesRelationsData[projectId] = {
          entities: entities || [],
          relations: relations || [],
          summary: summary || {
            entity_count: 0,
            relation_count: 0,
            document_count: 0,
          },
          lastFetched: Date.now(),
        };

        state.currentProjectId = projectId;
        state.error = null;
      })
      .addCase(fetchProjectEntitiesRelations.rejected, (state, action) => {
        state.loading.fetchEntitiesRelations = false;
        state.error = action.payload;
      })

      // Optional: individual entities/relations fetching
      .addCase(fetchProjectEntities.pending, (state) => {
        state.loading.fetchEntities = true;
        state.error = null;
      })
      .addCase(fetchProjectEntities.fulfilled, (state, action) => {
        state.loading.fetchEntities = false;
        state.entities = action.payload.entities;
        state.error = null;
      })
      .addCase(fetchProjectEntities.rejected, (state, action) => {
        state.loading.fetchEntities = false;
        state.error = action.payload;
      })

      .addCase(fetchProjectRelations.pending, (state) => {
        state.loading.fetchRelations = true;
        state.error = null;
      })
      .addCase(fetchProjectRelations.fulfilled, (state, action) => {
        state.loading.fetchRelations = false;
        state.relations = action.payload.relations;
        state.error = null;
      })
      .addCase(fetchProjectRelations.rejected, (state, action) => {
        state.loading.fetchRelations = false;
        state.error = action.payload;
      })
      .addCase(invalidateEntitiesRelationsCache, (state, action) => {
        const { projectId } = action.payload || {};

        if (projectId) {
          // Clear cached data for a specific project
          delete state.entitiesRelationsData[projectId];
        } else {
          // Clear all cached data
          state.entitiesRelationsData = {};
        }
      })

      // Clear all project data - UPDATED
      .addCase(clearAllProjectData.pending, (state) => {
        state.loading.deleteDocument = true;
        state.error = null;
      })
      .addCase(clearAllProjectData.fulfilled, (state, action) => {
        state.loading.deleteDocument = false;

        const { projectId } = action.payload;

        // Clear all documents for this project
        state.documents = state.documents.filter(
          (doc) => doc.project_id !== projectId
        );

        // Clear entities/relations data for this project
        delete state.entitiesRelationsData[projectId];

        // Clear current project if it matches
        if (state.currentProjectId === projectId) {
          state.currentProjectId = null;
        }

        state.error = null;
      })
      .addCase(clearAllProjectData.rejected, (state, action) => {
        state.loading.deleteDocument = false;
        state.error = action.payload;
      });
  },
});

// Export actions
export const {
  clearError,
  setCurrentProject,
  clearDocuments,
  clearProjectEntitiesRelations,
} = dataSlice.actions;

// The invalidateEntitiesRelationsCache is already exported above, so it will be available

// Simplified selectors
export const selectAllDocuments = (state) => state.data.documents;
export const selectCurrentProjectId = (state) => state.data.currentProjectId;
export const selectDataLoading = (state) => state.data.loading;
export const selectDataProgress = (state) => state.data.progress;
export const selectDataError = (state) => state.data.error;

// Add these selectors
export const selectEntities = (state) => state.data.entities;
export const selectRelations = (state) => state.data.relations;
export const selectEntitiesRelationsSummary = (state) =>
  state.data.entitiesRelationsSummary;

// New selectors
export const selectEntitiesRelationsData = (state) =>
  state.data.entitiesRelationsData;

// Memoized selector for entities by project and artifact type
export const selectEntitiesByProjectAndType = createSelector(
  [
    selectEntitiesRelationsData,
    (state, projectId) => projectId,
    (state, projectId, artifactType) => artifactType,
  ],
  (entitiesRelationsData, projectId, artifactType) => {
    const projectData = entitiesRelationsData[projectId];
    if (!projectData) return [];

    const typeData = projectData[artifactType || "all"];
    return typeData?.entities || [];
  }
);

// Memoized selector for relations by project and artifact type
export const selectRelationsByProjectAndType = createSelector(
  [
    selectEntitiesRelationsData,
    (state, projectId) => projectId,
    (state, projectId, artifactType) => artifactType,
  ],
  (entitiesRelationsData, projectId, artifactType) => {
    const projectData = entitiesRelationsData[projectId];
    if (!projectData) return [];

    const typeData = projectData[artifactType || "all"];
    return typeData?.relations || [];
  }
);

// Memoized selector for summary by project and artifact type
export const selectSummaryByProjectAndType = createSelector(
  [
    selectEntitiesRelationsData,
    (state, projectId) => projectId,
    (state, projectId, artifactType) => artifactType,
  ],
  (entitiesRelationsData, projectId, artifactType) => {
    const projectData = entitiesRelationsData[projectId];
    if (!projectData) return null;

    const typeData = projectData[artifactType || "all"];
    return typeData?.summary || null;
  }
);

// Selector to check if data exists for a project and artifact type
export const selectHasEntitiesRelationsData = createSelector(
  [
    selectEntitiesRelationsData,
    (state, projectId) => projectId,
    (state, projectId, artifactType) => artifactType,
  ],
  (entitiesRelationsData, projectId, artifactType) => {
    const projectData = entitiesRelationsData[projectId];
    if (!projectData) return false;

    const typeData = projectData[artifactType || "all"];
    return !!typeData && typeData.lastFetched;
  }
);

// Selector to check if data is stale (older than 5 minutes)
export const selectIsDataStale = createSelector(
  [
    selectEntitiesRelationsData,
    (state, projectId) => projectId,
    (state, projectId, artifactType) => artifactType,
    (state, projectId, artifactType, maxAgeMs) => maxAgeMs || 5 * 60 * 1000, // 5 minutes default
  ],
  (entitiesRelationsData, projectId, artifactType, maxAgeMs) => {
    const projectData = entitiesRelationsData[projectId];
    if (!projectData) return true;

    const typeData = projectData[artifactType || "all"];
    if (!typeData || !typeData.lastFetched) return true;

    return Date.now() - typeData.lastFetched > maxAgeMs;
  }
);

// UPDATED SELECTORS - Remove artifact_type parameter
export const selectEntitiesByProject = createSelector(
  [selectEntitiesRelationsData, (state, projectId) => projectId],
  (entitiesRelationsData, projectId) => {
    const projectData = entitiesRelationsData[projectId];
    return projectData?.entities || [];
  }
);

export const selectRelationsByProject = createSelector(
  [selectEntitiesRelationsData, (state, projectId) => projectId],
  (entitiesRelationsData, projectId) => {
    const projectData = entitiesRelationsData[projectId];
    return projectData?.relations || [];
  }
);

export const selectSummaryByProject = createSelector(
  [selectEntitiesRelationsData, (state, projectId) => projectId],
  (entitiesRelationsData, projectId) => {
    const projectData = entitiesRelationsData[projectId];
    return projectData?.summary || null;
  }
);

export const selectHasEntitiesRelationsDataForProject = createSelector(
  [selectEntitiesRelationsData, (state, projectId) => projectId],
  (entitiesRelationsData, projectId) => {
    const projectData = entitiesRelationsData[projectId];
    return !!projectData && !!projectData.lastFetched;
  }
);

export const selectIsDataStaleForProject = createSelector(
  [
    selectEntitiesRelationsData,
    (state, projectId) => projectId,
    (state, projectId, maxAgeMs) => maxAgeMs || 5 * 60 * 1000, // 5 minutes default
  ],
  (entitiesRelationsData, projectId, maxAgeMs) => {
    const projectData = entitiesRelationsData[projectId];
    if (!projectData || !projectData.lastFetched) return true;

    return Date.now() - projectData.lastFetched > maxAgeMs;
  }
);

// Filter entities by type within a project
export const selectEntitiesByProjectAndEntityType = createSelector(
  [selectEntitiesByProject, (state, projectId, entityType) => entityType],
  (entities, entityType) => {
    if (!entityType) return entities;
    return entities.filter((entity) => entity.type === entityType);
  }
);

// Filter relations by type within a project
export const selectRelationsByProjectAndRelationType = createSelector(
  [selectRelationsByProject, (state, projectId, relationType) => relationType],
  (relations, relationType) => {
    if (!relationType) return relations;
    return relations.filter(
      (relation) =>
        relation.relation_type === relationType ||
        relation.type === relationType
    );
  }
);

// Memoized selectors that derive data
export const selectBaseCaseDocuments = createSelector(
  [selectAllDocuments],
  (documents) => documents.filter((doc) => doc.artifact_type === "base_case")
);

export const selectTabularDataDocuments = createSelector(
  [selectAllDocuments],
  (documents) => documents.filter((doc) => doc.artifact_type === "scenario")
);

export const selectDocumentsByType = createSelector(
  [selectAllDocuments, (state, documentType) => documentType],
  (documents, documentType) =>
    documents.filter((doc) => doc.artifact_type === documentType)
);

// Memoized selectors for filtering entities and relations
export const selectEntitiesByType = createSelector(
  [selectEntities, (state, entityType) => entityType],
  (entities, entityType) =>
    entities.filter((entity) => entity.type === entityType)
);

export const selectRelationsByType = createSelector(
  [selectRelations, (state, relationType) => relationType],
  (relations, relationType) =>
    relations.filter(
      (relation) =>
        relation.relation_type === relationType ||
        relation.type === relationType
    )
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
  (documents, status) =>
    documents.filter((doc) => doc.processing_status === status)
);

export const selectBaseCaseDocumentsByProjectId = createSelector(
  [selectAllDocuments, (state, projectId) => projectId],
  (documents, projectId) =>
    documents.filter((doc) => doc.project_id === projectId && doc.artifact_type === "base_case")
);

// Selector for completed documents only
export const selectCompletedDocuments = createSelector(
  [selectAllDocuments],
  (documents) =>
    documents.filter((doc) => doc.processing_status === "completed")
);

// Selectors for entity and relation types
export const selectEntityTypes = createSelector(
  [selectEntities],
  (entities) => {
    const types = {};
    entities.forEach((entity) => {
      const type = entity.type || "unknown";
      types[type] = (types[type] || 0) + 1;
    });
    return types;
  }
);

export const selectRelationTypes = createSelector(
  [selectRelations],
  (relations) => {
    const types = {};
    relations.forEach((relation) => {
      const type = relation.relation_type || relation.type || "unknown";
      types[type] = (types[type] || 0) + 1;
    });
    return types;
  }
);

export default dataSlice.reducer;
