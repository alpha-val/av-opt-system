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
  async (scenarioData, { rejectWithValue }) => {
    try {
      const token = getAuthToken();
      if (!token) {
        throw new Error("No authentication token found");
      }

      const formData = new FormData();
      formData.append("project_id", scenarioData.project_id);
      formData.append("name", scenarioData.name);
      formData.append("description", scenarioData.description);
      formData.append("goal", scenarioData.goal);
      formData.append("change_type", scenarioData.change_type);
      formData.append("status", "draft");
      // if (scenarioData.file) {
      //   formData.append("file", scenarioData.file); // Attach the file
      // }

      const response = await fetch(`${API_BASE_URL}/scenarios/add`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`, // Authorization header
        },
        body: formData, // Send FormData as the request body
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(
          errorData.detail || `HTTP error! status: ${response.status}`
        );
      }

      const data = await response.json();
      console.log("[scenarioSlice] createScenario result:", data);
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
  async ({ scenarioId, updates }, { rejectWithValue, dispatch, getState }) => {
    try {
      const token = getAuthToken();
      if (!token) {
        throw new Error("No authentication token found");
      }

      // // First, update the scenario with any field changes
      // if (updates && Object.keys(updates).length > 0) {
      //   await dispatch(updateScenario({ scenarioId, updates })).unwrap();
      // }

      // Get the updated scenario from state
      const state = getState();
      const scenario = state.scenarios.byId[scenarioId];

      if (!scenario) {
        throw new Error(`Scenario ${scenarioId} not found in state`);
      }

      // Build cost estimate request payload matching CostEstimateRequest schema
      const costEstimateRequest = {
        project_id: scenario.properties.project_id,
        scenario_id: scenario.id,
        cost_id: null, // Auto-generate
        scenario_description: scenario.description,
        entity_types: ["Equipment", "Material", "Process"], // Default entity types
        uncertainties: null, // TODO: Add if needed
        goal: scenario.goal,
        change_type: scenario.change_type,
        equipment_types: null, // TODO: Extract from scenario if needed
        capacity_range: null, // TODO: Extract from scenario if needed
        selected_entities: updates.selected_entities || null,
      };
      console.log("Cost Estimate Request:", costEstimateRequest);
      // Trigger the cost estimation
      const response = await fetch(`${API_BASE_URL}/cost-estimates`, {
        method: "POST",
        headers: getAuthHeaders(),
        body: JSON.stringify(costEstimateRequest),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(
          errorData.detail || `HTTP error! status: ${response.status}`
        );
      }

      const costEstimate = await response.json();

      // Update scenario status to "ready" after successful estimation
      const updatedScenario = await dispatch(
        updateScenario({
          scenarioId,
          updates: {
            status: "ready",
            compute_state: "succeeded",
          },
        })
      ).unwrap();

      return {
        scenario: updatedScenario,
        costEstimate: costEstimate,
      };
    } catch (error) {

      // Update scenario status to "failed" on error
      try {
        await dispatch(
          updateScenario({
            scenarioId,
            updates: {
              status: "draft",
              compute_state: "failed",
            },
          })
        );
      } catch (updateError) {
        console.error(
          "[analyzeScenario] Failed to update error state:",
          updateError
        );
      }

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

      // Query cost estimates by scenario_id
      const response = await fetch(
        `${API_BASE_URL}/cost-estimates?scenario_id=${scenarioId}&limit=1`,
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

      // Extract the first estimate from the list
      const costEstimate =
        data.estimates && data.estimates.length > 0 ? data.estimates[0] : null;

      return { scenarioId, costEstimate };
    } catch (error) {
      return rejectWithValue(error.message);
    }
  }
);

export const extractScenarioData = createAsyncThunk(
  "scenarios/extractScenarioData",
  async ({ scenarioDetails, file, projectId, docId, artifactType, userId }, { rejectWithValue }) => {
    try {
      const token = getAuthToken();
      if (!token) {
        throw new Error("No authentication token found");
      }

      const formData = new FormData();
      formData.append("scenario", JSON.stringify(scenarioDetails)); // Add scenario details as JSON
      formData.append("project_id", projectId); // Add project_id
      formData.append("artifact_type", artifactType); // Add artifact_type
      formData.append("user_id", userId); // Add user_id
      if (file) {
        formData.append("file", file); // Attach the file
      }

      const response = await fetch(
        `${API_BASE_URL}/scenarios/extract-scenario-data`,
        {
          method: "POST",
          headers: {
            Authorization: `Bearer ${token}`, // Authorization header
          },
          body: formData, // Send FormData as the request body
        }
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(
          errorData.detail || `HTTP error! status: ${response.status}`
        );
      }

      const data = await response.json();
      console.log("[scenarioSlice] extractScenarioData result:", data);
      return data;
    } catch (error) {
      return rejectWithValue(error.message);
    }
  }
);

// Add extraction state to the slice
const scenarioSlice = createSlice({
  name: "scenarios",
  initialState: {
    byProject: {},
    byId: {},
    costEstimates: {},
    extraction: {
      loading: false,
      result: null,
      error: null,
    },
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

        if (state.byProject[scenario.properties.project_id]) {
          const index = state.byProject[scenario.properties.project_id].findIndex(
            (s) => s.id === scenario.id
          );
          if (index !== -1) {
            state.byProject[scenario.properties.project_id][index] = scenario;
          } else {
            state.byProject[scenario.properties.project_id].push(scenario);
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
        console.log("[scenarioSlice] Adding scenario: ", scenario)
        if (!state.byProject[scenario.properties.project_id]) {
          state.byProject[scenario.properties.project_id] = [];
        }
        state.byProject[scenario.properties.project_id].push(scenario);
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

        if (state.byProject[scenario.properties.project_id]) {
          const index = state.byProject[scenario.properties.project_id].findIndex(
            (s) => s.id === scenario.id
          );
          if (index !== -1) {
            state.byProject[scenario.properties.project_id][index] = scenario;
          }
        }
      })
      .addCase(updateScenario.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload || action.error.message;
      })

      .addCase(analyzeScenario.pending, (state, action) => {
        state.analyzing = true;
        state.error = null;

        // Update scenario state to analyzing
        const scenarioId = action.meta.arg.scenarioId;
        if (state.byId[scenarioId]) {
          state.byId[scenarioId].status = "analyzing";
          state.byId[scenarioId].compute_state = "running";
        }
      })
      .addCase(analyzeScenario.fulfilled, (state, action) => {
        state.analyzing = false;
        const { scenario, costEstimate } = action.payload;

        // Update scenario
        state.byId[scenario.id] = scenario;
        if (state.byProject[scenario.properties.project_id]) {
          const index = state.byProject[scenario.properties.project_id].findIndex(
            (s) => s.id === scenario.id
          );
          if (index !== -1) {
            state.byProject[scenario.properties.project_id][index] = scenario;
          }
        }

        // Store cost estimate
        state.costEstimates[scenario.id] = costEstimate;
      })
      .addCase(analyzeScenario.rejected, (state, action) => {
        state.analyzing = false;
        state.error = action.payload || action.error.message;

        // Update scenario state to failed
        const scenarioId = action.meta.arg.scenarioId;
        if (state.byId[scenarioId]) {
          state.byId[scenarioId].status = "draft";
          state.byId[scenarioId].compute_state = "failed";
        }
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
          state.byProject[scenario.properties.project_id] = state.byProject[
            scenario.properties.project_id
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
        if (costEstimate) {
          state.costEstimates[scenarioId] = costEstimate;
        }
      })
      .addCase(fetchCostEstimate.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload || action.error.message;
      })
      .addCase(extractScenarioData.pending, (state) => {
        state.extraction.loading = true;
        state.extraction.result = null;
        state.extraction.error = null;
      })
      .addCase(extractScenarioData.fulfilled, (state, action) => {
        state.extraction.loading = false;
        state.extraction.result = action.payload;
      })
      .addCase(extractScenarioData.rejected, (state, action) => {
        state.extraction.loading = false;
        state.extraction.error = action.payload || action.error.message;
      });
  },
});

export const { clearError } = scenarioSlice.actions;

export default scenarioSlice.reducer;
