import React from 'react';
import { useNavigate } from 'react-router-dom';
import Nav from '../../components/Nav';
// import ProjectDashboard from './ProjectDashboard';
import { Box } from '@mui/material';

const ProjectView = () => {
    const navigate = useNavigate();

    const handleBackToDashboard = () => {
        navigate('/');
    };

    return (
        <Box sx={{ display: 'flex', width: '100%' }}>
            {/* Project content */}
            <Box sx={{ flexGrow: 1 }}>
                {/* <ProjectDashboard onBackToDashboard={handleBackToDashboard} /> */}
            </Box>
        </Box>
    );
};

export default ProjectView;