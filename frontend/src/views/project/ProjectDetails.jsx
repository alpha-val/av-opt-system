import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useDispatch, useSelector } from "react-redux";
import {
  Box,
  Paper,
  Typography,
  Chip,
  Button,
  Grid,
  Divider,
  IconButton,
  Card,
  CardContent,
  Avatar,
  CircularProgress,
  Alert,
  Breadcrumbs,
  Link,
} from "@mui/material";
import {
  ArrowBack as ArrowBackIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Folder as FolderIcon,
  CalendarToday as CalendarIcon,
  Person as PersonIcon,
  Description as DescriptionIcon,
  Tag as TagIcon,
} from "@mui/icons-material";
import {
  fetchProjectById,
  selectCurrentProject,
  selectLoading,
  selectError,
  updateProject,
  deleteProject,
} from "../../redux/projectSlice";
import {
  selectDocumentsByProject,
  fetchDocumentsByProject,
} from "../../redux/documentSlice";
import { useDialogs } from "../../hooks/useDialogs/useDialogs";
import Header from "../../components/widgets/Header";

const ProjectDetails = () => {
  const { projectId } = useParams();
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const dialogs = useDialogs();

  // Redux state
  const project = useSelector(selectCurrentProject);
  const loading = useSelector(selectLoading);
  const error = useSelector(selectError);
  
  // Get documents for this project from Redux
  const projectDocuments = useSelector((state) =>
    selectDocumentsByProject(state, projectId)
  );
  
  // Calculate document count from Redux state
  const documentCount = projectDocuments.length;

  // Local state
  const [scenarioCount] = useState(0); // Placeholder - will be populated from API

  // Fetch project details on mount
  useEffect(() => {
    if (projectId) {
      dispatch(fetchProjectById(projectId));
      // Also fetch documents to get accurate document count
      dispatch(fetchDocumentsByProject(projectId));
    }
  }, [dispatch, projectId]);

  // Format date for display in local timezone
  const formatDate = (dateString) => {
    if (!dateString) return "N/A";
    const date = new Date(dateString);

    const options = {
      year: "numeric",
      month: "long",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
      timeZoneName: "short", // Shows timezone abbreviation (e.g., EST, PST)
    };

    // Use toLocaleString instead of toLocaleDateString to include time
    return date.toLocaleString("en-US", options);
  };

  // Parse tags (handle both string and array formats)
  const parseTags = (tags) => {
    if (!tags) return [];

    // If tags is already an array, return it (filtered for empty strings)
    if (Array.isArray(tags)) {
      return tags.filter((tag) => tag && tag.trim());
    }

    // If tags is a string, split it by comma
    if (typeof tags === "string") {
      return tags
        .split(",")
        .map((tag) => tag.trim())
        .filter((tag) => tag);
    }

    // If tags is neither string nor array, return empty array
    return [];
  };

  // Handle navigation back to home/dashboard
  const handleBack = () => {
    navigate("/");
  };

  // Handle edit project
  const handleEdit = async () => {
    if (!project) return;

    const updatedData = await dialogs.projectPrompt("Edit Project", {
      initialData: {
        id: project.id,
        name: project.name,
        description: project.description,
        tags: project.tags, // Can be array or string
      },
    });

    if (updatedData) {
      const result = await dispatch(
        updateProject({ projectId: project.id, projectData: updatedData })
      );
      // Handle result
    }
  };

  // Handle delete project
  const handleDelete = async () => {
    if (!project) return;

    const confirm = await dialogs.confirm(
      "Delete Project",
      `Are you sure you want to delete "${project.name}"? This action cannot be undone.`
    );

    if (confirm) {
      console.log("Delete project:", project.id);
      // Dispatch delete action and navigate back
      navigate("/");
    }
  };

  // Show loading state
  if (loading.fetchById) {
    return (
      <Box
        sx={{
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          height: "400px",
        }}
      >
        <CircularProgress />
      </Box>
    );
  }

  // Show error state
  if (error) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error" sx={{ mb: 2 }}>
          Error loading project: {error}
        </Alert>
        <Button
          variant="outlined"
          onClick={handleBack}
          startIcon={<ArrowBackIcon />}
        >
          Back to Dashboard
        </Button>
      </Box>
    );
  }

  // Show not found state
  if (!project) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="warning" sx={{ mb: 2 }}>
          Project not found
        </Alert>
        <Button
          variant="outlined"
          onClick={handleBack}
          startIcon={<ArrowBackIcon />}
        >
          Back to Dashboard
        </Button>
      </Box>
    );
  }

  const tags = parseTags(project.tags);

  return (
    <Box sx={{ p: 3 }}>
      <Grid container spacing={3} sx={{ alignItems: "stretch" }}>
        {/* Project Header */}
        <Grid size={{ xs: 12, md: 6 }} sx={{ display: "flex" }}>
          <Paper
            elevation={1}
            sx={{
              p: 3,
              mb: 2,
              width: "100%",
              display: "flex",
              flexDirection: "column",
            }}
          >
            <Box
              sx={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "flex-start",
                flex: 1,
              }}
            >
              <Box sx={{ flex: 1 }}>
                <Typography variant="h4" fontWeight="bold" gutterBottom>
                  {project.name}
                </Typography>
                {project.description && (
                  <Typography
                    variant="body1"
                    color="text.secondary"
                    sx={{ mb: 2 }}
                  >
                    {project.description}
                  </Typography>
                )}

                {/* Tags */}
                {tags.length > 0 && (
                  <Box
                    sx={{ display: "flex", flexWrap: "wrap", gap: 1, mb: 2 }}
                  >
                    {tags.map((tag, index) => (
                      <Chip
                        key={index}
                        label={tag}
                        size="small"
                        variant="outlined"
                        icon={<TagIcon />}
                      />
                    ))}
                  </Box>
                )}
                {/* Date updated */}
                <Box sx={{ mb: 0 }}>
                  <Typography variant="body2" color="text.secondary">
                    Last Updated
                  </Typography>
                  <Typography
                    variant="body1"
                    sx={{ display: "flex", alignItems: "center" }}
                  >
                    <CalendarIcon sx={{ mr: 1, fontSize: 16 }} />
                    {formatDate(project.updated_at)}
                  </Typography>
                </Box>
              </Box>

              {/* Action Buttons */}
              <Box sx={{ display: "flex", gap: 1 }}>
                <IconButton onClick={handleEdit} title="Edit Project">
                  <EditIcon />
                </IconButton>
                <IconButton
                  onClick={handleDelete}
                  title="Delete Project"
                  color="error"
                >
                  <DeleteIcon />
                </IconButton>
              </Box>
            </Box>
          </Paper>
        </Grid>
        {/* Project Statistics */}
        <Grid size={{ xs: 12, md: 6 }} sx={{ display: "flex" }}>
          <Paper
            elevation={1}
            sx={{
              p: 3,
              mb: 2,
              width: "100%",
              display: "flex",
              flexDirection: "column",
            }}
          >
            <Box
              sx={{
                flex: 1,
                display: "flex",
                flexDirection: "column",
              }}
            >
              <Typography
                variant="h6"
                gutterBottom
                sx={{ display: "flex", alignItems: "center" }}
              >
                <FolderIcon sx={{ mr: 1 }} />
                Project Content
              </Typography>

              <Grid container spacing={2} sx={{ flex: 1 }}>
                <Grid size={6}>
                  <Box sx={{ textAlign: "center", p: 2 }}>
                    <Avatar
                      sx={{
                        width: 48,
                        height: 48,
                        bgcolor: "primary.main",
                        mx: "auto",
                        mb: 1,
                      }}
                    >
                      <DescriptionIcon />
                    </Avatar>
                    <Typography variant="h4" fontWeight="bold">
                      {documentCount}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Documents
                    </Typography>
                  </Box>
                </Grid>
                <Grid size={6}>
                  <Box sx={{ textAlign: "center", p: 2 }}>
                    <Avatar
                      sx={{
                        width: 48,
                        height: 48,
                        bgcolor: "secondary.main",
                        mx: "auto",
                        mb: 1,
                      }}
                    >
                      <FolderIcon />
                    </Avatar>
                    <Typography variant="h4" fontWeight="bold">
                      {scenarioCount}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Scenarios
                    </Typography>
                  </Box>
                </Grid>
              </Grid>
            </Box>
          </Paper>
        </Grid>
      </Grid>
      <Grid container spacing={3}>
        {/* Project Information */}
        {/* <Grid size={{ xs: 12, md: 6 }}>
          <Card>
            <CardContent>
              <Typography
                variant="h6"
                gutterBottom
                sx={{ display: "flex", alignItems: "center" }}
              >
                <DescriptionIcon sx={{ mr: 1 }} />
                Project Information
              </Typography>
              <Divider sx={{ mb: 2 }} />

              <Box sx={{ mb: 2 }}>
                <Typography variant="body2" color="text.secondary">
                  Project ID
                </Typography>
                <Typography variant="body1">{project.id}</Typography>
              </Box>

              <Box sx={{ mb: 2 }}>
                <Typography variant="body2" color="text.secondary">
                  Created
                </Typography>
                <Typography
                  variant="body1"
                  sx={{ display: "flex", alignItems: "center" }}
                >
                  <CalendarIcon sx={{ mr: 1, fontSize: 16 }} />
                  {formatDate(project.created_at)}
                </Typography>
              </Box>

              <Box sx={{ mb: 2 }}>
                <Typography variant="body2" color="text.secondary">
                  Last Updated
                </Typography>
                <Typography
                  variant="body1"
                  sx={{ display: "flex", alignItems: "center" }}
                >
                  <CalendarIcon sx={{ mr: 1, fontSize: 16 }} />
                  {formatDate(project.updated_at)}
                </Typography>
              </Box>

              {project.created_by && (
                <Box>
                  <Typography variant="body2" color="text.secondary">
                    Created By
                  </Typography>
                  <Typography
                    variant="body1"
                    sx={{ display: "flex", alignItems: "center" }}
                  >
                    <PersonIcon sx={{ mr: 1, fontSize: 16 }} />
                    {project.created_by}
                  </Typography>
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid> */}

        {/* Project Statistics */}
        {/* <Grid size={{ xs: 12, md: 6 }}>
          <Card>
            <CardContent>
              <Typography
                variant="h6"
                gutterBottom
                sx={{ display: "flex", alignItems: "center" }}
              >
                <FolderIcon sx={{ mr: 1 }} />
                Project Content
              </Typography>
              <Divider sx={{ mb: 2 }} />

              <Grid container spacing={2}>
                <Grid size={6}>
                  <Box sx={{ textAlign: "center", p: 2 }}>
                    <Avatar
                      sx={{
                        width: 48,
                        height: 48,
                        bgcolor: "primary.main",
                        mx: "auto",
                        mb: 1,
                      }}
                    >
                      <DescriptionIcon />
                    </Avatar>
                    <Typography variant="h4" fontWeight="bold">
                      {documentCount}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Documents
                    </Typography>
                  </Box>
                </Grid>
                <Grid size={6}>
                  <Box sx={{ textAlign: "center", p: 2 }}>
                    <Avatar
                      sx={{
                        width: 48,
                        height: 48,
                        bgcolor: "secondary.main",
                        mx: "auto",
                        mb: 1,
                      }}
                    >
                      <FolderIcon />
                    </Avatar>
                    <Typography variant="h4" fontWeight="bold">
                      {scenarioCount}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Scenarios
                    </Typography>
                  </Box>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid> */}

        {/* Recent Activity */}
        <Grid size={{ xs: 12 }}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Recent Activity
              </Typography>
              <Divider sx={{ mb: 2 }} />
              <Typography variant="body2" color="text.secondary">
                No recent activity to display.
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default ProjectDetails;
