import React from 'react';
import {
    Box,
    Typography,
    Button,
    useTheme,
    Chip,
    IconButton
} from '@mui/material';
import {
    Add as AddIcon,
    MoreVert as MoreVertIcon,
} from '@mui/icons-material';
import DataTable from '../components/DataTable';
import { useDialogs } from '../hooks/useDialogs/useDialogs';
const AppContent = () => {
    const theme = useTheme();
    const dialogs = useDialogs();
    // Mock data - replace with actual data from your state/API
    const userName = "Sarah";
    const currentDate = new Date().toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        timeZoneName: 'short'
    });

    const userStats = {
        lastModified: "Sep 07 2025\n03:30 PM EST",
        storageUsed: "0.6%",
        storageDetail: "(30 MB of 5 GB)",
        documentsIngested: 25,
        projectsCreated: 7,
        scenariosCreated: 18
    };

    // Updated headers format - array of objects with key and display_value
    const projectHeaders = [
        { key: "name", display_value: "Project" },
        { key: "status", display_value: "Status" },
        { key: "lastUpdated", display_value: "Last Updated" },
        { key: "estimateReports", display_value: "Estimate Reports" },
        { key: "options", display_value: "Options" }
    ];

    // Updated data format - keys match header keys
    const projectData = [
        {
            name: "Copper Mine Expansion",
            status: <Chip label="Active" color="success" size="small" variant="outlined" />,
            lastUpdated: <Typography variant="body2" color="primary">2025-08-20</Typography>,
            estimateReports: [
                "3 completed", "2 pending review"
            ],
            options: <IconButton size="small"><MoreVertIcon /></IconButton>
        },
        {
            name: "Iron Ore Processing Plant",
            status: <Chip label="Needs Review" color="warning" size="small" variant="outlined" />,
            lastUpdated: <Typography variant="body2" color="primary">2025-08-15</Typography>,
            estimateReports: [
                "0 completed", "1 pending review"
            ],
            options: <IconButton size="small"><MoreVertIcon /></IconButton>
        },
        {
            name: "Gold Mine Development",
            status: <Chip label="Awaiting Input" color="info" size="small" variant="outlined" />,
            lastUpdated: <Typography variant="body2" color="primary">2025-08-18</Typography>,
            estimateReports: [
                "1 completed", "1 awaiting inputs"
            ],
            options: <IconButton size="small"><MoreVertIcon /></IconButton>
        },
        {
            name: "Crusher Installation",
            status: <Chip label="Completed" color="default" size="small" variant="outlined" />,
            lastUpdated: <Typography variant="body2" color="primary">2025-07-28</Typography>,
            estimateReports: [
                "4 completed"
            ],
            options: <IconButton size="small"><MoreVertIcon /></IconButton>
        }
    ];

    const getStatusColor = (status) => {
        switch (status) {
            case 'Active':
                return 'success';
            case 'Needs Review':
                return 'warning';
            case 'Awaiting Input':
                return 'info';
            case 'Completed':
                return 'default';
            default:
                return 'default';
        }
    };

    const handleAlert = async () => {
        await dialogs.alert('This is an alert message!', {
            title: 'Information',
            okText: 'Got it'
        });
        console.log('Alert closed');
    };

    const handleConfirm = async () => {
        const result = await dialogs.confirm('Are you sure you want to delete this item?', {
            title: 'Confirm Delete',
            severity: 'error',
            okText: 'Delete',
            cancelText: 'Keep'
        });

        if (result) {
            console.log('User confirmed deletion');
            // Perform delete action
        } else {
            console.log('User cancelled deletion');
        }
    };

    const handlePrompt = async () => {
        const projectName = await dialogs.prompt('Enter a name for your new project:', {
            title: 'Create New Project',
            okText: 'Create',
            cancelText: 'Cancel'
        });

        if (projectName) {
            console.log('Creating project:', projectName);
            // Create project with the name
        } else {
            console.log('Project creation cancelled');
        }
    };

    return (
        <Box sx={{ p: 3, maxWidth: "100%", width: '100%' }}>
            {/* Header Section */}
            <Box sx={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                mb: 4,
                borderBottom: 1,
                borderColor: 'divider',
                pb: 2
            }}>
                <Typography variant="h4" fontWeight="bold">
                    Welcome, {userName}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                    {currentDate}
                </Typography>
            </Box>

            {/* User Data Summary Section */}


            {/* Projects Section */}
            <Box>
                <Box sx={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    mb: 3
                }}>
                    <Typography variant="h5" fontWeight="bold">
                        Your Projects
                    </Typography>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                        <Typography variant="body2" color="text.secondary">
                            4 of 7 shown
                        </Typography>
                        <Button
                            variant="contained"
                            startIcon={<AddIcon />}
                            sx={{ ml: 2 }}
                            onClick={handlePrompt}
                        >
                            New Project
                        </Button>
                    </Box>
                </Box>

                <DataTable
                    headers={projectHeaders}
                    data={projectData}
                    // onRowClick={handleRowClick}
                    containerSx={{ borderRadius: 2 }}
                />

                <Box sx={{ display: 'flex', justifyContent: 'flex-end', mt: 2 }}>
                    <Button variant="text" color="primary">
                        View All
                    </Button>
                </Box>
            </Box>
        </Box>
    );
};

export default AppContent;