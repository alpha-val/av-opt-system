import { createSlice, createAsyncThunk } from "@reduxjs/toolkit";
import axios from "axios";
import REACT_APP_CONFIG from "../AppConfig";

const API_BASE_URL = REACT_APP_CONFIG.url.API_URL;

const getAuthToken = () => {
  return localStorage.getItem("access_token");
};

const getAuthHeaders = () => {
  const token = getAuthToken();
  return {
    "Content-Type": "application/json",
    ...(token && { Authorization: `Bearer ${token}` }),
  };
};

const setAuthToken = (token, rememberMe = false) => {
  localStorage.setItem("access_token", token);
};

const clearAuthToken = () => {
  localStorage.removeItem("access_token");
};

export const fetchScenarios = createAsyncThunk(
  "scenarios/fetchByProject",
  async (projectId, { rejectWithValue }) => {
    try {
      const token = getAuthToken();
      if (!token) {
        throw new Error("No authentication token found");
      }

      console.log(
        "[scenarioSlice] fetching: ",
        `${API_BASE_URL}/projects/${projectId}/scenarios`
      );

      const response = await fetch(
        `${API_BASE_URL}/projects/${projectId}/scenarios`,
        {
          method: "GET",
          headers: getAuthHeaders(),
        }
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(
          errorData.detail || `HTTP error! status: ${response.status}`
        );
      }

      const data = await response.json();
      console.log("[scenarioSlice] Fetched scenarios:", data);
      return { projectId, scenarios: data };
    } catch (error) {
      return rejectWithValue(error.message);
    }
  }
);

export const fetchScenario = createAsyncThunk(
  "scenarios/fetchById",
  async (scenarioId, { rejectWithValue }) => {
    try {
      const token = getAuthToken();
      if (!token) {
        throw new Error("No authentication token found");
      }

      const response = await fetch(`${API_BASE_URL}/scenarios/${scenarioId}`, {
        method: "GET",
        headers: getAuthHeaders(),
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
      return rejectWithValue(error.message);
    }
  }
);

export const createScenario = createAsyncThunk(
  "scenarios/create",
  async (scenario, { rejectWithValue }) => {
    try {
      const token = getAuthToken();
      if (!token) {
        throw new Error("No authentication token found");
      }

      console.log("Creating scenario:", scenario);

      const response = await fetch(`${API_BASE_URL}/scenarios/add`, {
        method: "POST",
        headers: getAuthHeaders(),
        body: JSON.stringify(scenario),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(
          errorData.detail || `HTTP error! status: ${response.status}`
        );
      }

      const data = await response.json();
      console.log("[scenarioSlice] Created scenario:", data);
      return data;
    } catch (error) {
      return rejectWithValue(error.message);
    }
  }
);

export const updateScenario = createAsyncThunk(
  "scenarios/update",
  async ({ scenarioId, updates }, { rejectWithValue }) => {
    try {
      const token = getAuthToken();
      if (!token) {
        throw new Error("No authentication token found");
      }

      console.log("Updating scenario:", scenarioId, updates);

      const response = await fetch(`${API_BASE_URL}/scenarios/${scenarioId}`, {
        method: "PUT",
        headers: getAuthHeaders(),
        body: JSON.stringify(updates),
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
      return rejectWithValue(error.message);
    }
  }
);

export const analyzeScenario = createAsyncThunk(
  "scenarios/analyze",
  async ({ scenarioId, updates }, { rejectWithValue, dispatch }) => {
    try {
      const token = getAuthToken();
      if (!token) {
        throw new Error("No authentication token found");
      }

      console.log("[analyzeScenario] Starting analysis for:", scenarioId);

      // First, update the scenario with any field changes
      if (updates && Object.keys(updates).length > 0) {
        console.log("[analyzeScenario] Updating scenario fields:", updates);
        await dispatch(updateScenario({ scenarioId, updates })).unwrap();
      }

      // Then trigger the analysis
      console.log("[analyzeScenario] Triggering cost analysis...");
      const response = await fetch(
        `${API_BASE_URL}/scenarios/${scenarioId}/analyze`,
        {
          method: "POST",
          headers: getAuthHeaders(),
        }
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(
          errorData.detail || `HTTP error! status: ${response.status}`
        );
      }

      const data = await response.json();
      console.log("[analyzeScenario] Analysis completed:", data);

      return {
        scenario: data.scenario,
        costEstimate: data.cost_estimate,
      };
    } catch (error) {
      console.error("[analyzeScenario] Failed:", error);
      return rejectWithValue(error.message);
    }
  }
);

export const deleteScenario = createAsyncThunk(
  "scenarios/delete",
  async (scenarioId, { rejectWithValue }) => {
    try {
      const token = getAuthToken();
      if (!token) {
        throw new Error("No authentication token found");
      }

      const response = await fetch(`${API_BASE_URL}/scenarios/${scenarioId}`, {
        method: "DELETE",
        headers: getAuthHeaders(),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(
          errorData.detail || `HTTP error! status: ${response.status}`
        );
      }

      return scenarioId;
    } catch (error) {
      return rejectWithValue(error.message);
    }
  }
);

export const fetchCostEstimate = createAsyncThunk(
  "scenarios/fetchCostEstimate",
  async (scenarioId, { rejectWithValue }) => {
    try {
      const token = getAuthToken();
      if (!token) {
        throw new Error("No authentication token found");
      }

      const response = await fetch(
        `${API_BASE_URL}/scenarios/${scenarioId}/cost-estimate`,
        {
          method: "GET",
          headers: getAuthHeaders(),
        }
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(
          errorData.detail || `HTTP error! status: ${response.status}`
        );
      }

      const data = await response.json();
      return { scenarioId, costEstimate: data };
    } catch (error) {
      return rejectWithValue(error.message);
    }
  }
);

const scenarioSlice = createSlice({
  name: "scenarios",
  initialState: {
    byProject: {},
    byId: {},
    costEstimates: {},
    loading: false,
    analyzing: false,
    error: null,
  },
  reducers: {
    clearError: (state) => {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchScenarios.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchScenarios.fulfilled, (state, action) => {
        state.loading = false;
        const { projectId, scenarios } = action.payload;
        state.byProject[projectId] = scenarios;
        scenarios.forEach((s) => {
          state.byId[s.id] = s;
        });
      })
      .addCase(fetchScenarios.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload || action.error.message;
      })

      .addCase(fetchScenario.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchScenario.fulfilled, (state, action) => {
        state.loading = false;
        const scenario = action.payload;
        state.byId[scenario.id] = scenario;

        if (state.byProject[scenario.project_id]) {
          const index = state.byProject[scenario.project_id].findIndex(
            (s) => s.id === scenario.id
          );
          if (index !== -1) {
            state.byProject[scenario.project_id][index] = scenario;
          } else {
            state.byProject[scenario.project_id].push(scenario);
          }
        }
      })
      .addCase(fetchScenario.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload || action.error.message;
      })

      .addCase(createScenario.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(createScenario.fulfilled, (state, action) => {
        state.loading = false;
        const scenario = action.payload;
        state.byId[scenario.id] = scenario;
        if (!state.byProject[scenario.project_id]) {
          state.byProject[scenario.project_id] = [];
        }
        state.byProject[scenario.project_id].push(scenario);
      })
      .addCase(createScenario.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload || action.error.message;
      })

      .addCase(updateScenario.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(updateScenario.fulfilled, (state, action) => {
        state.loading = false;
        const scenario = action.payload;
        state.byId[scenario.id] = scenario;

        if (state.byProject[scenario.project_id]) {
          const index = state.byProject[scenario.project_id].findIndex(
            (s) => s.id === scenario.id
          );
          if (index !== -1) {
            state.byProject[scenario.project_id][index] = scenario;
          }
        }
      })
      .addCase(updateScenario.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload || action.error.message;
      })

      .addCase(analyzeScenario.pending, (state) => {
        state.analyzing = true;
        state.error = null;
      })
      .addCase(analyzeScenario.fulfilled, (state, action) => {
        state.analyzing = false;
        const { scenario, costEstimate } = action.payload;

        // Update scenario
        state.byId[scenario.id] = scenario;
        if (state.byProject[scenario.project_id]) {
          const index = state.byProject[scenario.project_id].findIndex(
            (s) => s.id === scenario.id
          );
          if (index !== -1) {
            state.byProject[scenario.project_id][index] = scenario;
          }
        }

        // Store cost estimate
        state.costEstimates[scenario.id] = costEstimate;
      })
      .addCase(analyzeScenario.rejected, (state, action) => {
        state.analyzing = false;
        state.error = action.payload || action.error.message;
      })

      .addCase(deleteScenario.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(deleteScenario.fulfilled, (state, action) => {
        state.loading = false;
        const scenarioId = action.payload;
        const scenario = state.byId[scenarioId];
        if (scenario) {
          state.byProject[scenario.project_id] = state.byProject[
            scenario.project_id
          ].filter((s) => s.id !== scenarioId);
          delete state.byId[scenarioId];
          delete state.costEstimates[scenarioId];
        }
      })
      .addCase(deleteScenario.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload || action.error.message;
      })

      .addCase(fetchCostEstimate.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchCostEstimate.fulfilled, (state, action) => {
        state.loading = false;
        const { scenarioId, costEstimate } = action.payload;
        state.costEstimates[scenarioId] = costEstimate;
      })
      .addCase(fetchCostEstimate.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload || action.error.message;
      });
  },
});

export const { clearError } = scenarioSlice.actions;

export default scenarioSlice.reducer;
