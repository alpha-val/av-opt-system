import { createSlice, createAsyncThunk, PayloadAction, createSelector } from '@reduxjs/toolkit';
import {
  CostEstimateCreate,
  CostEstimateUpdate,
  CostEstimateOut,
} from '../types/api';
import { costEstimateApi, componentCostEstimateApi } from '../services/api';

// Async thunks for cost estimate operations
export const fetchCostEstimates = createAsyncThunk(
  'costEstimates/fetchCostEstimates',
  async (scenarioId?: string, { rejectWithValue }) => {
    try {
      // Fetch both regular cost estimates and component cost estimates
      const [regularEstimates, componentEstimates] = await Promise.all([
        costEstimateApi.listAll(scenarioId).catch(() => []), // Return empty array on error
        componentCostEstimateApi.listAll(scenarioId).catch(() => []), // Return empty array on error
      ]);
      
      // Convert component cost estimates to CostEstimateOut format for compatibility
      const normalizedComponentEstimates: CostEstimateOut[] = componentEstimates.map((ce: any) => ({
        id: ce.id,
        name: ce.name,
        description: ce.description || undefined,
        scenario_id: ce.scenario_id,
        created_at: ce.created_at,
        updated_at: ce.updated_at,
        metadata: {
          ...ce.metadata,
          cost_report: ce.cost_report,
          components_config: ce.components_config,
          // Mark as component-based for identification
          _isComponentBased: true,
        },
      }));
      
      // Combine both types and sort by created_at (newest first)
      const allEstimates = [...regularEstimates, ...normalizedComponentEstimates].sort(
        (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
      );
      
      return { costEstimates: allEstimates, scenarioId };
    } catch (error) {
      return rejectWithValue(
        error instanceof Error ? error.message : 'Failed to fetch cost estimates'
      );
    }
  }
);

export const fetchCostEstimateById = createAsyncThunk(
  'costEstimates/fetchCostEstimateById',
  async (costEstimateId: string, { rejectWithValue }) => {
    try {
      // Try regular cost estimate first
      try {
        const data = await costEstimateApi.getById(costEstimateId);
        return data;
      } catch (regularError) {
        // If not found, try component cost estimate
        try {
          const componentData = await componentCostEstimateApi.getById(costEstimateId);
          // Convert to CostEstimateOut format
          return {
            id: componentData.id,
            name: componentData.name,
            description: componentData.description || undefined,
            scenario_id: componentData.scenario_id,
            created_at: componentData.created_at,
            updated_at: componentData.updated_at,
            metadata: {
              ...componentData.metadata,
              cost_report: componentData.cost_report,
              components_config: componentData.components_config,
              _isComponentBased: true,
            },
          } as CostEstimateOut;
        } catch (componentError) {
          // If both fail, throw the original error
          throw regularError;
        }
      }
    } catch (error) {
      return rejectWithValue(
        error instanceof Error ? error.message : 'Failed to fetch cost estimate'
      );
    }
  }
);

export const createCostEstimate = createAsyncThunk(
  'costEstimates/createCostEstimate',
  async (costEstimateData: CostEstimateCreate, { rejectWithValue }) => {
    try {
      const costEstimate = await costEstimateApi.create(costEstimateData);
      return costEstimate;
    } catch (error) {
      return rejectWithValue(
        error instanceof Error ? error.message : 'Failed to create cost estimate'
      );
    }
  }
);

export const updateCostEstimate = createAsyncThunk(
  'costEstimates/updateCostEstimate',
  async (
    { costEstimateId, data }: { costEstimateId: string; data: CostEstimateUpdate },
    { rejectWithValue }
  ) => {
    try {
      const costEstimate = await costEstimateApi.update(costEstimateId, data);
      return costEstimate;
    } catch (error) {
      return rejectWithValue(
        error instanceof Error ? error.message : 'Failed to update cost estimate'
      );
    }
  }
);

export const deleteCostEstimate = createAsyncThunk(
  'costEstimates/deleteCostEstimate',
  async (costEstimateId: string, { rejectWithValue, getState }) => {
    try {
      // Check if it's a component-based cost estimate by looking at state
      const state = getState() as any;
      const costEstimate = state.costEstimates.costEstimates.find(
        (ce: CostEstimateOut) => ce.id === costEstimateId
      );
      
      // Try regular cost estimate first, then component cost estimate
      try {
        await costEstimateApi.delete(costEstimateId);
        return costEstimateId;
      } catch (regularError: any) {
        // If 404 or not found, try component cost estimate
        if (regularError.response?.status === 404 || costEstimate?.metadata?._isComponentBased) {
          try {
            await componentCostEstimateApi.delete(costEstimateId);
            return costEstimateId;
          } catch (componentError) {
            // If both fail, throw the original error
            throw regularError;
          }
        } else {
          throw regularError;
        }
      }
    } catch (error) {
      return rejectWithValue(
        error instanceof Error ? error.message : 'Failed to delete cost estimate'
      );
    }
  }
);

// State interface
interface CostEstimatesState {
  costEstimates: CostEstimateOut[];
  currentCostEstimate: CostEstimateOut | null;
  loading: {
    fetch: boolean;
    fetchById: boolean;
    create: boolean;
    update: boolean;
    delete: boolean;
  };
  error: string | null;
}

// Initial state
const initialState: CostEstimatesState = {
  costEstimates: [],
  currentCostEstimate: null,
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
const costEstimatesSlice = createSlice({
  name: 'costEstimates',
  initialState,
  reducers: {
    clearError: (state) => {
      state.error = null;
    },
    clearCurrentCostEstimate: (state) => {
      state.currentCostEstimate = null;
    },
  },
  extraReducers: (builder) => {
    // Fetch cost estimates
    builder
      .addCase(fetchCostEstimates.pending, (state) => {
        state.loading.fetch = true;
        state.error = null;
      })
      .addCase(fetchCostEstimates.fulfilled, (state, action) => {
        state.loading.fetch = false;
        state.costEstimates = action.payload.costEstimates;
      })
      .addCase(fetchCostEstimates.rejected, (state, action) => {
        state.loading.fetch = false;
        state.error = action.payload as string;
      });

    // Fetch cost estimate by ID
    builder
      .addCase(fetchCostEstimateById.pending, (state) => {
        state.loading.fetchById = true;
        state.error = null;
      })
      .addCase(fetchCostEstimateById.fulfilled, (state, action) => {
        state.loading.fetchById = false;
        state.currentCostEstimate = action.payload;
      })
      .addCase(fetchCostEstimateById.rejected, (state, action) => {
        state.loading.fetchById = false;
        state.error = action.payload as string;
      });

    // Create cost estimate
    builder
      .addCase(createCostEstimate.pending, (state) => {
        state.loading.create = true;
        state.error = null;
      })
      .addCase(createCostEstimate.fulfilled, (state, action) => {
        state.loading.create = false;
        state.costEstimates.unshift(action.payload);
      })
      .addCase(createCostEstimate.rejected, (state, action) => {
        state.loading.create = false;
        state.error = action.payload as string;
      });

    // Update cost estimate
    builder
      .addCase(updateCostEstimate.pending, (state) => {
        state.loading.update = true;
        state.error = null;
      })
      .addCase(updateCostEstimate.fulfilled, (state, action) => {
        state.loading.update = false;
        const index = state.costEstimates.findIndex(
          (ce) => ce.id === action.payload.id
        );
        if (index !== -1) {
          state.costEstimates[index] = action.payload;
        }
        if (state.currentCostEstimate?.id === action.payload.id) {
          state.currentCostEstimate = action.payload;
        }
      })
      .addCase(updateCostEstimate.rejected, (state, action) => {
        state.loading.update = false;
        state.error = action.payload as string;
      });

    // Delete cost estimate
    builder
      .addCase(deleteCostEstimate.pending, (state) => {
        state.loading.delete = true;
        state.error = null;
      })
      .addCase(deleteCostEstimate.fulfilled, (state, action) => {
        state.loading.delete = false;
        state.costEstimates = state.costEstimates.filter(
          (ce) => ce.id !== action.payload
        );
        if (state.currentCostEstimate?.id === action.payload) {
          state.currentCostEstimate = null;
        }
      })
      .addCase(deleteCostEstimate.rejected, (state, action) => {
        state.loading.delete = false;
        state.error = action.payload as string;
      });
  },
});

// Selectors
export const selectCostEstimates = (state: any) => state.costEstimates.costEstimates;
export const selectCurrentCostEstimate = (state: any) => state.costEstimates.currentCostEstimate;
export const selectCostEstimatesLoading = (state: any) => state.costEstimates.loading;
export const selectCostEstimatesError = (state: any) => state.costEstimates.error;
export const selectCostEstimateCreating = (state: any) => state.costEstimates.loading.create;
export const selectCostEstimateDeleting = (state: any) => state.costEstimates.loading.delete;

// Memoized selector for cost estimates by scenario
export const selectCostEstimatesByScenario = (scenarioId: string) =>
  createSelector(
    [selectCostEstimates],
    (costEstimates) => costEstimates.filter((ce) => ce.scenario_id === scenarioId)
  );

// Actions
export const { clearError, clearCurrentCostEstimate } = costEstimatesSlice.actions;

// Reducer
export default costEstimatesSlice.reducer;

