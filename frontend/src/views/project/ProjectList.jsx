import React, { useEffect, useMemo } from "react";
import { useDispatch, useSelector } from "react-redux";
import { Box, Paper, CircularProgress, Alert, Button } from "@mui/material";
import {
  createProject,
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

  // Select data from Redux store
  const projects = useSelector(selectProjects);
  const loading = useSelector(selectLoading);
  const error = useSelector(selectError);

  // Convert date strings to human-readable format
  const formatDate = (dateString) => {
    const options = {
      year: "numeric",
      month: "long",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    };
    return new Date(dateString).toLocaleDateString(undefined, options);
  };

  // Memoize the project list to prevent unnecessary re-renders
  const memoizedProjects = useMemo(() => {
    // Convert datestrings to Date objects for proper sorting/display if needed
    return (
      projects.map((project) => ({
        ...project,
        created_at_display: formatDate(project.created_at),
        updated_at_display: formatDate(project.updated_at),
      })) || []
    );
  }, [projects]);

  // Fetch projects on component mount
  useEffect(() => {
    dispatch(fetchProjects());
  }, [dispatch]);

  // Handler for creating a new project (placeholder)
  const handleCreateNewProject = async () => {
    // Logic to open a modal or navigate to project creation page
    console.log("Create New Project clicked");
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
      console.log("Project creation cancelled or no data provided.");
    }
  };

  // Show loading state
  if (loading) {
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
              size="small"
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
            headers={[
              { key: "name", display_value: "Name" },
              { key: "description", display_value: "Description" },
              { key: "created_at_display", display_value: "Created" },
              { key: "updated_at_display", display_value: "Updated" },
              { key: "tags", display_value: "Tags" },
            ]}
            data={memoizedProjects}
          />
        </Box>
      </Paper>
    </Box>
  );
};

export default ProjectList;
