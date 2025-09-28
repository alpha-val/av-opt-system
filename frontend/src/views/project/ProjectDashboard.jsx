import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';
import {
    Box,
    Typography,
    Breadcrumbs,
    Link,
    Tab,
    Tabs,
    Paper,
    CircularProgress,
    Alert,
    IconButton,
    Tooltip,
} from '@mui/material';
import {
    NavigateNext as NavigateNextIcon,
    ArrowBack as ArrowBackIcon,
    Folder as FolderIcon,
    Dashboard as DashboardIcon,
    Assessment as ScenariosIcon,
    Analytics as AnalysisIcon,
    Info as InfoIcon,
} from '@mui/icons-material';
import {
    fetchProject,
    selectCurrentProject,
    selectProjectsLoading,
    selectProjectsError,
} from '../../redux/projectSlice';

// Tab configuration
const PROJECT_TABS = [
    {
        id: 'sources',
        label: 'Sources',
        icon: <FolderIcon />,
        description: 'Project documents and data uploads'
    },
    {
        id: 'base-case',
        label: 'Base Case',
        icon: <DashboardIcon />,
        description: 'Data gleaned from uploaded documents'
    },
    {
        id: 'scenarios',
        label: 'Scenarios',
        icon: <ScenariosIcon />,
        description: 'Create deltas from base case for costing'
    },
    {
        id: 'analysis',
        label: 'Analysis',
        icon: <AnalysisIcon />,
        description: 'Compare and model base cases'
    }
];

const ProjectDashboard = () => {
    const { projectId } = useParams();
    const navigate = useNavigate();
    const dispatch = useDispatch();

    // Redux state
    const currentProject = useSelector(selectCurrentProject);
    const loading = useSelector(selectProjectsLoading);
    const error = useSelector(selectProjectsError);

    // Local state
    const [activeTab, setActiveTab] = useState('sources');

    // Load project data when component mounts or projectId changes
    useEffect(() => {
        if (projectId) {
            dispatch(fetchProject(projectId));
        }
    }, [dispatch, projectId]);

    // Handle tab change
    const handleTabChange = (event, newValue) => {
        setActiveTab(newValue);
    };

    // Handle breadcrumb navigation
    const handleProjectsClick = (event) => {
        event.preventDefault();
        navigate('/');
    };

    // Format date for display
    const formatDate = (dateString) => {
        if (!dateString) return '';
        return new Date(dateString).toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
            timeZoneName: 'short'
        });
    };

    // Loading state
    if (loading.fetch) {
        return (
            <Box sx={{
                display: 'flex',
                justifyContent: 'center',
                alignItems: 'center',
                minHeight: '50vh'
            }}>
                <CircularProgress />
                <Typography variant="body1" sx={{ ml: 2 }}>
                    Loading project...
                </Typography>
            </Box>
        );
    }

    // Error state
    if (error) {
        return (
            <Box sx={{ p: 3 }}>
                <Alert severity="error">
                    {error}
                </Alert>
            </Box>
        );
    }

    // Project not found
    if (!currentProject) {
        return (
            <Box sx={{ p: 3 }}>
                <Alert severity="warning">
                    Project not found
                </Alert>
            </Box>
        );
    }

    return (
        <Box sx={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
            {/* Header with Breadcrumbs and Last Updated */}
            <Box sx={{
                p: 3,
                borderBottom: 1,
                borderColor: 'divider',
                backgroundColor: 'background.paper'
            }}>
                <Box sx={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center'
                }}>
                    {/* Breadcrumbs */}
                    <Breadcrumbs
                        aria-label="breadcrumb"
                        separator={<NavigateNextIcon fontSize="small" />}
                        sx={{ flexGrow: 1 }}
                    >
                        <Link
                            underline="hover"
                            color="inherit"
                            href="/"
                            onClick={handleProjectsClick}
                            sx={{
                                display: 'flex',
                                alignItems: 'center',
                                cursor: 'pointer'
                            }}
                        >
                            Home
                        </Link>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            <Typography
                                color="text.primary"
                                sx={{
                                    fontWeight: 'medium',
                                    maxWidth: '300px',
                                    overflow: 'hidden',
                                    textOverflow: 'ellipsis',
                                    whiteSpace: 'nowrap'
                                }}
                            >
                                {currentProject.name}
                            </Typography>
                            {currentProject.description && (
                                <Tooltip
                                    title={currentProject.description}
                                    arrow
                                    placement="bottom-start"
                                >
                                    <InfoIcon
                                        fontSize="small"
                                        sx={{
                                            color: 'text.secondary',
                                            cursor: 'help',
                                            ml: 0.5
                                        }}
                                    />
                                </Tooltip>
                            )}
                        </Box>
                    </Breadcrumbs>

                    {/* Last Updated */}
                    <Box sx={{ textAlign: 'right', ml: 2 }}>
                        <Typography variant="body2" color="text.secondary">
                            Last Updated
                        </Typography>
                        <Typography variant="body2" fontWeight="medium">
                            {formatDate(currentProject.updated_at)}
                        </Typography>
                    </Box>
                </Box>

                {/* Project Description (if available) */}
                {/* {currentProject.description && (
                    <Typography
                        variant="body2"
                        color="text.secondary"
                        sx={{ mt: 1, maxWidth: '600px' }}
                    >
                        {currentProject.description}
                    </Typography>
                )} */}
            </Box>

            {/* Main Content Area */}
            <Box sx={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
                {/* Vertical Tabs Sidebar */}
                <Paper
                    elevation={0}
                    sx={{
                        width: 200,
                        borderRight: 1,
                        borderColor: 'divider',
                        borderRadius: 0,
                    }}
                >
                    <Tabs
                        orientation="vertical"
                        variant="scrollable"
                        value={activeTab}
                        onChange={handleTabChange}
                        sx={{
                            '& .MuiTabs-indicator': {
                                left: 0,
                                width: 3,
                            },
                        }}
                    >
                        {PROJECT_TABS.map((tab) => (
                            <Tab
                                key={tab.id}
                                value={tab.id}
                                icon={tab.icon}
                                iconPosition="start"
                                label={
                                    <Box sx={{ textAlign: 'left', }}>
                                        <Typography variant="body2" fontWeight="medium">
                                            {tab.label}
                                        </Typography>
                                    </Box>
                                }
                                sx={{
                                    minHeight: 64,
                                    alignItems: 'center', // Changed from 'flex-start' to 'center'
                                    justifyContent: 'flex-start',
                                    textAlign: 'left',
                                    px: 2,
                                    paddingLeft: 2,
                                    paddingRight: 0,
                                    py: 1.5,
                                    '&.Mui-selected': {
                                        backgroundColor: 'action.selected',
                                    },
                                    '& .MuiTab-iconWrapper': {
                                        marginBottom: 0,
                                        marginRight: 1.5,
                                        marginTop: 0, // Changed from 0.5 to 0 for perfect center alignment
                                    }
                                }}
                            />
                        ))}
                    </Tabs>
                </Paper>

                {/* Tab Content Area */}
                <Box sx={{
                    flex: 1,
                    p: 3,
                    overflow: 'auto',
                    backgroundColor: 'background.default'
                }}>
                    {/* Tab Content Placeholder */}
                    {activeTab === 'sources' && (
                        <Box>
                            <Typography variant="h5" gutterBottom fontWeight="bold">
                                Sources
                            </Typography>
                            <Typography variant="body1" color="text.secondary" paragraph>
                                Upload your mining reports and documents for AI-powered cost estimation and scenario analysis.
                                Supported formats include PDF, CSV, XLSX, and TXT.
                            </Typography>

                            <Paper sx={{
                                p: 4,
                                textAlign: 'center',
                                border: '2px dashed',
                                borderColor: 'divider',
                                backgroundColor: 'background.paper'
                            }}>
                                <FolderIcon sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
                                <Typography variant="h6" gutterBottom>
                                    Upload your mining report and other documents
                                </Typography>
                                <Typography variant="body2" color="text.secondary" sx={{ mb: 3, maxWidth: 400, mx: 'auto' }}>
                                    Upload your mining reports and documents for AI-powered cost estimation and scenario analysis.
                                    Ensure data accuracy for optimal results, focusing on key metrics like ore grade, extraction rates, and operational costs.
                                </Typography>
                                {/* Placeholder for upload component */}
                                <Typography variant="body2" color="primary" sx={{ fontStyle: 'italic' }}>
                                    [File Upload Component - To be implemented]
                                </Typography>
                            </Paper>
                        </Box>
                    )}

                    {activeTab === 'base-case' && (
                        <Box>
                            <Typography variant="h5" gutterBottom fontWeight="bold">
                                Base Case
                            </Typography>
                            <Typography variant="body1" color="text.secondary" paragraph>
                                Review and validate data extracted from your uploaded documents.
                                This forms the foundation for your cost analysis and scenario modeling.
                            </Typography>
                            <Paper sx={{ p: 3 }}>
                                <Typography variant="body2" color="text.secondary" sx={{ fontStyle: 'italic' }}>
                                    [Base Case View - To be implemented]
                                </Typography>
                            </Paper>
                        </Box>
                    )}

                    {activeTab === 'scenarios' && (
                        <Box>
                            <Typography variant="h5" gutterBottom fontWeight="bold">
                                Scenarios
                            </Typography>
                            <Typography variant="body1" color="text.secondary" paragraph>
                                Create and manage different scenarios by applying deltas to your base case.
                                Compare various operational parameters and their impact on costs.
                            </Typography>
                            <Paper sx={{ p: 3 }}>
                                <Typography variant="body2" color="text.secondary" sx={{ fontStyle: 'italic' }}>
                                    [Scenarios View - To be implemented]
                                </Typography>
                            </Paper>
                        </Box>
                    )}

                    {activeTab === 'analysis' && (
                        <Box>
                            <Typography variant="h5" gutterBottom fontWeight="bold">
                                Analysis
                            </Typography>
                            <Typography variant="body1" color="text.secondary" paragraph>
                                Compare scenarios and perform decision modeling.
                                Generate reports and visualizations to support your mining investment decisions.
                            </Typography>
                            <Paper sx={{ p: 3 }}>
                                <Typography variant="body2" color="text.secondary" sx={{ fontStyle: 'italic' }}>
                                    [Analysis View - To be implemented]
                                </Typography>
                            </Paper>
                        </Box>
                    )}
                </Box>
            </Box>
        </Box>
    );
};

export default ProjectDashboard;