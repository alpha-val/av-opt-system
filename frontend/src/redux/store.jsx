import { configureStore } from '@reduxjs/toolkit';
import dataReducer from './dataSlice';
import projectsReducer from './projectSlice';
import userReducer from './userSlice';
import authReducer from './authSlice';
import scenarioReducer from './scenarioSlice';
import optionReducer from './optionSlice';

export const store = configureStore({
  reducer: {
    data: dataReducer,
    projects: projectsReducer,
    user: userReducer,
    auth: authReducer,
    scenarios: scenarioReducer,
    options: optionReducer,
  },
});

export default store;

