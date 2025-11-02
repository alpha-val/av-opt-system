import React from 'react';
import { useNavigate } from 'react-router-dom';
import Nav from '../../components/Nav';
// import ProjectDashboard from './ProjectDashboard';
import { Box } from '@mui/material';
import Settings from "./Settings"

const SettingsView = () => {
    const navigate = useNavigate();

    const handleBackToDashboard = () => {
        navigate('/');
    };

    return (
        <Box sx={{ display: 'flex', width: '100%' }}>
            {/* Navigation sidebar */}
            <Nav />

            {/* Project content */}
            <Box sx={{ flexGrow: 1 }}>
                <Settings />
            </Box>
        </Box>
    );
};

export default SettingsView;