import { createSlice, createAsyncThunk } from "@reduxjs/toolkit";
import axios from "axios";

const API_BASE_URL = "http://127.0.0.1:5000/costing/v1";

// Async thunk for uploading a file and receiving parsed text
export const uploadFileAndParseText = createAsyncThunk(
  "data/uploadFileAndParseText",
  async (formData, { rejectWithValue }) => {
    try {
      // Send the file to the API endpoint
      const response = await axios.post(
        `${API_BASE_URL}/ingest`, // API endpoint for file ingestion
        formData,
        {
          headers: {
            "Content-Type": "multipart/form-data", // Required for file uploads
          },
        }
      );

      // Return the parsed text or response data
      return response.data; // Assuming the backend returns parsed text or a summary
    } catch (error) {
      // Handle errors and return a meaningful message
      return rejectWithValue(
        error.response?.data || "Failed to upload file and parse text"
      );
    }
  }
);

// Async thunk for fetching the whole Neo4j graph
export const fetchFullGraph = createAsyncThunk(
  "data/fetchFullGraph",
  async (_, { rejectWithValue }) => {
    try {
      const response = await axios.get(`${API_BASE_URL}/graph`);
      return response.data; // { nodes: [...], edges: [...] }
    } catch (error) {
      return rejectWithValue(error.response?.data || "Failed to fetch graph");
    }
  }
);

// Thunk: send user's question to backend
export const userQuery = createAsyncThunk(
  "data/userQuery",
  async (question, { rejectWithValue }) => {
    try {
      const res = await fetch(`${API_BASE_URL}/user_query`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question }),
      });
      if (!res.ok) {
        const text = await res.text();
        throw new Error(text || `HTTP ${res.status}`);
      }
      const data = await res.json();
      return data; // store entire response; adjust if backend returns {result: ...}
    } catch (err) {
      return rejectWithValue(err.message || "Request failed");
    }
  }
);

const initialState = {
  parsedText: "",
  status: "idle", // 'idle' | 'loading' | 'succeeded' | 'failed'
  error: null,
  graph: {
    nodes: [],
    edges: [],
  },
  graphStatus: "idle", // 'idle' | 'loading' | 'succeeded' | 'failed'
  graphError: null,
  query_result: null,
  queryStatus: "idle",
  queryError: null,
};

const dataSlice = createSlice({
  name: "data",
  initialState,
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(uploadFileAndParseText.pending, (state) => {
        state.status = "loading";
        state.error = null;
      })
      .addCase(uploadFileAndParseText.fulfilled, (state, action) => {
        state.status = "succeeded";
        state.parsedText = action.payload; // Store the parsed text
      })
      .addCase(uploadFileAndParseText.rejected, (state, action) => {
        state.status = "failed";
        state.error = action.payload; // Store the error message
      })
      // Extra reducers for fetchFullGraph
      .addCase(fetchFullGraph.pending, (state) => {
        state.graphStatus = "loading";
        state.graphError = null;
      })
      .addCase(fetchFullGraph.fulfilled, (state, action) => {
        state.graphStatus = "succeeded";
        state.graph = action.payload;
      })
      .addCase(fetchFullGraph.rejected, (state, action) => {
        state.graphStatus = "failed";
        state.graphError = action.payload;
      })
      .addCase(userQuery.pending, (state) => {
        state.queryStatus = "loading";
        state.queryError = null;
      })
      .addCase(userQuery.fulfilled, (state, action) => {
        state.queryStatus = "succeeded";
        state.query_result = action.payload;
      })
      .addCase(userQuery.rejected, (state, action) => {
        state.queryStatus = "failed";
        state.queryError =
          action.payload || action.error?.message || "Unknown error";
      });
  },
});

export const selectQueryResult = (state) => state.data.query_result;

export default dataSlice.reducer;
