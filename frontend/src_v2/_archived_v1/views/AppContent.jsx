import React, { useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Box } from '@mui/material';
import Dashboard from './Dashboard';

const AppContent = () => {
    const navigate = useNavigate();

    // Navigate to project view using URL routing
    const handleOpenProject = useCallback((projectId) => {
        navigate(`/projects/${projectId}`);
    }, [navigate]);

    return (
        <Box sx={{
            width: '100%',
            height: '100vh',
            overflow: 'hidden'
        }}>
            <Dashboard onOpenProject={handleOpenProject} />
        </Box>
    );
};

export default AppContent;