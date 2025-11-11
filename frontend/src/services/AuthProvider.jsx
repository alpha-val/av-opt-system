import React, { useEffect, useRef } from "react";
import { useSelector, useDispatch } from "react-redux";
import { CircularProgress, Box } from "@mui/material";
import UserAuth from "../views/UserAuth";
import {
  selectIsAuthenticated,
  selectFetchingUser,
  selectUser,
  getCurrentUser,
  clearAuth,
} from "../redux/authSlice";

const AuthProvider = ({ children }) => {
  const dispatch = useDispatch();
  const isAuthenticated = useSelector(selectIsAuthenticated);
  const fetchingUser = useSelector(selectFetchingUser);
  const user = useSelector(selectUser);
  const hasCheckedAuth = useRef(false);

  useEffect(() => {
    // Only check auth once on mount
    if (hasCheckedAuth.current) return;
    hasCheckedAuth.current = true;

    // Check for existing token and validate it
    const token = localStorage.getItem("access_token");

    if (token) {
      // We have a token - validate it by fetching user data
      // This will set isAuthenticated to true if token is valid
      dispatch(getCurrentUser());
    } else if (isAuthenticated) {
      // Token was removed but Redux still thinks we're authenticated
      // Clear auth state
      dispatch(clearAuth());
    }
  }, [dispatch, isAuthenticated]);

  // Show loading spinner while checking/validating authentication
  if (fetchingUser) {
    return (
      <Box
        sx={{
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          minHeight: "100vh",
          gap: 2,
        }}
      >
        <CircularProgress size={60} />
        <Box sx={{ textAlign: "center" }}>Loading your account...</Box>
      </Box>
    );
  }

  // Show login if not authenticated
  if (!isAuthenticated) {
    return <UserAuth />;
  }

  // Show protected content if authenticated
  return children;
};

export default AuthProvider;
