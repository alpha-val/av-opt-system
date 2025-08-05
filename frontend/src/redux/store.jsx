import { configureStore } from '@reduxjs/toolkit';
import dataReducer from './dataSlice.js';
import nodeReducer from './nodeSlice.jsx';

export const store = configureStore({
  reducer: {
    data: dataReducer,
    nodes: nodeReducer,
  },
});

