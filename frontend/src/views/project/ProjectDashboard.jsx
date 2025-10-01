import React, { useState, useEffect, useMemo, useCallback } from 'react';
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
    Button,
    Chip,
} from '@mui/material';
import {
    NavigateNext as NavigateNextIcon,
    ArrowBack as ArrowBackIcon,
    Folder as FolderIcon,
    Dashboard as DashboardIcon,
    DynamicFeed as ScenariosIcon,
    Analytics as AnalysisIcon,
    Info as InfoIcon,
} from '@mui/icons-material';
import {
    fetchProjectSmart, // Use the smart fetch instead
    selectProjectById,
    selectHasCachedProject,
    selectIsProjectDataStale,
    selectProjectsLoading,
    selectProjectsError,
    clearProjectCache,
} from '../../redux/projectSlice';
import Sources from "./Sources";
import BaseCaseView from './BaseCaseView';

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

    // Use memoized selectors
    const currentProject = useSelector(state => selectProjectById(state, projectId));
    const hasCachedData = useSelector(state => selectHasCachedProject(state, projectId));
    const isDataStale = useSelector(state => selectIsProjectDataStale(state, projectId));
    const loading = useSelector(selectProjectsLoading);
    const error = useSelector(selectProjectsError);

    // Local state
    const [activeTab, setActiveTab] = useState('sources');

    // Memoized function to load project data
    const loadProjectData = useCallback(() => {
        if (projectId) {
            // console.log('Loading project data:', {
            //     projectId,
            //     hasCached: hasCachedData,
            //     isStale: isDataStale
            // });

            dispatch(fetchProjectSmart({
                projectId,
                forceRefresh: false
            }));
        }
    }, [dispatch, projectId, hasCachedData, isDataStale]);

    // Load project data when component mounts or projectId changes
    useEffect(() => {
        loadProjectData();
    }, [loadProjectData]);

    // Force refresh function
    const forceRefresh = useCallback(() => {
        if (projectId) {
            console.log('Force refreshing project data');
            dispatch(fetchProjectSmart({
                projectId,
                forceRefresh: true
            }));
        }
    }, [dispatch, projectId]);

    // Clear cache function
    const clearCache = useCallback(() => {
        if (projectId) {
            dispatch(clearProjectCache(projectId));
            dispatch(fetchProjectSmart({ projectId, forceRefresh: true }));
        }
    }, [dispatch, projectId]);

    // Handle tab change with memoization
    const handleTabChange = useCallback((event, newValue) => {
        setActiveTab(newValue);
    }, []);

    // Handle breadcrumb navigation
    const handleProjectsClick = useCallback((event) => {
        event.preventDefault();
        navigate('/');
    }, [navigate]);

    // Memoized date formatting
    const formattedDate = useMemo(() => {
        if (!currentProject?.updated_at) return '';
        return new Date(currentProject.updated_at).toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
            timeZoneName: 'short'
        });
    }, [currentProject?.updated_at]);

    // Show cache status for debugging
    const cacheStatus = useMemo(() => {
        if (!projectId) return 'No project ID';
        if (!hasCachedData) return 'No cache';
        if (isDataStale) return 'Cache stale';
        return 'Cache fresh';
    }, [projectId, hasCachedData, isDataStale]);

    // Loading state - only show if we don't have any cached data
    if (loading.fetch && !currentProject) {
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
                <Alert severity="error" action={
                    <Button color="inherit" size="small" onClick={forceRefresh}>
                        Retry
                    </Button>
                }>
                    {error}
                </Alert>
            </Box>
        );
    }

    // Project not found
    if (!currentProject) {
        return (
            <Box sx={{ p: 3 }}>
                <Alert severity="warning" action={
                    <Button color="inherit" size="small" onClick={forceRefresh}>
                        Refresh
                    </Button>
                }>
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

                            {/* Cache status indicator (for debugging - remove in production) */}
                            {/* <Tooltip title={`Cache status: ${cacheStatus}`}>
                                <Chip
                                    size="small"
                                    label={cacheStatus}
                                    color={hasCachedData && !isDataStale ? 'success' : 'default'}
                                    sx={{ ml: 1, fontSize: '0.7rem' }}
                                />
                            </Tooltip> */}
                        </Box>
                    </Breadcrumbs>

                    {/* Last Updated and Cache Controls */}
                    <Box sx={{ textAlign: 'right', ml: 2 }}>
                        {/* <Box sx={{ display: 'flex', gap: 1, mb: 1 }}>
                            <Button
                                size="small"
                                variant="outlined"
                                onClick={forceRefresh}
                                disabled={loading.fetch}
                            >
                                Refresh
                            </Button>
                            <Button
                                size="small"
                                variant="text"
                                onClick={clearCache}
                            >
                                Clear Cache
                            </Button>
                        </Box> */}
                        <Typography variant="body2" color="text.secondary">
                            Last Updated
                        </Typography>
                        <Typography variant="body2" fontWeight="medium">
                            {formattedDate}
                        </Typography>
                    </Box>
                </Box>
            </Box>

            {/* Show loading indicator when refreshing but we have cached data */}
            {loading.fetch && currentProject && (
                <Box sx={{
                    position: 'fixed',
                    top: 0,
                    left: 0,
                    right: 0,
                    zIndex: 1000,
                    backgroundColor: 'primary.main',
                    color: 'white',
                    textAlign: 'center',
                    py: 0.5
                }}>
                    <Typography variant="caption">
                        Refreshing project data...
                    </Typography>
                </Box>
            )}

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
                                    minHeight: 50,
                                    alignItems: 'center',
                                    justifyContent: 'flex-start',
                                    textAlign: 'left',
                                    px: 2,
                                    paddingLeft: 2,
                                    paddingRight: 0,
                                    py: 2,
                                    '&.Mui-selected': {
                                        backgroundColor: 'action.selected',
                                    },
                                    '& .MuiTab-iconWrapper': {
                                        marginBottom: 0,
                                        marginRight: 1.5,
                                        marginTop: 0,
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
                    {/* Tab Content */}
                    {activeTab === 'sources' && <Sources />}

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
                                <BaseCaseView />
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