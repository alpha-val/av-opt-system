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

// Fetch scenarios by project ID
export const fetchScenariosByProject = createAsyncThunk(
  "scenarios/fetchScenariosByProject",
  async (projectId, { rejectWithValue }) => {
    try {
      console.log("Fetching scenarios by project ID:", projectId);  
      const response = await fetch(
        `${API_BASE_URL}/scenarios/project/${projectId}/list`,
        {
          headers: getAuthHeaders(),
        }
      );
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || "Failed to fetch scenarios");
      }
      const data = await response.json();
      return { scenarios: data, projectId };
    } catch (error) {
      return rejectWithValue(error.message);
    }
  }
);

// Fetch scenario by ID
export const fetchScenarioById = createAsyncThunk(
  "scenarios/fetchScenarioById",
  async (scenarioId, { rejectWithValue }) => {
    try {
      const response = await fetch(
        `${API_BASE_URL}/scenarios/${scenarioId}`,
        {
          headers: getAuthHeaders(),
        }
      );
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || "Failed to fetch scenario");
      }
      const data = await response.json();
      return data;
    } catch (error) {
      return rejectWithValue(error.message);
    }
  }
);

// Fetch scenario with full analysis data
export const fetchScenarioWithAnalysis = createAsyncThunk(
  "scenarios/fetchScenarioWithAnalysis",
  async (scenarioId, { rejectWithValue }) => {
    try {
      const response = await fetch(
        `${API_BASE_URL}/scenarios/${scenarioId}/full`,
        {
          headers: getAuthHeaders(),
        }
      );
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || "Failed to fetch scenario");
      }
      const data = await response.json();
      return data;
    } catch (error) {
      return rejectWithValue(error.message);
    }
  }
);

// Create scenario
export const createScenario = createAsyncThunk(
  "scenarios/createScenario",
  async (scenarioData, { rejectWithValue }) => {
    try {
      const response = await fetch(`${API_BASE_URL}/scenarios/`, {
        method: "POST",
        headers: getAuthHeaders(),
        body: JSON.stringify(scenarioData),
      });
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || "Failed to create scenario");
      }
      const data = await response.json();
      return data;
    } catch (error) {
      return rejectWithValue(error.message);
    }
  }
);

// Update scenario
export const updateScenario = createAsyncThunk(
  "scenarios/updateScenario",
  async ({ scenarioId, data }, { rejectWithValue }) => {
    try {
      const response = await fetch(
        `${API_BASE_URL}/scenarios/${scenarioId}`,
        {
          method: "PATCH",
          headers: getAuthHeaders(),
          body: JSON.stringify(data),
        }
      );
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || "Failed to update scenario");
      }
      const updatedData = await response.json();
      return updatedData;
    } catch (error) {
      return rejectWithValue(error.message);
    }
  }
);

// Delete scenario
export const deleteScenario = createAsyncThunk(
  "scenarios/deleteScenario",
  async (scenarioId, { rejectWithValue }) => {
    try {
      const response = await fetch(
        `${API_BASE_URL}/scenarios/${scenarioId}`,
        {
          method: "DELETE",
          headers: getAuthHeaders(),
        }
      );
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || "Failed to delete scenario");
      }
      return scenarioId;
    } catch (error) {
      return rejectWithValue(error.message);
    }
  }
);

// Analyze scenario
export const analyzeScenario = createAsyncThunk(
  "scenarios/analyzeScenario",
  async (scenarioId, { rejectWithValue }) => {
    try {
      const response = await fetch(
        `${API_BASE_URL}/scenarios/${scenarioId}/analyze`,
        {
          method: "POST",
          headers: getAuthHeaders(),
        }
      );
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || "Failed to analyze scenario");
      }
      const data = await response.json();
      return data;
    } catch (error) {
      return rejectWithValue(error.message);
    }
  }
);

// Resize system
export const resizeSystem = createAsyncThunk(
  "scenarios/resizeSystem",
  async ({ scenarioId, userConstraints = [] }, { rejectWithValue }) => {
    try {
      const response = await fetch(
        `${API_BASE_URL}/scenarios/${scenarioId}/resize`,
        {
          method: "POST",
          headers: getAuthHeaders(),
          body: JSON.stringify(userConstraints),
        }
      );
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || "Failed to resize system");
      }
      const data = await response.json();
      return data;
    } catch (error) {
      return rejectWithValue(error.message);
    }
  }
);

// Build recommendation
export const buildRecommendation = createAsyncThunk(
  "scenarios/buildRecommendation",
  async (scenarioId, { rejectWithValue }) => {
    try {
      const response = await fetch(
        `${API_BASE_URL}/scenarios/${scenarioId}/recommend`,
        {
          method: "POST",
          headers: getAuthHeaders(),
        }
      );
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || "Failed to build recommendation");
      }
      const data = await response.json();
      return data;
    } catch (error) {
      return rejectWithValue(error.message);
    }
  }
);

// Prepare cost estimation
export const prepareCostEstimation = createAsyncThunk(
  "scenarios/prepareCostEstimation",
  async ({ scenarioId, generateEstimates = false }, { rejectWithValue }) => {
    try {
      const response = await fetch(
        `${API_BASE_URL}/scenarios/${scenarioId}/cost-estimation?generate_estimates=${generateEstimates}`,
        {
          method: "POST",
          headers: getAuthHeaders(),
        }
      );
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(
          errorData.detail || "Failed to prepare cost estimation"
        );
      }
      const data = await response.json();
      return data;
    } catch (error) {
      return rejectWithValue(error.message);
    }
  }
);

// Generate report
export const generateReport = createAsyncThunk(
  "scenarios/generateReport",
  async ({ scenarioId, format = "json" }, { rejectWithValue }) => {
    try {
      const response = await fetch(
        `${API_BASE_URL}/scenarios/${scenarioId}/report?format=${format}`,
        {
          headers: getAuthHeaders(),
        }
      );
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || "Failed to generate report");
      }
      if (format === "markdown") {
        const text = await response.text();
        return { scenarioId, format, content: text };
      }
      const data = await response.json();
      return { scenarioId, format, ...data };
    } catch (error) {
      return rejectWithValue(error.message);
    }
  }
);

// Initial state
const initialState = {
  scenarios: {}, // keyed by scenario ID
  scenariosByProject: {}, // keyed by project ID, array of scenario IDs
  loading: {
    fetch: false,
    create: false,
    update: false,
    delete: false,
    analyze: {}, // keyed by scenario ID
    resize: {}, // keyed by scenario ID
    recommend: {}, // keyed by scenario ID
    costEstimation: {}, // keyed by scenario ID
    report: {}, // keyed by scenario ID
  },
  error: null,
  currentScenario: null, // Full scenario with analysis
};

// Scenario slice
const scenarioSlice = createSlice({
  name: "scenarios",
  initialState,
  reducers: {
    clearCurrentScenario: (state) => {
      state.currentScenario = null;
    },
    clearScenarios: (state) => {
      state.scenarios = {};
      state.scenariosByProject = {};
    },
    clearError: (state) => {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      // fetchScenariosByProject cases
      .addCase(fetchScenariosByProject.pending, (state) => {
        state.loading.fetch = true;
        state.error = null;
      })
      .addCase(fetchScenariosByProject.fulfilled, (state, action) => {
        state.loading.fetch = false;
        const { scenarios, projectId } = action.payload;
        
        // Store scenarios by ID
        scenarios.forEach((scenario) => {
          state.scenarios[scenario.id] = scenario;
        });
        
        // Store scenario IDs by project
        if (projectId) {
          state.scenariosByProject[projectId] = scenarios.map((s) => s.id);
        }
      })
      .addCase(fetchScenariosByProject.rejected, (state, action) => {
        state.loading.fetch = false;
        state.error = action.payload;
      })

      // fetchScenarioById cases
      .addCase(fetchScenarioById.pending, (state) => {
        state.loading.fetch = true;
        state.error = null;
      })
      .addCase(fetchScenarioById.fulfilled, (state, action) => {
        state.loading.fetch = false;
        const scenario = action.payload;
        state.scenarios[scenario.id] = scenario;
      })
      .addCase(fetchScenarioById.rejected, (state, action) => {
        state.loading.fetch = false;
        state.error = action.payload;
      })

      // fetchScenarioWithAnalysis cases
      .addCase(fetchScenarioWithAnalysis.pending, (state) => {
        state.loading.fetch = true;
        state.error = null;
      })
      .addCase(fetchScenarioWithAnalysis.fulfilled, (state, action) => {
        state.loading.fetch = false;
        const scenario = action.payload;
        state.scenarios[scenario.id] = scenario;
        state.currentScenario = scenario;
      })
      .addCase(fetchScenarioWithAnalysis.rejected, (state, action) => {
        state.loading.fetch = false;
        state.error = action.payload;
      })

      // createScenario cases
      .addCase(createScenario.pending, (state) => {
        state.loading.create = true;
        state.error = null;
      })
      .addCase(createScenario.fulfilled, (state, action) => {
        state.loading.create = false;
        const scenario = action.payload;
        state.scenarios[scenario.id] = scenario;
        
        // Add to project's scenario list
        if (scenario.project_id) {
          if (!state.scenariosByProject[scenario.project_id]) {
            state.scenariosByProject[scenario.project_id] = [];
          }
          if (!state.scenariosByProject[scenario.project_id].includes(scenario.id)) {
            state.scenariosByProject[scenario.project_id].push(scenario.id);
          }
        }
      })
      .addCase(createScenario.rejected, (state, action) => {
        state.loading.create = false;
        state.error = action.payload;
      })

      // updateScenario cases
      .addCase(updateScenario.pending, (state) => {
        state.loading.update = true;
        state.error = null;
      })
      .addCase(updateScenario.fulfilled, (state, action) => {
        state.loading.update = false;
        const scenario = action.payload;
        state.scenarios[scenario.id] = scenario;
        
        // Update currentScenario if it's the updated one
        if (state.currentScenario?.id === scenario.id) {
          state.currentScenario = scenario;
        }
      })
      .addCase(updateScenario.rejected, (state, action) => {
        state.loading.update = false;
        state.error = action.payload;
      })

      // deleteScenario cases
      .addCase(deleteScenario.pending, (state) => {
        state.loading.delete = true;
        state.error = null;
      })
      .addCase(deleteScenario.fulfilled, (state, action) => {
        state.loading.delete = false;
        const scenarioId = action.payload;
        delete state.scenarios[scenarioId];
        
        // Remove from project's scenario list
        Object.keys(state.scenariosByProject).forEach((projectId) => {
          state.scenariosByProject[projectId] = state.scenariosByProject[
            projectId
          ].filter((id) => id !== scenarioId);
        });
        
        // Clear currentScenario if it was deleted
        if (state.currentScenario?.id === scenarioId) {
          state.currentScenario = null;
        }
      })
      .addCase(deleteScenario.rejected, (state, action) => {
        state.loading.delete = false;
        state.error = action.payload;
      })

      // analyzeScenario cases
      .addCase(analyzeScenario.pending, (state, action) => {
        const scenarioId = action.meta.arg;
        state.loading.analyze[scenarioId] = true;
        state.error = null;
      })
      .addCase(analyzeScenario.fulfilled, (state, action) => {
        const scenario = action.payload;
        const scenarioId = scenario.id;
        state.scenarios[scenarioId] = scenario;
        state.loading.analyze[scenarioId] = false;
        
        // Update currentScenario if it's the analyzed one
        if (state.currentScenario?.id === scenarioId) {
          state.currentScenario = scenario;
        }
      })
      .addCase(analyzeScenario.rejected, (state, action) => {
        const scenarioId = action.meta.arg;
        state.loading.analyze[scenarioId] = false;
        state.error = action.payload;
      })

      // resizeSystem cases
      .addCase(resizeSystem.pending, (state, action) => {
        const scenarioId = action.meta.arg.scenarioId;
        state.loading.resize[scenarioId] = true;
        state.error = null;
      })
      .addCase(resizeSystem.fulfilled, (state, action) => {
        const scenario = action.payload;
        const scenarioId = scenario.id;
        state.scenarios[scenarioId] = scenario;
        state.loading.resize[scenarioId] = false;
        
        // Update currentScenario if it's the resized one
        if (state.currentScenario?.id === scenarioId) {
          state.currentScenario = scenario;
        }
      })
      .addCase(resizeSystem.rejected, (state, action) => {
        const scenarioId = action.meta.arg.scenarioId;
        state.loading.resize[scenarioId] = false;
        state.error = action.payload;
      })

      // buildRecommendation cases
      .addCase(buildRecommendation.pending, (state, action) => {
        const scenarioId = action.meta.arg;
        state.loading.recommend[scenarioId] = true;
        state.error = null;
      })
      .addCase(buildRecommendation.fulfilled, (state, action) => {
        const scenario = action.payload;
        const scenarioId = scenario.id;
        state.scenarios[scenarioId] = scenario;
        state.loading.recommend[scenarioId] = false;
        
        // Update currentScenario if it's the recommended one
        if (state.currentScenario?.id === scenarioId) {
          state.currentScenario = scenario;
        }
      })
      .addCase(buildRecommendation.rejected, (state, action) => {
        const scenarioId = action.meta.arg;
        state.loading.recommend[scenarioId] = false;
        state.error = action.payload;
      })

      // prepareCostEstimation cases
      .addCase(prepareCostEstimation.pending, (state, action) => {
        const scenarioId = action.meta.arg.scenarioId;
        state.loading.costEstimation[scenarioId] = true;
        state.error = null;
      })
      .addCase(prepareCostEstimation.fulfilled, (state, action) => {
        const scenario = action.payload;
        const scenarioId = scenario.id;
        state.scenarios[scenarioId] = scenario;
        state.loading.costEstimation[scenarioId] = false;
        
        // Update currentScenario if it's the cost estimation one
        if (state.currentScenario?.id === scenarioId) {
          state.currentScenario = scenario;
        }
      })
      .addCase(prepareCostEstimation.rejected, (state, action) => {
        const scenarioId = action.meta.arg.scenarioId;
        state.loading.costEstimation[scenarioId] = false;
        state.error = action.payload;
      })

      // generateReport cases
      .addCase(generateReport.pending, (state, action) => {
        const scenarioId = action.meta.arg.scenarioId;
        state.loading.report[scenarioId] = true;
        state.error = null;
      })
      .addCase(generateReport.fulfilled, (state, action) => {
        const scenarioId = action.payload.scenarioId;
        state.loading.report[scenarioId] = false;
        // Report data is returned but not stored in state (display only)
      })
      .addCase(generateReport.rejected, (state, action) => {
        const scenarioId = action.meta.arg.scenarioId;
        state.loading.report[scenarioId] = false;
        state.error = action.payload;
      });
  },
});

// Export actions
export const { clearCurrentScenario, clearScenarios, clearError } =
  scenarioSlice.actions;

// Selectors
export const selectScenariosByProject = createSelector(
  [
    (state) => state.scenarios.scenarios,
    (state) => state.scenarios.scenariosByProject,
    (state, projectId) => projectId,
  ],
  (scenarios, scenariosByProject, projectId) => {
    const scenarioIds = scenariosByProject[projectId] || [];
    return scenarioIds.map((id) => scenarios[id]).filter(Boolean);
  }
);

export const selectScenarioById = createSelector(
  [(state) => state.scenarios.scenarios, (state, scenarioId) => scenarioId],
  (scenarios, scenarioId) => scenarios[scenarioId] || null
);

export const selectCurrentScenario = (state) => state.scenarios.currentScenario;

export const selectScenariosLoading = (state) => state.scenarios.loading;

export const selectScenarioError = (state) => state.scenarios.error;

export const selectAnalysisLoading = createSelector(
  [
    (state) => state.scenarios.loading.analyze,
    (state, scenarioId) => scenarioId,
  ],
  (analyzeLoading, scenarioId) => analyzeLoading[scenarioId] || false
);

export const selectResizingLoading = createSelector(
  [
    (state) => state.scenarios.loading.resize,
    (state, scenarioId) => scenarioId,
  ],
  (resizeLoading, scenarioId) => resizeLoading[scenarioId] || false
);

export const selectRecommendationLoading = createSelector(
  [
    (state) => state.scenarios.loading.recommend,
    (state, scenarioId) => scenarioId,
  ],
  (recommendLoading, scenarioId) => recommendLoading[scenarioId] || false
);

export const selectCostEstimationLoading = createSelector(
  [
    (state) => state.scenarios.loading.costEstimation,
    (state, scenarioId) => scenarioId,
  ],
  (costEstimationLoading, scenarioId) =>
    costEstimationLoading[scenarioId] || false
);

export const selectReportLoading = createSelector(
  [
    (state) => state.scenarios.loading.report,
    (state, scenarioId) => scenarioId,
  ],
  (reportLoading, scenarioId) => reportLoading[scenarioId] || false
);

export default scenarioSlice.reducer;

