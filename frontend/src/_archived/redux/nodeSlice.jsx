import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { createSelector } from 'reselect';
import axios from 'axios';

const API_BASE_URL = 'http://127.0.0.1:5000/costing/v1';

// Async thunk to fetch nodes from the backend
export const fetchNodes = createAsyncThunk(
    'nodes/fetchNodes',
    async (type, { rejectWithValue }) => {
        try {
            const response = await fetch(`${API_BASE_URL}/entities`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ "type": type }),
            });
            const data = await response.json();
            console.log("[DEBUG : nodeSlice > ", data);
            return data.nodes || []; // Extract nodes array from backend response
        } catch (error) {
            return rejectWithValue(error.message || 'Failed to fetch nodes');
        }
    }
);


const nodeSlice = createSlice({
    name: 'nodes',
    initialState: {
        nodes: [],
        status: 'idle', // 'idle' | 'loading' | 'succeeded' | 'failed'
        error: null,
    },
    reducers: {},
    extraReducers: (builder) => {
        builder
            .addCase(fetchNodes.pending, (state) => {
                state.status = 'loading';
                state.error = null;
            })
            .addCase(fetchNodes.fulfilled, (state, action) => {
                state.status = 'succeeded';
                state.nodes = action.payload;
            })
            .addCase(fetchNodes.rejected, (state, action) => {
                state.status = 'failed';
                state.error = action.payload;
            });
    },
});

export default nodeSlice.reducer;

// Selector to get nodes from the state
const nodesSelector = (state) => state.nodes.nodes;

// Memoized selector using reselect
export const memoizedNodesSelector = createSelector(
    [nodesSelector],
    (nodes) => nodes // Memoizes the nodes array
);