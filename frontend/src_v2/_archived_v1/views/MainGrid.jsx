import React, { useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { getCurrentUser } from '../redux/authSlice';
import {
    Box,
    Typography,
    useTheme,
    useMediaQuery,
} from '@mui/material';
import Nav from '../components/Nav';
import AppContent from './AppContent';

const MainGrid = () => {
    const theme = useTheme();
    const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
    const isAdmin = useSelector((state) => state.auth.isAdmin);

    return (
        <Box sx={{ display: 'flex', height: '100vh' }}>
            {/* Navigation */}
            <Nav />

            {/* Main Content Area */}
            <Box
                component="main"
                sx={{
                    flexGrow: 1,
                    width: '100%',
                    minHeight: '100vh',
                    marginTop: isMobile ? '64px' : 0,
                    transition: theme.transitions.create('margin', {
                        easing: theme.transitions.easing.sharp,
                        duration: theme.transitions.duration.leavingScreen,
                    }),
                }}
            >
                <AppContent />
            </Box>
        </Box>
    );
};

export default MainGrid;