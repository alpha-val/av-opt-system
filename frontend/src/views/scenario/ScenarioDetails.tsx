import React, { useEffect } from "react";
import { useParams, useNavigate, Link as RouterLink } from "react-router-dom";
import { useDispatch, useSelector } from "react-redux";
import {
  Box,
  Typography,
  CircularProgress,
  Alert,
  Paper,
  Chip,
  Breadcrumbs,
  Link,
  Button,
} from "@mui/material";
import {
  fetchScenarioById,
  selectCurrentScenario,
  selectScenariosLoading,
  selectScenariosError,
  clearError,
} from "../../redux/scenariosSlice";
import {
  fetchProjectById,
  selectCurrentProject,
} from "../../redux/projectsSlice";
import { ScenarioStatus } from "../../types/api";

interface ScenarioDetailsProps {
  scenarioId?: string;
  projectId?: string;
  onBack?: () => void;
}

/**
 * Scenario Details page - placeholder for scenario details view.
 * 
 * This is a placeholder page that will be expanded later with scenario-specific
 * content and functionality.
 * 
 * Can be used as a standalone page (via route params) or embedded in a parent component (via props).
 */
const ScenarioDetails: React.FC<ScenarioDetailsProps> = ({ scenarioId: propScenarioId, projectId: propProjectId, onBack }) => {
  const routeParams = useParams<{
    projectId: string;
    scenarioId: string;
  }>();
  
  // Use props if provided, otherwise fall back to route params
  const scenarioId = propScenarioId || routeParams.scenarioId;
  const projectId = propProjectId || routeParams.projectId;
  
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const scenario = useSelector(selectCurrentScenario);
  const project = useSelector(selectCurrentProject);
  const loading = useSelector(selectScenariosLoading);
  const error = useSelector(selectScenariosError);

  /**
   * Fetch scenario and project data
   */
  useEffect(() => {
    if (scenarioId) {
      if (!scenario || scenario.id !== scenarioId) {
        dispatch(fetchScenarioById(scenarioId) as any);
      }
    }
    if (projectId) {
      if (!project || project.id !== projectId) {
        dispatch(fetchProjectById(projectId) as any);
      }
    }
  }, [scenarioId, projectId, scenario, project, dispatch]);

  /**
   * Get status color for chip
   */
  const getStatusColor = (
    status: ScenarioStatus
  ): "default" | "primary" | "secondary" | "error" | "info" | "success" | "warning" => {
    switch (status) {
      case ScenarioStatus.DRAFT:
        return "default";
      case ScenarioStatus.PROCESSING:
        return "info";
      case ScenarioStatus.COMPLETED:
        return "success";
      case ScenarioStatus.FAILED:
        return "error";
      default:
        return "default";
    }
  };

  if (!scenarioId || !projectId) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error">Invalid scenario or project ID</Alert>
      </Box>
    );
  }

  /**
   * Format date for display
   */
  const formatDate = (dateString: string): string => {
    try {
      return new Date(dateString).toLocaleDateString("en-US", {
        year: "numeric",
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      });
    } catch {
      return dateString;
    }
  };

  // If embedded (onBack provided), show a simpler header with back button
  // Otherwise, show full breadcrumb navigation
  const isEmbedded = !!onBack;

  return (
    <Box sx={{ p: 0 }}>
      {/* Breadcrumb Navigation - only show if not embedded */}
      {!isEmbedded && (
        <Box
          sx={{
            mb: 2,
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
          }}
        >
          <Breadcrumbs aria-label="breadcrumb">
            <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
              <Link
                component={RouterLink}
                to="/projects"
                color="primary"
                underline="hover"
              >
                All Projects
              </Link>
            </Box>
            {project ? (
              <Box
                sx={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                }}
              >
                <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                  <Link
                    component={RouterLink}
                    to={`/projects/${projectId}`}
                    color="primary"
                    underline="hover"
                  >
                    {project.name}
                  </Link>
                </Box>
              </Box>
            ) : (
              <Typography color="text.secondary">Loading...</Typography>
            )}
            <Box
              sx={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
              }}
            >
              <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                <Link
                  component={RouterLink}
                  to={`/projects/${projectId}#scenarios`}
                  color="primary"
                  underline="hover"
                >
                  All Scenarios
                </Link>
              </Box>
            </Box>
            {scenario && (
              <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                <Typography color="text.secondary">{scenario.name}</Typography>
                <Chip
                  label={scenario.status}
                  size="small"
                  color={getStatusColor(scenario.status)}
                />
              </Box>
            )}
          </Breadcrumbs>
          {scenario && (
            <Typography variant="body2" color="text.secondary">
              Created: {formatDate(scenario.created_at)}
            </Typography>
          )}
        </Box>
      )}

      {/* Embedded Header - show if embedded */}
      {isEmbedded && (
        <Box
          sx={{
            mb: 2,
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
          }}
        >
          <Box sx={{ display: "flex", alignItems: "center", gap: 2 }}>
            <Button
              onClick={onBack}
              size="small"
              sx={{ textTransform: "none" }}
            >
              ← Back to Scenarios
            </Button>
            {scenario && (
              <Chip
                label={scenario.status}
                size="small"
                color={getStatusColor(scenario.status)}
              />
            )}
          </Box>
          {scenario && (
            <Typography variant="body2" color="text.secondary">
              Created: {formatDate(scenario.created_at)}
            </Typography>
          )}
        </Box>
      )}

      {/* Error Alert */}
      {error && (
        <Alert
          severity="error"
          sx={{ mb: 2 }}
          onClose={() => dispatch(clearError())}
        >
          {error}
        </Alert>
      )}

      {/* Loading State */}
      {loading && !scenario ? (
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
      ) : scenario ? (
        <>
          {/* Scenario Info Panel */}
          <Paper elevation={1} sx={{ p: 3, mb: 3 }}>
            <Typography variant="h4" component="h1" gutterBottom>
              {scenario.name}
            </Typography>
            {scenario.description && (
              <Typography variant="body1" color="text.secondary" gutterBottom>
                {scenario.description}
              </Typography>
            )}
            <Typography variant="body2" color="text.secondary">
              Scenario ID: {scenario.id}
            </Typography>
          </Paper>

          {/* Placeholder Content */}
          <Paper elevation={1} sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Scenario Details
            </Typography>
            <Alert severity="info" sx={{ mt: 2 }}>
              <Typography variant="body2">
                This is a placeholder page for scenario details. The actual
                implementation will include scenario configuration, analysis
                results, and other scenario-specific content.
              </Typography>
            </Alert>
          </Paper>
        </>
      ) : (
        <Alert severity="warning">Scenario not found</Alert>
      )}
    </Box>
  );
};

export default ScenarioDetails;

