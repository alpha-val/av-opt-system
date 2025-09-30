import React, { useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { getCurrentUser } from '../redux/authSlice';
import {
    Box,
    Grid,
    Typography,
    useTheme,
    useMediaQuery,
} from '@mui/material';
import Nav from '../components/Nav';
import AppContent from './AppContent';

const MainGrid = () => {
    const theme = useTheme();
    const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
    // Get if the user is_admin
    const isAdmin = useSelector((state) => state.auth.isAdmin);
    console.log("[DEBUG] is admin user? ", isAdmin);

    const drawerWidth = 240;
    const collapsedWidth = 72;

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
                    marginTop: isMobile ? '64px' : 0, // Account for mobile AppBar
                    transition: theme.transitions.create('margin', {
                        easing: theme.transitions.easing.sharp,
                        duration: theme.transitions.duration.leavingScreen,
                    }),
                }}
            >
                {/* Content Container */}
                <AppContent />
            </Box>
        </Box>
    );
};

export default MainGrid;