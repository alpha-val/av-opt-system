import {
  createSlice,
  createAsyncThunk,
  createSelector,
} from "@reduxjs/toolkit";
import REACT_APP_CONFIG from "../AppConfig";

const API_BASE_URL = REACT_APP_CONFIG.url.API_URL;

// ============================================================================
// Helper Functions
// ============================================================================

const getAuthToken = () => {
  return localStorage.getItem("access_token") || 
         sessionStorage.getItem("access_token") ||
         localStorage.getItem("token") || 
         sessionStorage.getItem("token");
};

const getAuthHeaders = (includeContentType = false) => {
  const headers = {
    Authorization: `Bearer ${getAuthToken()}`,
  };
  if (includeContentType) {
    headers["Content-Type"] = "application/json";
  }
  return headers;
};

const getUserId = () => {
  return localStorage.getItem("userId") || sessionStorage.getItem("userId");
};

// ============================================================================
// Async Thunks
// ============================================================================

/**
 * Fetch table entities (nodes) for a project
 * Retrieves structured data extracted from tables
 */
export const fetchProjectTableEntities = createAsyncThunk(
  "tableData/fetchProjectTableEntities",
  async (
    { projectId, nodeType = null, limit = 1000, includeMetadata = true },
    { rejectWithValue }
  ) => {
    try {
      const token = getAuthToken();
      if (!token) {
        throw new Error("No authentication token found");
      }

      // Build query parameters
      const params = new URLSearchParams();
      if (nodeType) params.append("node_type", nodeType);
      params.append("limit", limit.toString());
      params.append("include_metadata", includeMetadata.toString());

      const url = `${API_BASE_URL}/projects/${projectId}/table-entities${
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
          tableEntities: [],
          summary: {
            entity_count: 0,
            table_count: 0,
            entity_types: {},
          },
        };
      }

      return {
        projectId,
        tableEntities: data.entities || [],
        summary: data.summary || {
          entity_count: 0,
          table_count: 0,
          entity_types: {},
          source_tables: [],
        },
      };
    } catch (error) {
      console.error("fetchProjectTableEntities error:", error);
      return rejectWithValue(error.message);
    }
  }
);

/**
 * Fetch table edges (relationships) for a project
 * Retrieves relationships between entities extracted from tables
 */
export const fetchProjectTableEdges = createAsyncThunk(
  "tableData/fetchProjectTableEdges",
  async (
    {
      projectId,
      edgeType = null,
      sourceId = null,
      targetId = null,
      limit = 1000,
      includeMetadata = true,
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
      if (edgeType) params.append("edge_type", edgeType);
      if (sourceId) params.append("source_id", sourceId);
      if (targetId) params.append("target_id", targetId);
      params.append("limit", limit.toString());
      params.append("include_metadata", includeMetadata.toString());

      const url = `${API_BASE_URL}/projects/${projectId}/table-edges${
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
          tableEdges: [],
          summary: {
            edge_count: 0,
            edge_types: {},
          },
        };
      }

      return {
        projectId,
        tableEdges: data.edges || [],
        summary: data.summary || {
          edge_count: 0,
          edge_types: {},
          source_tables: [],
        },
      };
    } catch (error) {
      console.error("fetchProjectTableEdges error:", error);
      return rejectWithValue(error.message);
    }
  }
);

/**
 * Fetch both table entities and edges in a single call
 * More efficient when you need both datasets
 */
export const fetchProjectTableData = createAsyncThunk(
  "tableData/fetchProjectTableData",
  async (
    {
      projectId,
      nodeType = null,
      edgeType = null,
      limit = 1000,
      includeMetadata = true,
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
      if (nodeType) params.append("node_type", nodeType);
      if (edgeType) params.append("edge_type", edgeType);
      params.append("limit", limit.toString());
      params.append("include_metadata", includeMetadata.toString());

      const url = `${API_BASE_URL}/projects/${projectId}/table-data${
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
          tableEntities: [],
          tableEdges: [],
          summary: {
            entity_count: 0,
            edge_count: 0,
            table_count: 0,
            entity_types: {},
            edge_types: {},
          },
        };
      }

      console.log(
        `Fetched ${data.entities?.length || 0} table entities and ${
          data.edges?.length || 0
        } table edges`
      );

      return {
        projectId,
        tableEntities: data.entities || [],
        tableEdges: data.edges || [],
        summary: data.summary || {
          entity_count: 0,
          edge_count: 0,
          table_count: 0,
          entity_types: {},
          edge_types: {},
          source_tables: [],
        },
      };
    } catch (error) {
      console.error("fetchProjectTableData error:", error);
      return rejectWithValue(error.message);
    }
  }
);

/**
 * Fetch tables metadata for a project
 * Retrieves information about extracted tables without full entity data
 */
export const fetchProjectTables = createAsyncThunk(
  "tableData/fetchProjectTables",
  async ({ projectId, docId = null, limit = 100 }, { rejectWithValue }) => {
    try {
      const token = getAuthToken();
      if (!token) {
        throw new Error("No authentication token found");
      }

      // Build query parameters
      const params = new URLSearchParams();
      if (docId) params.append("doc_id", docId);
      params.append("limit", limit.toString());

      const url = `${API_BASE_URL}/projects/${projectId}/tables${
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
          tables: [],
          totalTables: 0,
        };
      }

      return {
        projectId,
        tables: data.tables || [],
        totalTables: data.total_tables || 0,
      };
    } catch (error) {
      console.error("fetchProjectTables error:", error);
      return rejectWithValue(error.message);
    }
  }
);

/**
 * Fetch a single table by ID
 */
export const fetchTableById = createAsyncThunk(
  "tableData/fetchTableById",
  async ({ projectId, tableId }, { rejectWithValue }) => {
    try {
      const token = getAuthToken();
      if (!token) {
        throw new Error("No authentication token found");
      }

      const url = `${API_BASE_URL}/projects/${projectId}/tables/${tableId}`;

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
        throw new Error("Table not found");
      }

      return {
        projectId,
        table: data,
      };
    } catch (error) {
      console.error("fetchTableById error:", error);
      return rejectWithValue(error.message);
    }
  }
);

/**
 * Delete table data (entities and edges) for a project
 */
export const deleteProjectTableData = createAsyncThunk(
  "tableData/deleteProjectTableData",
  async ({ projectId }, { rejectWithValue }) => {
    try {
      const token = getAuthToken();
      if (!token) {
        throw new Error("No authentication token found");
      }

      const url = `${API_BASE_URL}/projects/${projectId}/table-data`;

      const response = await fetch(url, {
        method: "DELETE",
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

      return {
        projectId,
        deletedCounts: data,
      };
    } catch (error) {
      console.error("deleteProjectTableData error:", error);
      return rejectWithValue(error.message);
    }
  }
);

// ============================================================================
// Initial State
// ============================================================================

const initialState = {
  // Table data by project
  // Structure: { "project-123": { entities: [], edges: [], tables: [], summary: {}, lastFetched: timestamp } }
  tableData: {},

  // Currently selected table for detailed view
  selectedTable: null,

  // Loading states
  loading: {
    fetchTableEntities: false,
    fetchTableEdges: false,
    fetchTableData: false,
    fetchTables: false,
    fetchTableById: false,
    deleteTableData: false,
  },

  // Error state
  error: null,
};

// ============================================================================
// Slice
// ============================================================================

const tableDataSlice = createSlice({
  name: "tableData",
  initialState,
  reducers: {
    // Clear error
    clearError: (state) => {
      state.error = null;
    },

    // Clear table data for a specific project
    clearProjectTableData: (state, action) => {
      const projectId = action.payload;
      if (state.tableData[projectId]) {
        delete state.tableData[projectId];
      }
    },

    // Clear all table data
    clearAllTableData: (state) => {
      state.tableData = {};
      state.selectedTable = null;
    },

    // Set selected table
    setSelectedTable: (state, action) => {
      state.selectedTable = action.payload;
    },

    // Clear selected table
    clearSelectedTable: (state) => {
      state.selectedTable = null;
    },
  },
  extraReducers: (builder) => {
    builder
      // ================================================================
      // Fetch table entities
      // ================================================================
      .addCase(fetchProjectTableEntities.pending, (state) => {
        state.loading.fetchTableEntities = true;
        state.error = null;
      })
      .addCase(fetchProjectTableEntities.fulfilled, (state, action) => {
        state.loading.fetchTableEntities = false;
        const { projectId, tableEntities, summary } = action.payload;

        if (!state.tableData[projectId]) {
          state.tableData[projectId] = {
            entities: [],
            edges: [],
            tables: [],
            summary: {},
            lastFetched: null,
          };
        }

        state.tableData[projectId].entities = tableEntities;
        state.tableData[projectId].summary = {
          ...state.tableData[projectId].summary,
          ...summary,
        };
        state.tableData[projectId].lastFetched = Date.now();
        state.error = null;
      })
      .addCase(fetchProjectTableEntities.rejected, (state, action) => {
        state.loading.fetchTableEntities = false;
        state.error = action.payload;
      })

      // ================================================================
      // Fetch table edges
      // ================================================================
      .addCase(fetchProjectTableEdges.pending, (state) => {
        state.loading.fetchTableEdges = true;
        state.error = null;
      })
      .addCase(fetchProjectTableEdges.fulfilled, (state, action) => {
        state.loading.fetchTableEdges = false;
        const { projectId, tableEdges, summary } = action.payload;

        if (!state.tableData[projectId]) {
          state.tableData[projectId] = {
            entities: [],
            edges: [],
            tables: [],
            summary: {},
            lastFetched: null,
          };
        }

        state.tableData[projectId].edges = tableEdges;
        state.tableData[projectId].summary = {
          ...state.tableData[projectId].summary,
          ...summary,
        };
        state.tableData[projectId].lastFetched = Date.now();
        state.error = null;
      })
      .addCase(fetchProjectTableEdges.rejected, (state, action) => {
        state.loading.fetchTableEdges = false;
        state.error = action.payload;
      })

      // ================================================================
      // Fetch table data (combined entities + edges)
      // ================================================================
      .addCase(fetchProjectTableData.pending, (state) => {
        state.loading.fetchTableData = true;
        state.error = null;
      })
      .addCase(fetchProjectTableData.fulfilled, (state, action) => {
        state.loading.fetchTableData = false;
        const { projectId, tableEntities, tableEdges, summary } =
          action.payload;

        state.tableData[projectId] = {
          entities: tableEntities,
          edges: tableEdges,
          tables: state.tableData[projectId]?.tables || [],
          summary,
          lastFetched: Date.now(),
        };

        state.error = null;
      })
      .addCase(fetchProjectTableData.rejected, (state, action) => {
        state.loading.fetchTableData = false;
        state.error = action.payload;
      })

      // ================================================================
      // Fetch tables metadata
      // ================================================================
      .addCase(fetchProjectTables.pending, (state) => {
        state.loading.fetchTables = true;
        state.error = null;
      })
      .addCase(fetchProjectTables.fulfilled, (state, action) => {
        state.loading.fetchTables = false;
        const { projectId, tables, totalTables } = action.payload;

        if (!state.tableData[projectId]) {
          state.tableData[projectId] = {
            entities: [],
            edges: [],
            tables: [],
            summary: {},
            lastFetched: null,
          };
        }

        state.tableData[projectId].tables = tables;
        state.tableData[projectId].summary = {
          ...state.tableData[projectId].summary,
          table_count: totalTables,
        };
        state.error = null;
      })
      .addCase(fetchProjectTables.rejected, (state, action) => {
        state.loading.fetchTables = false;
        state.error = action.payload;
      })

      // ================================================================
      // Fetch table by ID
      // ================================================================
      .addCase(fetchTableById.pending, (state) => {
        state.loading.fetchTableById = true;
        state.error = null;
      })
      .addCase(fetchTableById.fulfilled, (state, action) => {
        state.loading.fetchTableById = false;
        const { table } = action.payload;
        state.selectedTable = table;
        state.error = null;
      })
      .addCase(fetchTableById.rejected, (state, action) => {
        state.loading.fetchTableById = false;
        state.error = action.payload;
      })

      // ================================================================
      // Delete project table data
      // ================================================================
      .addCase(deleteProjectTableData.pending, (state) => {
        state.loading.deleteTableData = true;
        state.error = null;
      })
      .addCase(deleteProjectTableData.fulfilled, (state, action) => {
        state.loading.deleteTableData = false;
        const { projectId } = action.payload;

        // Clear the project's table data
        if (state.tableData[projectId]) {
          delete state.tableData[projectId];
        }

        // Clear selected table if it belongs to this project
        if (state.selectedTable?.properties?.project_id === projectId) {
          state.selectedTable = null;
        }

        state.error = null;
      })
      .addCase(deleteProjectTableData.rejected, (state, action) => {
        state.loading.deleteTableData = false;
        state.error = action.payload;
      });
  },
});

// ============================================================================
// Actions
// ============================================================================

export const {
  clearError,
  clearProjectTableData,
  clearAllTableData,
  setSelectedTable,
  clearSelectedTable,
} = tableDataSlice.actions;

// ============================================================================
// Selectors
// ============================================================================

// Basic selectors
export const selectTableData = (state) => state.tableData.tableData;
export const selectSelectedTable = (state) => state.tableData.selectedTable;
export const selectTableDataLoading = (state) => state.tableData.loading;
export const selectTableDataError = (state) => state.tableData.error;

// Memoized selector for table entities by project
export const selectTableEntitiesByProject = createSelector(
  [selectTableData, (state, projectId) => projectId],
  (tableData, projectId) => {
    const projectData = tableData[projectId];
    return projectData?.entities || [];
  }
);

// Memoized selector for table edges by project
export const selectTableEdgesByProject = createSelector(
  [selectTableData, (state, projectId) => projectId],
  (tableData, projectId) => {
    const projectData = tableData[projectId];
    return projectData?.edges || [];
  }
);

// Memoized selector for tables metadata by project
export const selectTablesByProject = createSelector(
  [selectTableData, (state, projectId) => projectId],
  (tableData, projectId) => {
    const projectData = tableData[projectId];
    return projectData?.tables || [];
  }
);

// Memoized selector for table summary by project
export const selectTableSummaryByProject = createSelector(
  [selectTableData, (state, projectId) => projectId],
  (tableData, projectId) => {
    const projectData = tableData[projectId];
    return projectData?.summary || null;
  }
);

// Selector to check if table data exists for a project
export const selectHasTableData = createSelector(
  [selectTableData, (state, projectId) => projectId],
  (tableData, projectId) => {
    const projectData = tableData[projectId];
    return !!projectData && projectData.lastFetched;
  }
);

// Selector to check if table data is stale
export const selectIsTableDataStale = createSelector(
  [
    selectTableData,
    (state, projectId) => projectId,
    (state, projectId, maxAgeMs) => maxAgeMs || 5 * 60 * 1000, // 5 minutes default
  ],
  (tableData, projectId, maxAgeMs) => {
    const projectData = tableData[projectId];
    if (!projectData || !projectData.lastFetched) return true;
    return Date.now() - projectData.lastFetched > maxAgeMs;
  }
);

// Filter table entities by type
export const selectTableEntitiesByType = createSelector(
  [selectTableEntitiesByProject, (state, projectId, entityType) => entityType],
  (entities, entityType) => {
    if (!entityType) return entities;
    return entities.filter((entity) => entity.type === entityType);
  }
);

// Filter table edges by type
export const selectTableEdgesByType = createSelector(
  [selectTableEdgesByProject, (state, projectId, edgeType) => edgeType],
  (edges, edgeType) => {
    if (!edgeType) return edges;
    return edges.filter((edge) => edge.type === edgeType);
  }
);

// Get entity types distribution from table data
export const selectTableEntityTypes = createSelector(
  [selectTableEntitiesByProject],
  (entities) => {
    const types = {};
    entities.forEach((entity) => {
      const type = entity.type || "unknown";
      types[type] = (types[type] || 0) + 1;
    });
    return types;
  }
);

// Get edge types distribution from table data
export const selectTableEdgeTypes = createSelector(
  [selectTableEdgesByProject],
  (edges) => {
    const types = {};
    edges.forEach((edge) => {
      const type = edge.type || "unknown";
      types[type] = (types[type] || 0) + 1;
    });
    return types;
  }
);

// Get tables grouped by source document
export const selectTablesByDocument = createSelector(
  [selectTablesByProject],
  (tables) => {
    const grouped = {};
    tables.forEach((table) => {
      const docId = table.doc_id || "unknown";
      if (!grouped[docId]) {
        grouped[docId] = [];
      }
      grouped[docId].push(table);
    });
    return grouped;
  }
);

// Get entities by source table
export const selectEntitiesBySourceTable = createSelector(
  [selectTableEntitiesByProject, (state, projectId, tableId) => tableId],
  (entities, tableId) => {
    if (!tableId) return entities;
    return entities.filter(
      (entity) =>
        entity.properties?.source_table_id === tableId ||
        entity.properties?.table_id === tableId
    );
  }
);

// Get edges by source table
export const selectEdgesBySourceTable = createSelector(
  [selectTableEdgesByProject, (state, projectId, tableId) => tableId],
  (edges, tableId) => {
    if (!tableId) return edges;
    return edges.filter(
      (edge) =>
        edge.properties?.source_table_id === tableId ||
        edge.properties?.table_id === tableId
    );
  }
);

// Get loading state for any table operation
export const selectIsTableDataLoading = createSelector(
  [selectTableDataLoading],
  (loading) => {
    return Object.values(loading).some((isLoading) => isLoading);
  }
);

// ============================================================================
// Export
// ============================================================================

export default tableDataSlice.reducer;
