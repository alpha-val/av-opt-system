import React, { useEffect, useMemo, useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { useDispatch, useSelector } from "react-redux";
import {
  Box,
  Paper,
  CircularProgress,
  Alert,
  Button,
  Menu,
  MenuItem,
  ListItemIcon,
  ListItemText,
  IconButton,
} from "@mui/material";
import MoreVertIcon from "@mui/icons-material/MoreVert";
import DeleteIcon from "@mui/icons-material/Delete";
import OpenIcon from "@mui/icons-material/FolderOpen";

import {
  createProject,
  deleteProject,
  fetchProjects,
  selectProjects,
  selectLoading,
  selectError,
} from "../../redux/projectSlice";
import { useDialogs } from "../../hooks/useDialogs/useDialogs";
import DataTable from "../../components/DataTable";

const ProjectList = () => {
  const dialogs = useDialogs();
  const dispatch = useDispatch();
  const navigate = useNavigate();

  // Select data from Redux store
  const projects = useSelector(selectProjects);
  const loading = useSelector(selectLoading);
  const error = useSelector(selectError);

  // Context menu state
  const [contextMenu, setContextMenu] = useState(null);
  const [selectedProject, setSelectedProject] = useState(null);

  // Convert date strings to human-readable format in local timezone
  const formatDate = (dateString) => {
    if (!dateString) return "N/A";
    const date = new Date(dateString);

    const options = {
      year: "numeric",
      month: "long",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
      timeZoneName: "short", // Shows timezone abbreviation
    };

    // Use toLocaleString instead of toLocaleDateString to include time
    return date.toLocaleString("en-US", options);
  };
  
  // Memoize the project list to prevent unnecessary re-renders
  const OptionCell = React.memo(({ project, onClick, disabled }) => (
    <IconButton
      size="small"
      onClick={(e) => onClick(e, project)}
      disabled={disabled}
    >
      <MoreVertIcon />
    </IconButton>
  ));

  // Fetch projects on component mount
  useEffect(() => {
    dispatch(fetchProjects());
  }, [dispatch]);

  // Handler for creating a new project (placeholder)
  const handleCreateNewProject = async () => {
    // Logic to open a modal or navigate to project creation page

    const projectData = await dialogs.projectPrompt("Create New Project");
    if (projectData) {
      console.log("Project data received:", projectData);
      // Dispatch action to create project (not implemented here)
      const result = await dispatch(createProject(projectData));
      if (createProject.fulfilled.match(result)) {
        console.log("Project created successfully:", result.payload);
      } else {
        console.error("Failed to create project:", result.payload);
      }
    } else {
      // console.log("Project creation cancelled or no data provided.");
    }
  };

  // Update handleOpenProject to accept a project parameter for row clicks
  const handleOpenProject = useCallback(
    (project = null) => {
      console.log(
        "Opening project:",
        project,
        " or selectedProject:",
        selectedProject
      );
      // Use the provided project parameter or fall back to selectedProject for context menu
      const projectToOpen = project || selectedProject;

      if (projectToOpen) {
        navigate(`/project/${projectToOpen.id}`);
        // Only close context menu if it was opened from context menu
        if (selectedProject) {
          handleContextMenuClose();
        }
      }
    },
    [selectedProject, navigate, handleContextMenuClose]
  );

  // Context menu handlers
  const handleOptionsClick = useCallback((event, project) => {
    event.preventDefault();
    setSelectedProject(project);
    setContextMenu({ mouseX: event.clientX + 2, mouseY: event.clientY - 6 });
  }, []);

  const handleContextMenuClose = useCallback(() => {
    setContextMenu(null);
    setSelectedProject(null);
  }, []);

  const handleDeleteProject = useCallback(async () => {
    const projectToDelete = selectedProject;

    handleContextMenuClose();
    // Add a small delay to allow the menu to fully close and focus to be released
    await new Promise((resolve) => setTimeout(resolve, 200));
    if (!projectToDelete) return;
    const confirm = await dialogs.confirm(
      "Delete Project",
      `Are you sure you want to delete the project "${projectToDelete?.name}"? This action cannot be undone.`
    );
    if (!confirm) {
      return;
    }
    if (selectedProject) {
      console.log("Delete project with ID:", selectedProject.id);
      // dispatch delete...
      const result = await dispatch(deleteProject(selectedProject.id));
      console.log("Delete dispatch result:", result);
      if (deleteProject.fulfilled.match(result)) {
        console.log("Project deleted successfully:", result.payload);
      } else {
        console.error("Failed to delete project:", result.payload);
      }
    }
  }, [selectedProject, handleContextMenuClose, dispatch, dialogs]);

  const memoizedProjects = useMemo(() => {
    return (projects || []).map((project) => ({
      ...project,
      created_at_display: formatDate(project.created_at),
      updated_at_display: formatDate(project.updated_at),
      options: (
        <OptionCell
          project={project}
          onClick={handleOptionsClick}
          disabled={!!loading?.delete}
        />
      ),
    }));
    // include everything referenced inside: projects, loading.delete, handleOptionsClick
  }, [projects, loading?.delete, handleOptionsClick]);

  const headers = useMemo(
    () => [
      { key: "name", display_value: "Name" },
      { key: "description", display_value: "Description" },
      { key: "created_at_display", display_value: "Created" },
      { key: "updated_at_display", display_value: "Updated" },
      { key: "tags", display_value: "Tags" },
      { key: "options", display_value: "Options" },
    ],
    []
  );

  // Show loading state
  if (loading.fetch) {
    return (
      <Box
        sx={{
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          height: "200px",
        }}
      >
        <CircularProgress />
      </Box>
    );
  }

  // Show error state
  if (error) {
    return (
      <Box sx={{ display: "flex", width: "100%" }}>
        <Paper elevation={1} sx={{ p: 2, width: "100%" }}>
          <Alert severity="error">Error loading projects: {error}</Alert>
        </Paper>
      </Box>
    );
  }
  console.log("Rendering ProjectList with projects:", memoizedProjects);
  return (
    <Box sx={{ display: "flex", width: "100%" }}>
      {/* Project content */}
      <Paper elevation={1} sx={{ p: 2, width: "100%" }}>
        <Box>
          <h2>Project List</h2>
        </Box>
        <Box
          sx={{
            display: "flex",
            flexDirection: "row",
            justifyContent: "space-between",
            alignItems: "center",
          }}
        >
          <Box>
            <p>Found {memoizedProjects.length} projects</p>

            {/* Placeholder for project list content - will be updated later */}
            {memoizedProjects.length === 0 ? (
              <p>
                No projects found. Create your first project to get started.
              </p>
            ) : null}
          </Box>
          <Box>
            <Button
              variant="contained"
              size="normal"
              color="primary"
              sx={{ float: "right" }}
              onClick={() => {
                handleCreateNewProject();
              }}
            >
              Create New Project
            </Button>
          </Box>
        </Box>
        <Box sx={{ mt: 1, textAlign: "right" }}>
          <DataTable
            headers={headers}
            data={memoizedProjects}
            onRowClick={handleOpenProject}
          />
        </Box>
      </Paper>
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
          disabled={loading.delete}
          sx={{
            color: "error.main",
            "&:hover": {
              backgroundColor: "error.veryLight",
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

export default ProjectList;
