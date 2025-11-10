import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  Box,
  Typography,
  Button,
  CircularProgress,
  Alert,
  Paper,
  Card,
  CardContent,
} from "@mui/material";
import {
  ArrowBack as ArrowBackIcon,
  Save as SaveIcon,
} from "@mui/icons-material";
import { projectApi } from "../../services/api";
import { ProjectOut } from "../../types/api";

/**
 * System Base Design view for entity validation.
 * 
 * This is a placeholder component that will be extended later to:
 * - Display extracted entities in structured view
 * - Show entity attributes (tank diameter, height, pump ratings, etc.)
 * - Allow editing attributes (mark as fixed/variable, set ranges)
 * - Submit updated system design
 */
const SystemBaseDesign: React.FC = () => {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  const [project, setProject] = useState<ProjectOut | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState<boolean>(false);

  /**
   * Fetch project data
   */
  const fetchProject = async (): Promise<void> => {
    if (!projectId) return;

    setLoading(true);
    setError(null);
    try {
      const data = await projectApi.getById(projectId);
      setProject(data);
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : "Failed to fetch project";
      setError(errorMessage);
      console.error("Error fetching project:", err);
    } finally {
      setLoading(false);
    }
  };

  /**
   * Handle saving system design
   */
  const handleSave = async (): Promise<void> => {
    if (!projectId) return;

    setSaving(true);
    try {
      // TODO: Implement entity validation and update logic
      // This will call the orchestration service's validate_entities method
      console.log("Saving system design for project:", projectId);
      
      // Placeholder: Show success message
      alert("System design saved (placeholder)");
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : "Failed to save system design";
      setError(errorMessage);
      console.error("Error saving system design:", err);
    } finally {
      setSaving(false);
    }
  };

  useEffect(() => {
    fetchProject();
  }, [projectId]);

  if (!projectId) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error">Invalid project ID</Alert>
      </Box>
    );
  }

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
        <Box sx={{ display: "flex", alignItems: "center", gap: 2 }}>
          <Button
            startIcon={<ArrowBackIcon />}
            onClick={() => navigate("/projects")}
          >
            Back
          </Button>
          <Typography variant="h4" component="h1">
            System Base Design
          </Typography>
        </Box>
        <Button
          variant="contained"
          startIcon={<SaveIcon />}
          onClick={handleSave}
          disabled={saving || loading}
        >
          {saving ? "Saving..." : "Save Changes"}
        </Button>
      </Box>

      {/* Error Alert */}
      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Loading State */}
      {loading ? (
        <Box
          sx={{
            display: "flex",
            justifyContent: "center",
            alignItems: "center",
            minHeight: "400px",
          }}
        >
          <CircularProgress />
        </Box>
      ) : project ? (
        /* Project Info and Placeholder Content */
        <Box sx={{ display: "flex", flexDirection: "column", gap: 3 }}>
          {/* Project Information */}
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Project: {project.name}
              </Typography>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Objective: {project.global_objective_type} - {project.global_objective_target}
              </Typography>
              {project.description && (
                <Typography variant="body2" color="text.secondary">
                  {project.description}
                </Typography>
              )}
            </CardContent>
          </Card>

          {/* Placeholder for Entity Validation */}
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Extracted Entities
              </Typography>
              <Typography variant="body2" color="text.secondary">
                This is a placeholder view. The actual implementation will:
              </Typography>
              <Box component="ul" sx={{ mt: 2, pl: 3 }}>
                <li>
                  <Typography variant="body2">
                    Display extracted entities in a structured view
                  </Typography>
                </li>
                <li>
                  <Typography variant="body2">
                    Show entity attributes (tank diameter, height, pump ratings, etc.)
                  </Typography>
                </li>
                <li>
                  <Typography variant="body2">
                    Allow editing attributes (mark as fixed/variable, set ranges)
                  </Typography>
                </li>
                <li>
                  <Typography variant="body2">
                    Submit updated system design to backend
                  </Typography>
                </li>
              </Box>
              <Alert severity="info" sx={{ mt: 2 }}>
                No entities extracted yet. Upload and process documents first.
              </Alert>
            </CardContent>
          </Card>
        </Box>
      ) : (
        <Alert severity="warning">Project not found</Alert>
      )}
    </Box>
  );
};

export default SystemBaseDesign;

