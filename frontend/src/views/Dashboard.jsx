import React, { useCallback, useEffect, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import {
    Box,
    Typography,
    Button,
    useTheme,
    Chip,
    IconButton,
    CircularProgress,
    Menu,
    MenuItem,
    ListItemIcon,
    ListItemText
} from '@mui/material';
import {
    Add as AddIcon,
    MoreVert as MoreVertIcon,
    OpenInNew as OpenIcon,
    Delete as DeleteIcon,
} from '@mui/icons-material';
import DataTable from '../components/DataTable';
import { useDialogs } from '../hooks/useDialogs/useDialogs';
import {
    createProject,
    fetchProjects,
    deleteProject,
    selectProjects,
    selectProjectsLoading,
    selectProjectsError,
    clearError
} from '../redux/projectSlice';

const Dashboard = ({ onOpenProject }) => {
    const theme = useTheme();
    const dialogs = useDialogs();
    const dispatch = useDispatch();

    // Redux selectors
    const projects = useSelector(selectProjects);
    const loading = useSelector(selectProjectsLoading);
    const error = useSelector(selectProjectsError);

    // Context menu state
    const [contextMenu, setContextMenu] = useState(null);
    const [selectedProject, setSelectedProject] = useState(null);

    // Load projects on component mount
    useEffect(() => {
        dispatch(fetchProjects({ page: 1, limit: 10 }));
    }, [dispatch]);

    // Clear errors when component unmounts or changes
    useEffect(() => {
        return () => {
            if (error) {
                dispatch(clearError());
            }
        };
    }, [error, dispatch]);

    // Mock data - replace with actual data from your state/API
    const userName = "Sid";
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
        projectsCreated: projects.length || 7,
        scenariosCreated: 18
    };

    // Updated headers format - array of objects with key and display_value
    const projectHeaders = [
        { key: "name", display_value: "Project" },
        { key: "status", display_value: "Status" },
        { key: "created", display_value: "Created" },
        { key: "lastUpdated", display_value: "Updated" },
        { key: "estimateReports", display_value: "Estimate Reports" },
        { key: "options", display_value: "Options" }
    ];

    // Helper function for status colors
    const getStatusColor = useCallback((status) => {
        switch (status.toLowerCase()) {
            case 'active':
                return 'success';
            case 'needs review':
                return 'warning';
            case 'awaiting input':
                return 'info';
            case 'completed':
            case 'archived':
                return 'default';
            default:
                return 'default';
        }
    }, []);

    // Context menu handlers
    const handleOptionsClick = useCallback((event, project) => {
        event.preventDefault();
        event.stopPropagation();

        setSelectedProject(project);
        setContextMenu(
            contextMenu === null
                ? {
                    mouseX: event.clientX + 2,
                    mouseY: event.clientY - 6,
                }
                : null,
        );
    }, [contextMenu]);

    const handleContextMenuClose = useCallback(() => {
        setContextMenu(null);
        setSelectedProject(null);
    }, []);

    // Updated handleOpenProject to use callback prop instead of navigation
    const handleOpenProject = useCallback(() => {
        if (selectedProject && onOpenProject) {
            console.log('Opening project:', selectedProject);
            onOpenProject(selectedProject.project_id);
        }
        handleContextMenuClose();
    }, [selectedProject, onOpenProject, handleContextMenuClose]);

    const handleDeleteProject = useCallback(async () => {
        if (!selectedProject) return;

        try {
            // Show confirmation dialog
            const confirmed = await dialogs.confirm(
                `Are you sure you want to delete "${selectedProject.name}"?\n\nThis action cannot be undone.`,
                {
                    title: 'Delete Project',
                    severity: 'error',
                    okText: 'Delete',
                    cancelText: 'Cancel'
                }
            );

            if (confirmed) {
                // Dispatch delete action
                const resultAction = await dispatch(deleteProject({
                    projectId: selectedProject.project_id,
                    hardDelete: false // Use soft delete by default
                }));

                if (deleteProject.fulfilled.match(resultAction)) {
                    await dialogs.alert(
                        `Project "${selectedProject.name}" has been deleted successfully.`,
                        {
                            title: 'Project Deleted',
                            okText: 'OK'
                        }
                    );
                    console.log('Project deleted:', resultAction.payload);
                } else {
                    // Handle deletion error
                    const errorMessage = resultAction.payload || 'Failed to delete project';
                    await dialogs.alert(`Error deleting project: ${errorMessage}`, {
                        title: 'Error',
                        okText: 'OK'
                    });
                }
            }
        } catch (error) {
            console.error('Error in project deletion flow:', error);
            await dialogs.alert('An unexpected error occurred while deleting the project.', {
                title: 'Error',
                okText: 'OK'
            });
        }

        handleContextMenuClose();
    }, [selectedProject, dialogs, dispatch, handleContextMenuClose]);

    // Add this handleRowClick function
    const handleRowClick = useCallback((row, rowIndex) => {
        // Get the original project data from the projects array using the row index
        const project = projects[rowIndex];
        if (project && onOpenProject) {
            console.log('Opening project from row click:', project);
            onOpenProject(project.project_id);
        }
    }, [projects, onOpenProject]);

    // Convert Redux projects data to table format
    const formatProjectsForTable = (projects) => {
        return projects.map(project => ({
            name: project.name,
            status: <Chip
                label={project.status}
                color={getStatusColor(project.status)}
                size="small"
                variant="outlined"
            />,
            lastUpdated: new Date(project.updated_at).toLocaleDateString(),
            created: new Date(project.created_at).toLocaleDateString(),
            estimateReports: [
                "0 completed", "0 pending review"
            ],
            options: (
                <IconButton
                    size="small"
                    onClick={(event) => handleOptionsClick(event, project)}
                    disabled={loading.delete}
                >
                    <MoreVertIcon />
                </IconButton>
            )
        }));
    };

    const projectData = formatProjectsForTable(projects);

    const handleCreateProject = async () => {
        try {
            // Use the new projectPrompt method instead of regular prompt
            const projectData = await dialogs.projectPrompt(
                'Enter details for your new project:',
                {
                    title: 'Create New Project',
                    okText: 'Create Project',
                    cancelText: 'Cancel'
                }
            );

            if (projectData && projectData.name) {
                // Dispatch the createProject action with the collected data
                const resultAction = await dispatch(createProject({
                    name: projectData.name,
                    description: projectData.description || `New project: ${projectData.name}`,
                    project_type: 'mining',
                    status: 'active',
                    tags: ['new', 'mining'],
                    metadata: {
                        created_via: 'web_interface',
                        creation_date: new Date().toISOString(),
                        has_custom_description: !!projectData.description
                    }
                }));

                // Check if creation was successful
                if (createProject.fulfilled.match(resultAction)) {
                    // Use callback to open the newly created project
                    const newProject = resultAction.payload;
                    if (onOpenProject) {
                        onOpenProject(newProject.project_id);
                    }
                } else {
                    // Handle creation error
                    const errorMessage = resultAction.payload || 'Failed to create project';
                    await dialogs.alert(`Error creating project: ${errorMessage}`, {
                        title: 'Error',
                        okText: 'OK'
                    });
                }
            } else {
                console.log('Project creation cancelled or no name provided');
            }
        } catch (error) {
            console.error('Error in project creation flow:', error);
            await dialogs.alert('An unexpected error occurred while creating the project.', {
                title: 'Error',
                okText: 'OK'
            });
        }
    };

    // Show loading state
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
                    Loading projects...
                </Typography>
            </Box>
        );
    }

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

            {/* Error Display */}
            {error && (
                <Box sx={{ mb: 2 }}>
                    <Typography color="error" variant="body2">
                        Error: {error}
                    </Typography>
                </Box>
            )}

            {/* User Data Summary Section */}
            <Box sx={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
                gap: 3,
                mb: 4,
                p: 3,
                bgcolor: 'background.paper',
                borderRadius: 2,
                boxShadow: 1
            }}>
                <Box>
                    <Typography variant="subtitle2" color="text.secondary">
                        Last Modified
                    </Typography>
                    <Typography variant="body2" fontWeight="medium">
                        {userStats.lastModified}
                    </Typography>
                </Box>
                <Box>
                    <Typography variant="subtitle2" color="text.secondary">
                        Storage Used
                    </Typography>
                    <Typography variant="body1" fontWeight="medium">
                        {userStats.storageUsed}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                        {userStats.storageDetail}
                    </Typography>
                </Box>
                <Box>
                    <Typography variant="subtitle2" color="text.secondary">
                        Documents Ingested
                    </Typography>
                    <Typography variant="h6" color="primary">
                        {userStats.documentsIngested}
                    </Typography>
                </Box>
                <Box>
                    <Typography variant="subtitle2" color="text.secondary">
                        Projects Created
                    </Typography>
                    <Typography variant="h6" color="secondary">
                        {userStats.projectsCreated}
                    </Typography>
                </Box>
                <Box>
                    <Typography variant="subtitle2" color="text.secondary">
                        Scenarios Created
                    </Typography>
                    <Typography variant="h6" color="success.main">
                        {userStats.scenariosCreated}
                    </Typography>
                </Box>
            </Box>

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
                            {projects.length} projects
                        </Typography>
                        <Button
                            variant="contained"
                            startIcon={loading.create ? <CircularProgress size={20} /> : <AddIcon />}
                            sx={{ ml: 2 }}
                            onClick={handleCreateProject}
                            disabled={loading.create}
                        >
                            {loading.create ? 'Creating...' : 'New Project'}
                        </Button>
                    </Box>
                </Box>

                {projectData.length > 0 ? (
                    <>
                        <DataTable
                            headers={projectHeaders}
                            data={projectData}
                            onRowClick={handleRowClick}
                            containerSx={{ borderRadius: 2 }}
                        />

                        <Box sx={{ display: 'flex', justifyContent: 'flex-end', mt: 2 }}>
                            <Button variant="text" color="primary">
                                View All
                            </Button>
                        </Box>
                    </>
                ) : (
                    <Box sx={{
                        textAlign: 'center',
                        py: 6,
                        border: '1px dashed',
                        borderColor: 'divider',
                        borderRadius: 2
                    }}>
                        <Typography variant="h6" color="text.secondary" gutterBottom>
                            No projects yet
                        </Typography>
                        <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                            Create your first project to get started
                        </Typography>
                        <Button
                            variant="contained"
                            startIcon={<AddIcon />}
                            onClick={handleCreateProject}
                            disabled={loading.create}
                        >
                            Create First Project
                        </Button>
                    </Box>
                )}
            </Box>

            {/* Context Menu */}
            <Menu
                open={contextMenu !== null}
                onClose={handleContextMenuClose}
                anchorReference="anchorPosition"
                anchorPosition={
                    contextMenu !== null
                        ? { top: contextMenu.mouseY, left: contextMenu.mouseX }
                        : undefined
                }
                slotProps={{
                    paper: {
                        sx: {
                            minWidth: 120,
                        },
                    },
                }}
            >
                <MenuItem
                    onClick={handleOpenProject}
                    disabled={!selectedProject}
                >
                    <ListItemIcon>
                        <OpenIcon fontSize="small" />
                    </ListItemIcon>
                    <ListItemText>Open</ListItemText>
                </MenuItem>

                <MenuItem
                    onClick={handleDeleteProject}
                    disabled={!selectedProject || loading.delete}
                    sx={{
                        color: 'error.main',
                        '&:hover': {
                            backgroundColor: 'error.light',
                            color: 'error.contrastText',
                        },
                    }}
                >
                    <ListItemIcon>
                        <DeleteIcon fontSize="small" sx={{ color: 'inherit' }} />
                    </ListItemIcon>
                    <ListItemText>
                        {loading.delete ? 'Deleting...' : 'Delete'}
                    </ListItemText>
                </MenuItem>
            </Menu>
        </Box>
    );
};

export default Dashboard;