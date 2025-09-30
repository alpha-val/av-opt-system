import { configureStore } from '@reduxjs/toolkit';
import dataReducer from './dataSlice';
import projectsReducer from './projectSlice';
import userReducer from './userSlice';
import authReducer from './authSlice';

export const store = configureStore({
  reducer: {
    data: dataReducer,
    projects: projectsReducer,
    user: userReducer,
    auth: authReducer,
  },
});

export default store;

