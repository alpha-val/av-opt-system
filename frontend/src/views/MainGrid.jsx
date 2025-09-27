import React from 'react';
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
                {/* <Box
                    sx={{
                        p: 3,
                        height: '100%',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                    }}
                >
                    <Typography
                        variant="h4"
                        color="textSecondary"
                        sx={{
                            textAlign: 'center',
                            fontWeight: 300,
                        }}
                    >
                        <AppContent />
                    </Typography>
                </Box> */}
            </Box>
        </Box>
    );
};

export default MainGrid;