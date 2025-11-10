import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Box,
  Typography,
  Button,
  CircularProgress,
  Alert,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  IconButton,
  Tooltip,
} from "@mui/material";
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Refresh as RefreshIcon,
  Visibility as ViewIcon,
  Description as ReportIcon,
} from "@mui/icons-material";
import { ProjectOut, ProjectStatus } from "../../types/api";
import { projectApi } from "../../services/api";
import CreateProjectDialog from "../../components/project/CreateProjectDialog";

const ProjectList: React.FC = () => {
  const navigate = useNavigate();
  const [projects, setProjects] = useState<ProjectOut[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [createDialogOpen, setCreateDialogOpen] = useState<boolean>(false);

  /**
   * Fetch all projects from the API
   */
  const fetchProjects = async (): Promise<void> => {
    setLoading(true);
    setError(null);
    try {
      const data = await projectApi.listAll();
      setProjects(data);
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : "Failed to fetch projects";
      setError(errorMessage);
      console.error("Error fetching projects:", err);
    } finally {
      setLoading(false);
    }
  };

  /**
   * Delete a project
   */
  const handleDelete = async (projectId: string): Promise<void> => {
    if (!window.confirm("Are you sure you want to delete this project?")) {
      return;
    }

    try {
      await projectApi.delete(projectId);
      // Remove from local state
      setProjects(projects.filter((p) => p.id !== projectId));
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : "Failed to delete project";
      setError(errorMessage);
      console.error("Error deleting project:", err);
    }
  };

  /**
   * Format date for display
   */
  const formatDate = (dateString: string): string => {
    try {
      return new Date(dateString).toLocaleDateString("en-US", {
        year: "numeric",
        month: "short",
        day: "numeric",
      });
    } catch {
      return dateString;
    }
  };

  /**
   * Get status color for chip
   */
  const getStatusColor = (status: ProjectStatus): "default" | "primary" | "secondary" | "error" | "info" | "success" | "warning" => {
    switch (status) {
      case ProjectStatus.DRAFT:
        return "default";
      case ProjectStatus.PROCESSING:
        return "info";
      case ProjectStatus.VALIDATION:
        return "warning";
      case ProjectStatus.COMPLETED:
        return "success";
      default:
        return "default";
    }
  };

  // Fetch projects on component mount
  useEffect(() => {
    fetchProjects();
  }, []);

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box
        sx={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          mb: 3,
        }}
      >
        <Typography variant="h4" component="h1">
          Projects
        </Typography>
        <Box sx={{ display: "flex", gap: 1 }}>
          <Tooltip title="Refresh">
            <IconButton onClick={fetchProjects} disabled={loading}>
              <RefreshIcon />
            </IconButton>
          </Tooltip>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => setCreateDialogOpen(true)}
          >
            New Project
          </Button>
        </Box>
      </Box>

      {/* Error Alert */}
      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Loading State */}
      {loading && projects.length === 0 ? (
        <Box
          sx={{
            display: "flex",
            justifyContent: "center",
            alignItems: "center",
            minHeight: "200px",
          }}
        >
          <CircularProgress />
        </Box>
      ) : (
        /* Projects Table */
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Name</TableCell>
                <TableCell>Description</TableCell>
                <TableCell>Objective</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Tags</TableCell>
                <TableCell>Created</TableCell>
                <TableCell>Updated</TableCell>
                <TableCell align="right">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {projects.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={8} align="center">
                    <Typography variant="body2" color="text.secondary">
                      No projects found. Create your first project to get started.
                    </Typography>
                  </TableCell>
                </TableRow>
              ) : (
                projects.map((project) => (
                  <TableRow key={project.id} hover>
                    <TableCell>
                      <Typography variant="body1" fontWeight="medium">
                        {project.name}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Typography
                        variant="body2"
                        color="text.secondary"
                        sx={{
                          maxWidth: "200px",
                          overflow: "hidden",
                          textOverflow: "ellipsis",
                          whiteSpace: "nowrap",
                        }}
                      >
                        {project.description || "—"}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2" color="text.secondary">
                        {project.global_objective_type}: {project.global_objective_target}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={project.status}
                        size="small"
                        color={getStatusColor(project.status)}
                      />
                    </TableCell>
                    <TableCell>
                      <Box sx={{ display: "flex", gap: 0.5, flexWrap: "wrap" }}>
                        {project.tags && project.tags.length > 0 ? (
                          project.tags.map((tag, index) => (
                            <Chip key={index} label={tag} size="small" />
                          ))
                        ) : (
                          <Typography variant="body2" color="text.secondary">
                            —
                          </Typography>
                        )}
                      </Box>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2" color="text.secondary">
                        {formatDate(project.created_at)}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2" color="text.secondary">
                        {formatDate(project.updated_at)}
                      </Typography>
                    </TableCell>
                    <TableCell align="right">
                      <Box sx={{ display: "flex", gap: 0.5, justifyContent: "flex-end" }}>
                        <Tooltip title="View System Design">
                          <IconButton
                            size="small"
                            onClick={() => {
                              navigate(`/projects/${project.id}/system-design`);
                            }}
                          >
                            <ViewIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title="View Report">
                          <IconButton
                            size="small"
                            onClick={() => {
                              navigate(`/projects/${project.id}/report`);
                            }}
                          >
                            <ReportIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title="Edit">
                          <IconButton
                            size="small"
                            onClick={() => {
                              // TODO: Open edit dialog
                              console.log("Edit project:", project.id);
                            }}
                          >
                            <EditIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title="Delete">
                          <IconButton
                            size="small"
                            color="error"
                            onClick={() => handleDelete(project.id)}
                          >
                            <DeleteIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                      </Box>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </TableContainer>
      )}

      {/* Create Project Dialog */}
      <CreateProjectDialog
        open={createDialogOpen}
        onClose={() => setCreateDialogOpen(false)}
        onSuccess={() => {
          fetchProjects();
        }}
      />
    </Box>
  );
};

export default ProjectList;

