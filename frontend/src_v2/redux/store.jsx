import { configureStore } from "@reduxjs/toolkit";
import dataReducer from "./dataSlice";
import projectsReducer from "./projectSlice";
import userReducer from "./userSlice";
import authReducer from "./authSlice";
import scenarioReducer from "./scenarioSlice";
import optionReducer from "./optionSlice";
import documentsReducer from "./documentSlice";

export const store = configureStore({
  reducer: {
    data: dataReducer,
    projects: projectsReducer,
    user: userReducer,
    auth: authReducer,
    scenarios: scenarioReducer,
    options: optionReducer,
    documents: documentsReducer,
  },
  // Add this to ensure state is properly initialized
  preloadedState: {
    projects: {
      projects: [],
      projectsCache: {},
      currentProject: null,
      projectStats: null,
      pagination: { total: 0, page: 1, limit: 10 },
      loading: {
        fetch: false,
        create: false,
        update: false,
        delete: false,
        stats: false,
      },
      error: null,
    },
  },
});

export default store;
