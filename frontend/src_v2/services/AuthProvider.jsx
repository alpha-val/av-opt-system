import React, { useEffect } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { CircularProgress, Box } from '@mui/material';
import UserAuth from '../views/UserAuth';
import {
    selectIsAuthenticated,
    selectFetchingUser,
    selectUser,
    getCurrentUser,
} from '../redux/authSlice';

const AuthProvider = ({ children }) => {
    const dispatch = useDispatch();
    const isAuthenticated = useSelector(selectIsAuthenticated);
    const fetchingUser = useSelector(selectFetchingUser);
    const user = useSelector(selectUser);

    useEffect(() => {
        // Check for existing token and fetch user data
        const token = localStorage.getItem('access_token');

        if (token && isAuthenticated && !user) {
            // We have a token but no user data, fetch it
            dispatch(getCurrentUser());
        } else if (!token && isAuthenticated) {
            // Token was removed but Redux still thinks we're authenticated
            // This can happen if token was cleared elsewhere
            window.location.reload(); // Force a clean state
        }
    }, [dispatch, isAuthenticated, user]);

    // Show loading spinner while checking authentication
    if (fetchingUser) {
        return (
            <Box
                sx={{
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    justifyContent: 'center',
                    minHeight: '100vh',
                    gap: 2,
                }}
            >
                <CircularProgress size={60} />
                <Box sx={{ textAlign: 'center' }}>
                    Loading your account...
                </Box>
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