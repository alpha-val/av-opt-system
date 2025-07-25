import { configureStore } from '@reduxjs/toolkit';
// import athleteReducer from './athleteSlice.jsx';
// import coachReducer from './coachSlice.jsx';
// import eventReducer from './eventSlice.jsx';
// import inviteReducer from './inviteSlice.jsx';
// import userReducer from './userSlice.jsx';

export const store = configureStore({
  reducer: {
    // athletes: athleteReducer,
    // coaches: coachReducer,
    // events: eventReducer,
    // invites: inviteReducer,
    // users: userReducer,
  },
});

