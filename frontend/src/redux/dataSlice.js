import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import axios from 'axios';

const API_BASE_URL = 'http://127.0.0.1:5000/api/v1';

// Async thunk for uploading a file and receiving parsed text
export const uploadFileAndParseText = createAsyncThunk(
    'data/uploadFileAndParseText',
    async (formData, { rejectWithValue }) => {
        try {
            const response = await axios.post(`${API_BASE_URL}/file_upload`, formData, {
                headers: {
                    'Content-Type': 'multipart/form-data',
                },
            });
            return response.data; // Assuming the backend returns the parsed text
        } catch (error) {
            return rejectWithValue(error.response?.data || 'Failed to upload file and parse text');
        }
    }
);

const dataSlice = createSlice({
    name: 'data',
    initialState: {
        parsedText: '',
        status: 'idle', // 'idle' | 'loading' | 'succeeded' | 'failed'
        error: null,
    },
    reducers: {},
    extraReducers: (builder) => {
        builder
            .addCase(uploadFileAndParseText.pending, (state) => {
                state.status = 'loading';
                state.error = null;
            })
            .addCase(uploadFileAndParseText.fulfilled, (state, action) => {
                state.status = 'succeeded';
                state.parsedText = action.payload; // Store the parsed text
            })
            .addCase(uploadFileAndParseText.rejected, (state, action) => {
                state.status = 'failed';
                state.error = action.payload; // Store the error message
            });
    },
});

export default dataSlice.reducer;