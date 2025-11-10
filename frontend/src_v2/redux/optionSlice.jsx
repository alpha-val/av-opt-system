import { createSlice, createAsyncThunk } from "@reduxjs/toolkit";
import axios from "axios";
import REACT_APP_CONFIG from "../AppConfig";

const API_BASE_URL = REACT_APP_CONFIG.url.API_URL;

export const fetchOptions = createAsyncThunk(
  "options/fetchByScenario",
  async (scenarioId) => {
    const response = await axios.get(
      `${API_BASE_URL}/scenarios/${scenarioId}/options`
    );
    return { scenarioId, options: response.data };
  }
);

export const createOption = createAsyncThunk(
  "options/create",
  async (option) => {
    const response = await axios.post(`${API_BASE_URL}/options`, option);
    return response.data;
  }
);

export const updateOption = createAsyncThunk(
  "options/update",
  async ({ optionId, updates }) => {
    const response = await axios.patch(
      `${API_BASE_URL}/options/${optionId}`,
      updates
    );
    return response.data;
  }
);

export const deleteOption = createAsyncThunk(
  "options/delete",
  async (optionId) => {
    await axios.delete(`${API_BASE_URL}/options/${optionId}`);
    return optionId;
  }
);

export const selectOption = createAsyncThunk(
  "options/select",
  async (optionId) => {
    const response = await axios.post(
      `${API_BASE_URL}/options/${optionId}/select`
    );
    return response.data;
  }
);

const optionSlice = createSlice({
  name: "options",
  initialState: {
    byScenario: {},
    byId: {},
    loading: false,
    error: null,
  },
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(fetchOptions.pending, (state) => {
        state.loading = true;
      })
      .addCase(fetchOptions.fulfilled, (state, action) => {
        state.loading = false;
        const { scenarioId, options } = action.payload;
        state.byScenario[scenarioId] = options;
        options.forEach((opt) => {
          state.byId[opt.id] = opt;
        });
      })
      .addCase(createOption.fulfilled, (state, action) => {
        const option = action.payload;
        state.byId[option.id] = option;
        if (!state.byScenario[option.scenario_id]) {
          state.byScenario[option.scenario_id] = [];
        }
        state.byScenario[option.scenario_id].push(option);
      })
      .addCase(deleteOption.fulfilled, (state, action) => {
        const optionId = action.payload;
        const option = state.byId[optionId];
        if (option) {
          state.byScenario[option.scenario_id] = state.byScenario[
            option.scenario_id
          ].filter((o) => o.id !== optionId);
          delete state.byId[optionId];
        }
      })
      .addCase(selectOption.fulfilled, (state, action) => {
        const selectedOption = action.payload;
        const scenarioId = selectedOption.scenario_id;

        // Deselect all options in this scenario
        if (state.byScenario[scenarioId]) {
          state.byScenario[scenarioId].forEach((opt) => {
            if (state.byId[opt.id]) {
              state.byId[opt.id].selected = false;
            }
            opt.selected = false;
          });
        }

        // Select the chosen option
        state.byId[selectedOption.id] = selectedOption;
        const index = state.byScenario[scenarioId].findIndex(
          (o) => o.id === selectedOption.id
        );
        if (index !== -1) {
          state.byScenario[scenarioId][index] = selectedOption;
        }
      });
  },
});

export default optionSlice.reducer;
