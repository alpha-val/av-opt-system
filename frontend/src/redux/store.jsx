import { configureStore } from "@reduxjs/toolkit";
import authReducer from "./authSlice";
import userReducer from "./userSlice";
export const store = configureStore({
  reducer: {
    auth: authReducer,
    user: userReducer,
  },
  // Add this to ensure state is properly initialized
  preloadedState: {
    // projects: {
    //   projects: [],
    //   projectsCache: {},
    //   currentProject: null,
    //   projectStats: null,
    //   pagination: { total: 0, page: 1, limit: 10 },
    //   loading: {
    //     fetch: false,
    //     create: false,
    //     update: false,
    //     delete: false,
    //     stats: false,
    //   },
    //   error: null,
    // },
  },
});

export default store;
