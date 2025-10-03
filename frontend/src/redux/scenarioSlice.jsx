import { createSlice, createAsyncThunk } from "@reduxjs/toolkit";
import axios from "axios";

const API_BASE_URL = "http://localhost:8000/api/v1";

export const fetchScenarios = createAsyncThunk(
  "scenarios/fetchByProject",
  async (projectId) => {
    console.log("[scenarioSlice] fetching: ", `${API_BASE_URL}/projects/${projectId}/scenarios`)
    const response = await axios.get(
      `${API_BASE_URL}/projects/${projectId}/scenarios`
    );
    console.log("[scenarioSlice] Fetched scenarios:", response.data);
    return { projectId, scenarios: response.data };
  }
);

export const fetchScenario = createAsyncThunk(
  "scenarios/fetchById",
  async (scenarioId) => {
    const response = await axios.get(`${API_BASE_URL}/scenarios/${scenarioId}`);
    return response.data;
  }
);

export const createScenario = createAsyncThunk(
  "scenarios/create",
  async (scenario) => {
    console.log("Creating scenario:", scenario);
    const response = await axios.post(`${API_BASE_URL}/scenarios`, scenario);
    return response.data;
  }
);

// ADD THIS: updateScenario thunk
export const updateScenario = createAsyncThunk(
  "scenarios/update",
  async ({ scenarioId, updates }) => {
    const response = await axios.patch(
      `${API_BASE_URL}/scenarios/${scenarioId}`,
      updates
    );
    return response.data;
  }
);

export const deleteScenario = createAsyncThunk(
  "scenarios/delete",
  async (scenarioId) => {
    await axios.delete(`${API_BASE_URL}/scenarios/${scenarioId}`);
    return scenarioId;
  }
);

const scenarioSlice = createSlice({
  name: "scenarios",
  initialState: {
    byProject: {},
    byId: {},
    loading: false,
    error: null,
  },
  reducers: {},
  extraReducers: (builder) => {
    builder
      // Fetch scenarios by project
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
        state.error = action.error.message;
      })

      // Fetch single scenario
      .addCase(fetchScenario.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchScenario.fulfilled, (state, action) => {
        state.loading = false;
        const scenario = action.payload;
        state.byId[scenario.id] = scenario;

        // Also update the project list if it exists
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
        state.error = action.error.message;
      })

      // Create scenario
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
        state.error = action.error.message;
      })

      // Update scenario
      .addCase(updateScenario.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(updateScenario.fulfilled, (state, action) => {
        state.loading = false;
        const scenario = action.payload;
        state.byId[scenario.id] = scenario;

        // Update in project list if it exists
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
        state.error = action.error.message;
      })

      // Delete scenario
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
        }
      })
      .addCase(deleteScenario.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message;
      });
  },
});

export default scenarioSlice.reducer;
