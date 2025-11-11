import { createSlice, createAsyncThunk, PayloadAction, createSelector } from '@reduxjs/toolkit';
import {
  ScenarioCreate,
  ScenarioUpdate,
  ScenarioOut,
} from '../types/api';
import { scenarioApi } from '../services/api';

// Async thunks for scenario operations
export const fetchScenarios = createAsyncThunk(
  'scenarios/fetchScenarios',
  async (projectId?: string, { rejectWithValue }) => {
    try {
      const data = await scenarioApi.listAll(projectId);
      return { scenarios: data, projectId };
    } catch (error) {
      return rejectWithValue(
        error instanceof Error ? error.message : 'Failed to fetch scenarios'
      );
    }
  }
);

export const fetchScenarioById = createAsyncThunk(
  'scenarios/fetchScenarioById',
  async (scenarioId: string, { rejectWithValue }) => {
    try {
      const data = await scenarioApi.getById(scenarioId);
      return data;
    } catch (error) {
      return rejectWithValue(
        error instanceof Error ? error.message : 'Failed to fetch scenario'
      );
    }
  }
);

export const createScenario = createAsyncThunk(
  'scenarios/createScenario',
  async (scenarioData: ScenarioCreate, { rejectWithValue }) => {
    try {
      const scenario = await scenarioApi.create(scenarioData);
      return scenario;
    } catch (error) {
      return rejectWithValue(
        error instanceof Error ? error.message : 'Failed to create scenario'
      );
    }
  }
);

export const updateScenario = createAsyncThunk(
  'scenarios/updateScenario',
  async (
    { scenarioId, data }: { scenarioId: string; data: ScenarioUpdate },
    { rejectWithValue }
  ) => {
    try {
      const scenario = await scenarioApi.update(scenarioId, data);
      return scenario;
    } catch (error) {
      return rejectWithValue(
        error instanceof Error ? error.message : 'Failed to update scenario'
      );
    }
  }
);

export const deleteScenario = createAsyncThunk(
  'scenarios/deleteScenario',
  async (scenarioId: string, { rejectWithValue }) => {
    try {
      await scenarioApi.delete(scenarioId);
      return scenarioId;
    } catch (error) {
      return rejectWithValue(
        error instanceof Error ? error.message : 'Failed to delete scenario'
      );
    }
  }
);

// Initial state
interface ScenariosState {
  scenarios: ScenarioOut[];
  currentScenario: ScenarioOut | null;
  loading: {
    fetch: boolean;
    fetchById: boolean;
    create: boolean;
    update: boolean;
    delete: boolean;
  };
  error: string | null;
}

const initialState: ScenariosState = {
  scenarios: [],
  currentScenario: null,
  loading: {
    fetch: false,
    fetchById: false,
    create: false,
    update: false,
    delete: false,
  },
  error: null,
};

// Slice
const scenariosSlice = createSlice({
  name: 'scenarios',
  initialState,
  reducers: {
    clearError: (state) => {
      state.error = null;
    },
    clearCurrentScenario: (state) => {
      state.currentScenario = null;
    },
    setCurrentScenario: (state, action: PayloadAction<ScenarioOut>) => {
      state.currentScenario = action.payload;
    },
    clearScenarios: (state) => {
      state.scenarios = [];
    },
  },
  extraReducers: (builder) => {
    builder
      // Fetch scenarios
      .addCase(fetchScenarios.pending, (state) => {
        state.loading.fetch = true;
        state.error = null;
      })
      .addCase(fetchScenarios.fulfilled, (state, action) => {
        state.loading.fetch = false;
        state.scenarios = action.payload.scenarios;
        state.error = null;
      })
      .addCase(fetchScenarios.rejected, (state, action) => {
        state.loading.fetch = false;
        state.error = action.payload as string;
      })

      // Fetch scenario by ID
      .addCase(fetchScenarioById.pending, (state) => {
        state.loading.fetchById = true;
        state.error = null;
      })
      .addCase(fetchScenarioById.fulfilled, (state, action) => {
        state.loading.fetchById = false;
        state.currentScenario = action.payload;
        // Also update in scenarios list if it exists
        const index = state.scenarios.findIndex(
          (s) => s.id === action.payload.id
        );
        if (index !== -1) {
          state.scenarios[index] = action.payload;
        } else {
          state.scenarios.push(action.payload);
        }
        state.error = null;
      })
      .addCase(fetchScenarioById.rejected, (state, action) => {
        state.loading.fetchById = false;
        state.error = action.payload as string;
      })

      // Create scenario
      .addCase(createScenario.pending, (state) => {
        state.loading.create = true;
        state.error = null;
      })
      .addCase(createScenario.fulfilled, (state, action) => {
        state.loading.create = false;
        state.scenarios.push(action.payload);
        state.currentScenario = action.payload;
        state.error = null;
      })
      .addCase(createScenario.rejected, (state, action) => {
        state.loading.create = false;
        state.error = action.payload as string;
      })

      // Update scenario
      .addCase(updateScenario.pending, (state) => {
        state.loading.update = true;
        state.error = null;
      })
      .addCase(updateScenario.fulfilled, (state, action) => {
        state.loading.update = false;
        const updatedScenario = action.payload;
        
        // Update in scenarios list
        const index = state.scenarios.findIndex(
          (s) => s.id === updatedScenario.id
        );
        if (index !== -1) {
          state.scenarios[index] = updatedScenario;
        }
        
        // Update current scenario if it's the same one
        if (state.currentScenario?.id === updatedScenario.id) {
          state.currentScenario = updatedScenario;
        }
        
        state.error = null;
      })
      .addCase(updateScenario.rejected, (state, action) => {
        state.loading.update = false;
        state.error = action.payload as string;
      })

      // Delete scenario
      .addCase(deleteScenario.pending, (state) => {
        state.loading.delete = true;
        state.error = null;
      })
      .addCase(deleteScenario.fulfilled, (state, action) => {
        state.loading.delete = false;
        const deletedScenarioId = action.payload;
        
        // Remove from scenarios list
        state.scenarios = state.scenarios.filter(
          (s) => s.id !== deletedScenarioId
        );
        
        // Clear current scenario if it was deleted
        if (state.currentScenario?.id === deletedScenarioId) {
          state.currentScenario = null;
        }
        
        state.error = null;
      })
      .addCase(deleteScenario.rejected, (state, action) => {
        state.loading.delete = false;
        state.error = action.payload as string;
      });
  },
});

// Export actions
export const {
  clearError,
  clearCurrentScenario,
  setCurrentScenario,
  clearScenarios,
} = scenariosSlice.actions;

// Base selectors
export const selectScenarios = (state: { scenarios: ScenariosState }) =>
  state.scenarios.scenarios;
export const selectCurrentScenario = (state: { scenarios: ScenariosState }) =>
  state.scenarios.currentScenario;
export const selectScenariosLoading = (state: { scenarios: ScenariosState }) =>
  state.scenarios.loading.fetch;
export const selectScenariosError = (state: { scenarios: ScenariosState }) =>
  state.scenarios.error;
export const selectScenarioCreating = (state: { scenarios: ScenariosState }) =>
  state.scenarios.loading.create;
export const selectScenarioDeleting = (state: { scenarios: ScenariosState }) =>
  state.scenarios.loading.delete;

// Memoized selector for scenarios by project
export const selectScenariosByProject = (projectId: string) =>
  createSelector(
    [selectScenarios],
    (scenarios) => scenarios.filter((s) => s.project_id === projectId)
  );

// Export reducer
export default scenariosSlice.reducer;

