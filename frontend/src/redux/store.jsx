import { configureStore } from '@reduxjs/toolkit';
import projectsReducer from './projectSlice';
import userReducer from './userSlice';
import authReducer from './authSlice';

export const store = configureStore({
  reducer: {
    projects: projectsReducer,
    user: userReducer,
    auth: authReducer,
  },
});

export default store;

