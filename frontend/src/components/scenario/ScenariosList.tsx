import React, { useEffect, useState, useMemo } from "react";
import { useDispatch, useSelector } from "react-redux";
import { useNavigate } from "react-router-dom";
import {
  Box,
  Typography,
  Button,
  Card,
  CardContent,
  CardActions,
  Grid,
  Chip,
  CircularProgress,
  Alert,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
} from "@mui/material";
import {
  Add as AddIcon,
  PlayArrow as PlayArrowIcon,
  Delete as DeleteIcon,
  Edit as EditIcon,
} from "@mui/icons-material";
import {
  fetchScenarios,
  createScenario,
  deleteScenario,
  selectScenariosByProject,
  selectScenariosLoading,
  selectScenariosError,
  selectScenarioCreating,
  selectScenarioDeleting,
  clearError,
} from "../../redux/scenariosSlice";
import { ScenarioStatus, ScenarioCreate } from "../../types/api";

interface ScenariosListProps {
  projectId: string;
  onScenarioSelect?: (scenarioId: string) => void;
}

/**
 * Scenarios list component.
 * 
 * Displays an empty state with "Create New Scenario" button when no scenarios exist,
 * or a grid of scenario cards when scenarios are present.
 */
const ScenariosList: React.FC<ScenariosListProps> = ({ projectId, onScenarioSelect }) => {
  const navigate = useNavigate();
  const dispatch = useDispatch();
  
  // Memoize the selector to avoid creating a new one on every render
  const memoizedSelector = useMemo(
    () => selectScenariosByProject(projectId),
    [projectId]
  );
  
  const scenarios = useSelector(memoizedSelector);
  const loading = useSelector(selectScenariosLoading);
  const creating = useSelector(selectScenarioCreating);
  const deleting = useSelector(selectScenarioDeleting);
  const error = useSelector(selectScenariosError);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [newScenarioName, setNewScenarioName] = useState("");
  const [newScenarioDescription, setNewScenarioDescription] = useState("");

  /**
   * Fetch scenarios for the project
   */
  useEffect(() => {
    dispatch(fetchScenarios(projectId) as any);
  }, [projectId, dispatch]);

  /**
   * Handle creating a new scenario
   */
  const handleCreateScenario = () => {
    if (!newScenarioName.trim()) {
      return;
    }

    const scenarioData: ScenarioCreate = {
      name: newScenarioName.trim(),
      description: newScenarioDescription.trim() || undefined,
      project_id: projectId,
      status: ScenarioStatus.DRAFT,
      configuration: {},
    };

    dispatch(createScenario(scenarioData) as any).then((result: any) => {
      if (createScenario.fulfilled.match(result)) {
        setCreateDialogOpen(false);
        setNewScenarioName("");
        setNewScenarioDescription("");
      }
    });
  };

  /**
   * Handle deleting a scenario
   */
  const handleDeleteScenario = (scenarioId: string, event: React.MouseEvent) => {
    event.stopPropagation();
    if (window.confirm("Are you sure you want to delete this scenario?")) {
      dispatch(deleteScenario(scenarioId) as any);
    }
  };

  /**
   * Handle clicking on a scenario card
   */
  const handleScenarioClick = (scenarioId: string) => {
    if (onScenarioSelect) {
      onScenarioSelect(scenarioId);
    } else {
      navigate(`/projects/${projectId}/scenarios/${scenarioId}`);
    }
  };

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

  return (
    <Box>
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
      {loading ? (
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
      ) : scenarios.length === 0 ? (
        /* Empty State */
        <Box
          sx={{
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            minHeight: "400px",
            textAlign: "center",
            p: 4,
          }}
        >
          <Typography variant="h5" gutterBottom color="text.secondary">
            No scenarios yet
          </Typography>
          <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
            Create your first scenario to start analyzing different options for this project.
          </Typography>
          <Button
            variant="contained"
            size="large"
            startIcon={<AddIcon />}
            onClick={() => setCreateDialogOpen(true)}
            disabled={creating}
          >
            Create New Scenario
          </Button>
        </Box>
      ) : (
        /* Scenarios Grid */
        <>
          <Box
            sx={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              mb: 3,
            }}
          >
            <Typography variant="h6">
              Scenarios ({scenarios.length})
            </Typography>
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={() => setCreateDialogOpen(true)}
              disabled={creating}
            >
              Create New Scenario
            </Button>
          </Box>

          <Grid container spacing={3}>
            {scenarios.map((scenario) => (
              <Grid item xs={12} sm={6} md={4} key={scenario.id}>
                <Card
                  sx={{
                    height: "100%",
                    display: "flex",
                    flexDirection: "column",
                    cursor: "pointer",
                    "&:hover": {
                      boxShadow: 4,
                    },
                  }}
                  onClick={() => handleScenarioClick(scenario.id)}
                >
                  <CardContent sx={{ flexGrow: 1 }}>
                    <Box
                      sx={{
                        display: "flex",
                        justifyContent: "space-between",
                        alignItems: "flex-start",
                        mb: 1,
                      }}
                    >
                      <Typography variant="h6" component="h3" gutterBottom>
                        {scenario.name}
                      </Typography>
                      <Chip
                        label={scenario.status}
                        size="small"
                        color={getStatusColor(scenario.status)}
                        onClick={(e) => e.stopPropagation()}
                      />
                    </Box>
                    {scenario.description && (
                      <Typography
                        variant="body2"
                        color="text.secondary"
                        sx={{ mb: 2 }}
                      >
                        {scenario.description}
                      </Typography>
                    )}
                    <Typography variant="caption" color="text.secondary">
                      Created: {formatDate(scenario.created_at)}
                    </Typography>
                  </CardContent>
                  <CardActions
                    sx={{
                      justifyContent: "flex-end",
                      px: 2,
                      pb: 2,
                    }}
                    onClick={(e) => e.stopPropagation()}
                  >
                    <IconButton
                      size="small"
                      onClick={(e) => handleDeleteScenario(scenario.id, e)}
                      disabled={deleting}
                      color="error"
                    >
                      <DeleteIcon fontSize="small" />
                    </IconButton>
                  </CardActions>
                </Card>
              </Grid>
            ))}
          </Grid>
        </>
      )}

      {/* Create Scenario Dialog */}
      <Dialog
        open={createDialogOpen}
        onClose={() => setCreateDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Create New Scenario</DialogTitle>
        <DialogContent>
          <Box sx={{ display: "flex", flexDirection: "column", gap: 2, pt: 1 }}>
            <TextField
              label="Scenario Name"
              required
              fullWidth
              value={newScenarioName}
              onChange={(e) => setNewScenarioName(e.target.value)}
              inputProps={{ maxLength: 200 }}
              helperText={`${newScenarioName.length}/200 characters`}
            />
            <TextField
              label="Description (Optional)"
              fullWidth
              multiline
              rows={3}
              value={newScenarioDescription}
              onChange={(e) => setNewScenarioDescription(e.target.value)}
              inputProps={{ maxLength: 500 }}
              helperText={`${newScenarioDescription.length}/500 characters`}
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button
            onClick={() => {
              setCreateDialogOpen(false);
              setNewScenarioName("");
              setNewScenarioDescription("");
            }}
            disabled={creating}
          >
            Cancel
          </Button>
          <Button
            onClick={handleCreateScenario}
            variant="contained"
            disabled={creating || !newScenarioName.trim()}
          >
            {creating ? "Creating..." : "Create"}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default ScenariosList;

