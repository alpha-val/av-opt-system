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

export const runAnalysis = createAsyncThunk(
  'scenarios/runAnalysis',
  async (scenarioId: string, { rejectWithValue }) => {
    try {
      const data = await scenarioApi.runAnalysis(scenarioId);
      // Fetch updated scenario to get new status
      const updatedScenario = await scenarioApi.getById(scenarioId);
      return { scenarioId, analysisResult: data, scenario: updatedScenario };
    } catch (error) {
      return rejectWithValue(
        error instanceof Error ? error.message : 'Failed to run analysis'
      );
    }
  }
);

export const runAnalysisV2 = createAsyncThunk(
  'scenarios/runAnalysisV2',
  async (
    {
      scenarioId,
      extract_summary,
      extraction_scope,
    }: {
      scenarioId: string;
      extract_summary?: boolean;
      extraction_scope?: "exact" | "with_relationships" | "with_context";
    },
    { rejectWithValue }
  ) => {
    try {
      const data = await scenarioApi.runAnalysisV2(scenarioId, {
        extract_summary,
        extraction_scope,
      });
      // Fetch updated scenario to get new status
      const updatedScenario = await scenarioApi.getById(scenarioId);
      return { scenarioId, analysisResult: data, scenario: updatedScenario };
    } catch (error) {
      return rejectWithValue(
        error instanceof Error ? error.message : 'Failed to run analysis (V2)'
      );
    }
  }
);

export const runAnalysisV4 = createAsyncThunk(
  'scenarios/runAnalysisV4',
  async (scenarioId: string, { rejectWithValue }) => {
    try {
      console.log('[Redux Thunk] runAnalysisV4 - Calling API for scenarioId:', scenarioId);
      const data = await scenarioApi.runAnalysisV5(scenarioId);
      console.log('[Redux Thunk] runAnalysisV4 - API response data:', data);
      console.log('[Redux Thunk] runAnalysisV4 - data.job_id:', data?.job_id);
      // Fetch updated scenario to get new status
      const updatedScenario = await scenarioApi.getById(scenarioId);
      console.log('[Redux Thunk] runAnalysisV4 - Returning payload with analysisResult:', data);
      return { scenarioId, analysisResult: data, scenario: updatedScenario };
    } catch (error) {
      console.error('[Redux Thunk] runAnalysisV4 - Error:', error);
      return rejectWithValue(
        error instanceof Error ? error.message : 'Failed to run analysis (v4)'
      );
    }
  }
);

export const cancelAnalysisV4 = createAsyncThunk(
  'scenarios/cancelAnalysisV4',
  async ({ scenarioId, jobId }: { scenarioId: string; jobId: string }, { rejectWithValue }) => {
    try {
      const data = await scenarioApi.cancelAnalysisV4(scenarioId, jobId);
      // Fetch updated scenario to get new status
      const updatedScenario = await scenarioApi.getById(scenarioId);
      return { scenarioId, cancelResult: data, scenario: updatedScenario };
    } catch (error) {
      return rejectWithValue(
        error instanceof Error ? error.message : 'Failed to cancel analysis'
      );
    }
  }
);

export const runAnalysisV5 = createAsyncThunk(
  'scenarios/runAnalysisV5',
  async (scenarioId: string, { rejectWithValue }) => {
    try {
      console.log('[Redux Thunk] runAnalysisV5 - Calling API for scenarioId:', scenarioId);
      const data = await scenarioApi.runAnalysisV5(scenarioId);
      console.log('[Redux Thunk] runAnalysisV5 - API response data:', data);
      console.log('[Redux Thunk] runAnalysisV5 - data.job_id:', data?.job_id);
      // Fetch updated scenario to get new status
      const updatedScenario = await scenarioApi.getById(scenarioId);
      console.log('[Redux Thunk] runAnalysisV5 - Returning payload with analysisResult:', data);
      return { scenarioId, analysisResult: data, scenario: updatedScenario };
    } catch (error) {
      console.error('[Redux Thunk] runAnalysisV5 - Error:', error);
      return rejectWithValue(
        error instanceof Error ? error.message : 'Failed to run analysis (v5)'
      );
    }
  }
);


// Initial state
interface ScenariosState {
  scenarios: ScenarioOut[];
  currentScenario: ScenarioOut | null;
  currentAnalysisJobId: string | null;
  loading: {
    fetch: boolean;
    fetchById: boolean;
    create: boolean;
    update: boolean;
    delete: boolean;
    runAnalysis: boolean;
    runAnalysisV2: boolean;
    runAnalysisV4: boolean;
    cancelAnalysisV4: boolean;
  };
  error: string | null;
}

const initialState: ScenariosState = {
  scenarios: [],
  currentScenario: null,
  currentAnalysisJobId: null,
  loading: {
    fetch: false,
    fetchById: false,
    create: false,
    update: false,
    delete: false,
    runAnalysis: false,
    runAnalysisV2: false,
    runAnalysisV4: false,
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
    clearAnalysisJobId: (state) => {
      state.currentAnalysisJobId = null;
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
      })

      // Run analysis
      .addCase(runAnalysis.pending, (state, action) => {
        state.loading.runAnalysis = true;
        state.error = null;
        // Optimistically update scenario status to "Processing"
        const scenarioId = action.meta.arg;
        const scenario = state.currentScenario;
        if (scenario && scenario.id === scenarioId) {
          state.currentScenario = { ...scenario, status: "processing" as any };
        }
        const index = state.scenarios.findIndex((s) => s.id === scenarioId);
        if (index !== -1) {
          state.scenarios[index] = { ...state.scenarios[index], status: "processing" as any };
        }
      })
      .addCase(runAnalysis.fulfilled, (state, action) => {
        state.loading.runAnalysis = false;
        const { scenario } = action.payload;
        
        // Update scenario in list and current scenario
        if (scenario) {
          const index = state.scenarios.findIndex((s) => s.id === scenario.id);
          if (index !== -1) {
            state.scenarios[index] = scenario;
          }
          if (state.currentScenario?.id === scenario.id) {
            state.currentScenario = scenario;
          }
        }
        
        state.error = null;
      })
      .addCase(runAnalysis.rejected, (state, action) => {
        state.loading.runAnalysis = false;
        state.error = action.payload as string;
      })

      // Run analysis V2
      .addCase(runAnalysisV2.pending, (state, action) => {
        state.loading.runAnalysisV2 = true;
        state.error = null;
        // Optimistically update scenario status to "Processing"
        const scenarioId = action.meta.arg.scenarioId;
        const scenario = state.currentScenario;
        if (scenario && scenario.id === scenarioId) {
          state.currentScenario = { ...scenario, status: "processing" as any };
        }
        const index = state.scenarios.findIndex((s) => s.id === scenarioId);
        if (index !== -1) {
          state.scenarios[index] = { ...state.scenarios[index], status: "processing" as any };
        }
      })
      .addCase(runAnalysisV2.fulfilled, (state, action) => {
        state.loading.runAnalysisV2 = false;
        const { scenario } = action.payload;
        
        // Update scenario in list and current scenario
        if (scenario) {
          const index = state.scenarios.findIndex((s) => s.id === scenario.id);
          if (index !== -1) {
            state.scenarios[index] = scenario;
          }
          if (state.currentScenario?.id === scenario.id) {
            state.currentScenario = scenario;
          }
        }
        
        state.error = null;
      })
      .addCase(runAnalysisV2.rejected, (state, action) => {
        state.loading.runAnalysisV2 = false;
        state.error = action.payload as string;
      })

      // Run analysis V3
      .addCase(runAnalysisV4.pending, (state, action) => {
        state.loading.runAnalysisV4 = true;
        state.error = null;
        // Optimistically update scenario status to "Processing"
        const scenarioId = action.meta.arg;
        const scenario = state.currentScenario;
        if (scenario && scenario.id === scenarioId) {
          state.currentScenario = { ...scenario, status: "processing" as any };
        }
        const index = state.scenarios.findIndex((s) => s.id === scenarioId);
        if (index !== -1) {
          state.scenarios[index] = { ...state.scenarios[index], status: "processing" as any };
        }
      })
      .addCase(runAnalysisV4.fulfilled, (state, action) => {
        state.loading.runAnalysisV4 = false;
        // console.log('[Redux] runAnalysisV4.fulfilled - Full action payload:', JSON.stringify(action.payload, null, 2));
        const { scenario, analysisResult } = action.payload;
        
        // Store job_id from analysis result for WebSocket connection
        // console.log('[Redux] runAnalysisV4.fulfilled - analysisResult:', analysisResult);
        // console.log('[Redux] runAnalysisV4.fulfilled - analysisResult type:', typeof analysisResult);
        // console.log('[Redux] runAnalysisV4.fulfilled - analysisResult.job_id:', analysisResult?.job_id);
        
        if (analysisResult?.job_id) {
          // console.log('[Redux] Storing job_id:', analysisResult.job_id);
          state.currentAnalysisJobId = analysisResult.job_id;
        } else {
          // console.warn('[Redux] No job_id found in analysisResult. Keys:', analysisResult ? Object.keys(analysisResult) : 'analysisResult is null/undefined');
          // console.warn('[Redux] Full analysisResult:', analysisResult);
        }
        
        // Update scenario in list and current scenario
        if (scenario) {
          const index = state.scenarios.findIndex((s) => s.id === scenario.id);
          if (index !== -1) {
            state.scenarios[index] = scenario;
          }
          if (state.currentScenario?.id === scenario.id) {
            state.currentScenario = scenario;
          }
        }
        
        state.error = null;
      })
      .addCase(runAnalysisV4.rejected, (state, action) => {
        state.loading.runAnalysisV4 = false;
        state.error = action.payload as string;
        // Clear job_id on error
        state.currentAnalysisJobId = null;
      })
      .addCase(cancelAnalysisV4.pending, (state) => {
        state.loading.cancelAnalysisV4 = true;
      })
      .addCase(cancelAnalysisV4.fulfilled, (state, action) => {
        state.loading.cancelAnalysisV4 = false;
        const { scenario, cancelResult } = action.payload;
        // Clear the job ID since analysis is cancelled
        state.currentAnalysisJobId = null;
        // Update scenario if provided (stay on same view, just update data)
        if (scenario) {
          const index = state.scenarios.findIndex((s) => s.id === scenario.id);
          if (index !== -1) {
            state.scenarios[index] = scenario;
          }
          if (state.currentScenario?.id === scenario.id) {
            state.currentScenario = scenario;
          }
        }
        state.error = null;
      })
      .addCase(cancelAnalysisV4.rejected, (state, action) => {
        state.loading.cancelAnalysisV4 = false;
        state.error = action.payload as string;
        // Still clear job ID even on error
        state.currentAnalysisJobId = null;
      });
  },
});

// Export actions
export const {
  clearError,
  clearCurrentScenario,
  setCurrentScenario,
  clearScenarios,
  clearAnalysisJobId,
} = scenariosSlice.actions;

// Note: runAnalysisV4 and cancelAnalysisV4 are already exported at their definition above

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
export const selectScenarioRunningAnalysis = (state: { scenarios: ScenariosState }) => {
  const loading = state.scenarios.loading.runAnalysis || 
    state.scenarios.loading.runAnalysisV2 || 
    state.scenarios.loading.runAnalysisV4;
  // Also check if scenario status is "processing"
  const statusProcessing = state.scenarios.currentScenario?.status === "processing";
  return loading || statusProcessing;
};
export const selectCurrentAnalysisJobId = (state: { scenarios: ScenariosState }) =>
  state.scenarios.currentAnalysisJobId;

// Memoized selector for scenarios by project
export const selectScenariosByProject = (projectId: string) =>
  createSelector(
    [selectScenarios],
    (scenarios) => scenarios.filter((s) => s.project_id === projectId)
  );

// Export reducer
export default scenariosSlice.reducer;

