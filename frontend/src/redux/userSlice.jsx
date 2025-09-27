import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';

// API base URL - adjust as needed
const API_BASE_URL = 'http://localhost:8000/api/v1';

// Async thunks for user operations
export const fetchUser = createAsyncThunk(
  'user/fetchUser',
  async (userId, { rejectWithValue }) => {
    try {
      const response = await fetch(`${API_BASE_URL}/users/${userId}`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      return data;
    } catch (error) {
      return rejectWithValue(error.message);
    }
  }
);

export const fetchAllUsers = createAsyncThunk(
  'user/fetchAllUsers',
  async (_, { rejectWithValue }) => {
    try {
      const response = await fetch(`${API_BASE_URL}/users`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      return data.users || data; // Handle different response formats
    } catch (error) {
      return rejectWithValue(error.message);
    }
  }
);

export const createUser = createAsyncThunk(
  'user/createUser',
  async (userData, { rejectWithValue }) => {
    try {
      const response = await fetch(`${API_BASE_URL}/users`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(userData),
      });
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      return data;
    } catch (error) {
      return rejectWithValue(error.message);
    }
  }
);

export const updateUser = createAsyncThunk(
  'user/updateUser',
  async ({ userId, userData }, { rejectWithValue }) => {
    try {
      const response = await fetch(`${API_BASE_URL}/users/${userId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(userData),
      });
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      return data;
    } catch (error) {
      return rejectWithValue(error.message);
    }
  }
);

export const deleteUser = createAsyncThunk(
  'user/deleteUser',
  async (userId, { rejectWithValue }) => {
    try {
      const response = await fetch(`${API_BASE_URL}/users/${userId}`, {
        method: 'DELETE',
      });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return userId; // Return the deleted user ID
    } catch (error) {
      return rejectWithValue(error.message);
    }
  }
);

// Initial state
const initialState = {
  users: [],
  currentUser: null,
  loading: false,
  error: null,
  // Loading states for individual operations
  creating: false,
  updating: false,
  deleting: false,
  fetchingUser: false,
  fetchingUsers: false,
};

// Slice
const userSlice = createSlice({
  name: 'user',
  initialState,
  reducers: {
    clearError: (state) => {
      state.error = null;
    },
    clearCurrentUser: (state) => {
      state.currentUser = null;
    },
    setCurrentUser: (state, action) => {
      state.currentUser = action.payload;
    },
    clearUsers: (state) => {
      state.users = [];
    },
  },
  extraReducers: (builder) => {
    builder
      // Fetch single user
      .addCase(fetchUser.pending, (state) => {
        state.fetchingUser = true;
        state.error = null;
      })
      .addCase(fetchUser.fulfilled, (state, action) => {
        state.fetchingUser = false;
        state.currentUser = action.payload;
        state.error = null;
      })
      .addCase(fetchUser.rejected, (state, action) => {
        state.fetchingUser = false;
        state.error = action.payload;
      })

      // Fetch all users
      .addCase(fetchAllUsers.pending, (state) => {
        state.fetchingUsers = true;
        state.error = null;
      })
      .addCase(fetchAllUsers.fulfilled, (state, action) => {
        state.fetchingUsers = false;
        state.users = action.payload;
        state.error = null;
      })
      .addCase(fetchAllUsers.rejected, (state, action) => {
        state.fetchingUsers = false;
        state.error = action.payload;
      })

      // Create user
      .addCase(createUser.pending, (state) => {
        state.creating = true;
        state.error = null;
      })
      .addCase(createUser.fulfilled, (state, action) => {
        state.creating = false;
        // Note: The API returns success info, not the full user object
        // You might want to fetch the user after creation or modify the API
        state.error = null;
      })
      .addCase(createUser.rejected, (state, action) => {
        state.creating = false;
        state.error = action.payload;
      })

      // Update user
      .addCase(updateUser.pending, (state) => {
        state.updating = true;
        state.error = null;
      })
      .addCase(updateUser.fulfilled, (state, action) => {
        state.updating = false;
        const updatedUser = action.payload;
        
        // Update user in users array
        const index = state.users.findIndex(
          (user) => user.user_id === updatedUser.user_id || user._id === updatedUser._id
        );
        if (index !== -1) {
          state.users[index] = updatedUser;
        }
        
        // Update current user if it's the same one
        if (state.currentUser && 
            (state.currentUser.user_id === updatedUser.user_id || 
             state.currentUser._id === updatedUser._id)) {
          state.currentUser = updatedUser;
        }
        
        state.error = null;
      })
      .addCase(updateUser.rejected, (state, action) => {
        state.updating = false;
        state.error = action.payload;
      })

      // Delete user
      .addCase(deleteUser.pending, (state) => {
        state.deleting = true;
        state.error = null;
      })
      .addCase(deleteUser.fulfilled, (state, action) => {
        state.deleting = false;
        const deletedUserId = action.payload;
        
        // Remove user from users array
        state.users = state.users.filter(
          (user) => user.user_id !== deletedUserId && user._id !== deletedUserId
        );
        
        // Clear current user if it was deleted
        if (state.currentUser && 
            (state.currentUser.user_id === deletedUserId || 
             state.currentUser._id === deletedUserId)) {
          state.currentUser = null;
        }
        
        state.error = null;
      })
      .addCase(deleteUser.rejected, (state, action) => {
        state.deleting = false;
        state.error = action.payload;
      });
  },
});

// Export actions
export const { clearError, clearCurrentUser, setCurrentUser, clearUsers } = userSlice.actions;

// Selectors
export const selectUsers = (state) => state.user.users;
export const selectCurrentUser = (state) => state.user.currentUser;
export const selectUsersLoading = (state) => state.user.loading;
export const selectUsersError = (state) => state.user.error;
export const selectUserCreating = (state) => state.user.creating;
export const selectUserUpdating = (state) => state.user.updating;
export const selectUserDeleting = (state) => state.user.deleting;
export const selectUserFetchingUser = (state) => state.user.fetchingUser;
export const selectUserFetchingUsers = (state) => state.user.fetchingUsers;

// Export reducer
export default userSlice.reducer;