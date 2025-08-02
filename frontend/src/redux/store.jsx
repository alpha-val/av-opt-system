import { configureStore } from '@reduxjs/toolkit';
import nodeReducer from './nodeSlice.jsx';

export const store = configureStore({
  reducer: {
    nodes: nodeReducer,
  },
});

