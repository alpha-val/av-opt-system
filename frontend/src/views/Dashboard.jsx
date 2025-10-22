import React, { useCallback, useEffect, useState, useMemo } from "react";
import { useDispatch, useSelector } from "react-redux";
import {
  Box,
  Typography,
  Button,
  Chip,
  IconButton,
  CircularProgress,
  Menu,
  MenuItem,
  ListItemIcon,
  ListItemText,
} from "@mui/material";
import {
  Add as AddIcon,
  MoreVert as MoreVertIcon,
  OpenInNew as OpenIcon,
  Delete as DeleteIcon,
} from "@mui/icons-material";
import DataTable from "../components/DataTable";
import { useDialogs } from "../hooks/useDialogs/useDialogs";
import {
  createProject,
  fetchProjects,
  deleteProject,
  selectProjects,
  selectProjectsLoading,
  selectProjectsError,
  clearError,
} from "../redux/projectSlice";

const Dashboard = ({ onOpenProject }) => {
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

  // Calculate user stats
  const userStats = useMemo(() => {
    if (!projects || projects.length === 0) {
      return {
        lastModified: "No projects yet",
        storageUsed: "0%",
        storageDetail: "(0 MB of 5 GB)",
        documentsIngested: 0,
        projectsCreated: 0,
        scenariosCreated: 0,
        baseCaseDocuments: 0,
        activeProjects: 0,
        projectsWithData: 0,
      };
    }

    const totals = projects.reduce(
      (acc, project) => {
        const stats = project.metadata?.stats || {};
        return {
          documents: acc.documents + (stats.number_of_documents || 0),
          baseCaseDocuments:
            acc.baseCaseDocuments + (project.base_case_documents || 0),
          scenarioDocuments:
            acc.scenarioDocuments + (project.tabular_documents || 0),
          scenariosCreated:
            acc.scenariosCreated + (stats.number_of_scenarios || 0),
          document_size: acc.document_size + (stats.total_document_size || 0),
        };
      },
      {
        documents: 0,
        baseCaseDocuments: 0,
        scenarioDocuments: 0,
        scenariosCreated: 0,
        document_size: 0,
      }
    );

    const lastModifiedProject = projects.reduce((latest, project) => {
      const projectDate = new Date(project.updated_at);
      const latestDate = latest ? new Date(latest.updated_at) : new Date(0);
      return projectDate > latestDate ? project : latest;
    }, null);

    const lastModified = lastModifiedProject
      ? new Date(lastModifiedProject.updated_at).toLocaleDateString("en-US", {
          year: "numeric",
          month: "short",
          day: "2-digit",
          hour: "2-digit",
          minute: "2-digit",
          timeZoneName: "short",
        })
      : "No projects yet";

    const estimatedStorageMB = (totals.document_size || 0) / (1024 * 1024); // Convert bytes to MB
    const storagePercentage = Math.min((estimatedStorageMB / 5120) * 100, 100); // Out of 5GB

    return {
      lastModified,
      storageUsed: `${storagePercentage.toFixed(2)}%`,
      storageDetail: `(${estimatedStorageMB.toFixed(2)} MB of 5 GB)`,
      documentsIngested: totals.documents,
      projectsCreated: projects.length,
      scenariosCreated: totals.scenarioDocuments,
      baseCaseDocuments: totals.baseCaseDocuments,
      activeProjects: projects.filter((p) => p.status === "active").length,
      projectsWithData: projects.filter((p) => p.has_data).length,
    };
  }, [projects]);

  // Format projects for the table
  const projectData = useMemo(() => {
    return projects.map((project) => ({
      name: project.name,
      status: (
        <Chip
          label={project.status}
          color={project.status === "active" ? "success" : "default"}
          size="small"
          variant="outlined"
        />
      ),
      lastUpdated: new Date(project.updated_at).toLocaleDateString(),
      created: new Date(project.created_at).toLocaleDateString(),
      options: (
        <IconButton
          size="small"
          onClick={(event) => handleOptionsClick(event, project)}
          disabled={loading.delete}
        >
          <MoreVertIcon />
        </IconButton>
      ),
    }));
  }, [projects, loading.delete]);

  // Handle create project
  const handleCreateProject = useCallback(async () => {
    try {
      const projectData = await dialogs.projectPrompt("Create New Project");
      console.log("Project name received from dialog:", projectData);
      if (projectData) {
        const resultAction = await dispatch(
          createProject(projectData) // Send projectData directly
        );
        if (createProject.fulfilled.match(resultAction)) {
          const newProjectId = resultAction.payload.id;
          if (onOpenProject) {
            onOpenProject(newProjectId);
          }
        } else {
          const errorMessage =
            resultAction.payload || "Failed to create project";
          await dialogs.alert(`Error creating project: ${errorMessage}`, {
            title: "Error",
            okText: "OK",
          });
        }
      }
    } catch (error) {
      console.error("Unexpected error during project creation:", error);
      await dialogs.alert(
        "An unexpected error occurred while creating the project.",
        {
          title: "Error",
          okText: "OK",
        }
      );
    }
  }, [dispatch, dialogs, onOpenProject]);

  // Context menu handlers
  const handleOptionsClick = useCallback((event, project) => {
    event.preventDefault();
    setSelectedProject(project);
    setContextMenu({
      mouseX: event.clientX + 2,
      mouseY: event.clientY - 6,
    });
  }, []);

  const handleContextMenuClose = useCallback(() => {
    setContextMenu(null);
    setSelectedProject(null);
  }, []);

  const handleOpenProject = useCallback(() => {
    if (selectedProject && onOpenProject) {
      onOpenProject(selectedProject.id);
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
          title: "Delete Project",
          severity: "error",
          okText: "Delete",
          cancelText: "Cancel",
        }
      );

      if (confirmed) {
        // Dispatch delete action
        const resultAction = await dispatch(
          deleteProject({
            projectId: selectedProject.id,
            hardDelete: false, // Use soft delete by default
          })
        );

        if (deleteProject.fulfilled.match(resultAction)) {
          // await dialogs.alert(
          //   `Project "${selectedProject.name}" has been deleted successfully.`,
          //   {
          //     title: "Project Deleted",
          //     okText: "OK",
          //   }
          // );
          // console.log("Project deleted:", resultAction.payload);
        } else {
          // Handle deletion error
          const errorMessage =
            resultAction.payload || "Failed to delete project";
          await dialogs.alert(`Error deleting project: ${errorMessage}`, {
            title: "Error",
            okText: "OK",
          });
        }
      }
    } catch (error) {
      console.error("Error in project deletion flow:", error);
      await dialogs.alert(
        "An unexpected error occurred while deleting the project.",
        {
          title: "Error",
          okText: "OK",
        }
      );
    }

    handleContextMenuClose();
  }, [selectedProject, dialogs, dispatch, handleContextMenuClose]);

  // Add this handleRowClick function
  const handleRowClick = useCallback(
    (row, rowIndex) => {
      // Get the original project data from the projects array using the row index
      const project = projects[rowIndex];
      if (project && onOpenProject) {
        onOpenProject(project.id);
      }
    },
    [projects, onOpenProject]
  );

  // Show loading state
  if (loading.fetch) {
    return (
      <Box
        sx={{
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          minHeight: "50vh",
        }}
      >
        <CircularProgress />
        <Typography variant="body1" sx={{ ml: 2 }}>
          Loading projects...
        </Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3, maxWidth: "100%", width: "100%" }}>
      {/* Header Section */}
      <Box
        sx={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          mb: 4,
          borderBottom: 1,
          borderColor: "divider",
          pb: 2,
        }}
      >
        <Typography variant="h4" fontWeight="bold">
          Welcome, User
        </Typography>
        <Typography variant="body2" color="text.secondary">
          {new Date().toLocaleDateString("en-US", {
            year: "numeric",
            month: "short",
            day: "2-digit",
            hour: "2-digit",
            minute: "2-digit",
            timeZoneName: "short",
          })}
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

      {/* User Stats */}
      <Box
        sx={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
          gap: 3,
          mb: 4,
          p: 3,
          bgcolor: "background.paper",
          borderRadius: 2,
          boxShadow: 1,
        }}
      >
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
            Projects Created
          </Typography>
          <Typography variant="h6" color="secondary">
            {userStats.projectsCreated}
          </Typography>
        </Box>
        <Box>
          <Typography variant="subtitle2" color="text.secondary">
            Total Documents Ingested
          </Typography>
          <Typography variant="h6" color="secondary">
            {userStats.documentsIngested}
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
      </Box>

      {/* Projects Table */}
      <Box>
        <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <Typography variant="h5" fontWeight="bold" sx={{ mb: 3 }}>
          Your Projects
        </Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={handleCreateProject}
          size="small"
          sx={{ mb: 2 }}
        >
          Create New Project
        </Button>
        </Box>
        {projectData.length > 0 ? (
          <DataTable
            headers={[
              { key: "name", display_value: "Project" },
              { key: "status", display_value: "Status" },
              { key: "created", display_value: "Created" },
              { key: "lastUpdated", display_value: "Updated" },
              { key: "options", display_value: "Options" },
            ]}
            data={projectData}
            onRowClick={(row, rowIndex) => {
              const project = projects[rowIndex];
              if (project && onOpenProject) {
                onOpenProject(project.id);
              }
            }}
            containerSx={{ borderRadius: 2 }}
          />
        ) : (
          <Box
            sx={{
              textAlign: "center",
              py: 6,
              border: "1px dashed",
              borderColor: "divider",
              borderRadius: 2,
            }}
          >
            <Typography variant="h6" color="text.secondary" gutterBottom>
              No projects yet
            </Typography>
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={handleCreateProject}
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
        <MenuItem onClick={handleOpenProject} disabled={!selectedProject}>
          <ListItemIcon>
            <OpenIcon fontSize="small" />
          </ListItemIcon>
          <ListItemText>Open</ListItemText>
        </MenuItem>

        <MenuItem
          onClick={handleDeleteProject}
          disabled={!selectedProject || loading.delete}
          sx={{
            color: "error.main",
            "&:hover": {
              backgroundColor: "error.light",
              color: "error.contrastText",
            },
          }}
        >
          <ListItemIcon>
            <DeleteIcon fontSize="small" sx={{ color: "inherit" }} />
          </ListItemIcon>
          <ListItemText>
            {loading.delete ? "Deleting..." : "Delete"}
          </ListItemText>
        </MenuItem>
      </Menu>
    </Box>
  );
};

export default Dashboard;
