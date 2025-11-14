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
  MenuItem,
  Select,
  FormControl,
  InputLabel,
} from "@mui/material";
import {
  Add as AddIcon,
  PlayArrow as PlayArrowIcon,
  Delete as DeleteIcon,
  Edit as EditIcon,
  Description as DescriptionIcon,
  TrackChanges as ObjectiveIcon,
  CalendarToday as CalendarIcon,
  FolderSpecial as FolderSpecialIcon,
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
import { useDialogs } from "../../hooks/useDialogs";

const OBJECTIVE_TYPES = [
  "increase production",
  "reduce capex",
  "reduce wastage",
  "improve efficiency",
  "reduce opex",
  "optimize capacity",
];

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
const ScenariosList: React.FC<ScenariosListProps> = ({
  projectId,
  onScenarioSelect,
}) => {
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const dialogs = useDialogs();

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
  const [newObjectiveType, setNewObjectiveType] = useState("");
  const [newTargetValue, setNewTargetValue] = useState("");
  const [newTargetType, setNewTargetType] = useState<"%" | "$">("%");

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

    // Validate required objective fields
    if (!newObjectiveType.trim()) {
      return;
    }
    if (!newTargetValue.trim()) {
      return;
    }

    const globalObjectiveTarget = `${newTargetValue}${newTargetType}`;

    const scenarioData: ScenarioCreate = {
      name: newScenarioName.trim(),
      description: "", // Always empty string as per requirements
      project_id: projectId,
      status: ScenarioStatus.DRAFT,
      global_objective_type: newObjectiveType,
      global_objective_target: globalObjectiveTarget,
      configuration: {},
    };

    dispatch(createScenario(scenarioData) as any).then((result: any) => {
      if (createScenario.fulfilled.match(result)) {
        const newScenarioId = result.payload.id;
        // Clear form state
        setCreateDialogOpen(false);
        setNewScenarioName("");
        setNewScenarioDescription("");
        setNewObjectiveType("");
        setNewTargetValue("");
        setNewTargetType("%");
        // Navigate to scenario details
        navigate(`/projects/${projectId}/scenarios/${newScenarioId}`);
      }
    });
  };

  /**
   * Handle deleting a scenario
   */
  const handleDeleteScenario = async (
    scenarioId: string,
    event: React.MouseEvent
  ) => {
    event.stopPropagation();

    // Find scenario to show name in warning
    const scenarioToDelete = scenarios.find((s) => s.id === scenarioId);
    const scenarioName = scenarioToDelete?.name || "this scenario";

    // Show confirmation dialog with warning
    const confirmed = await dialogs.confirm(
      `Deleting "${scenarioName}" will permanently remove the scenario and all associated data. This includes:
      
• All analysis results and reports for this scenario
• Extracted entities and relationships
• Cost estimates and calculations
• Any configuration and objective data

This action cannot be undone. Are you sure you want to delete this scenario?`,
      {
        title: "Delete Scenario",
        severity: "error",
        okText: "Delete",
        cancelText: "Cancel",
      }
    );

    if (!confirmed) {
      return; // User cancelled
    }

    dispatch(clearError());
    dispatch(deleteScenario(scenarioId) as any);
  };

  /**
   * Handle clicking on a scenario card
   * Always navigates to scenario details page
   */
  const handleScenarioClick = (scenarioId: string) => {
    navigate(`/projects/${projectId}/scenarios/${scenarioId}`);
  };

  /**
   * Get status color for chip
   */
  const getStatusColor = (
    status: ScenarioStatus
  ):
    | "default"
    | "primary"
    | "secondary"
    | "error"
    | "info"
    | "success"
    | "warning" => {
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
            Create your first scenario to start analyzing different options for
            this project.
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
            <Typography variant="h6">Scenarios ({scenarios.length})</Typography>
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
                  variant="outlined"
                  sx={{
                    height: "100%",
                    display: "flex",
                    flexDirection: "column",
                    cursor: "pointer",
                    transition: "transform 0.2s, box-shadow 0.2s",
                    border: "1px solid",
                    borderColor: "divider",
                    bgcolor: (theme) => theme.palette.mode === "dark" 
                      ? "rgba(156, 39, 176, 0.08)" 
                      : "rgba(156, 39, 176, 0.04)",
                    "&:hover": {
                      transform: "translateY(-2px)",
                      boxShadow: 3,
                      borderColor: "secondary.main",
                    },
                  }}
                  onClick={() => handleScenarioClick(scenario.id)}
                >
                  <CardContent sx={{ flexGrow: 1, p: 2.5 }}>
                    {/* Header with Title and Status */}
                    <Box
                      sx={{
                        display: "flex",
                        alignItems: "flex-start",
                        mb: 2,
                      }}
                    >
                      {/* <FolderSpecialIcon
                        sx={{
                          mr: 1.5,
                          fontSize: 24,
                          color: "secondary.main",
                          flexShrink: 0,
                          mt: 0.5,
                        }}
                      /> */}
                      <Box sx={{ flex: 1, minWidth: 0 }}>
                        <Typography
                          variant="h6"
                          component="h3"
                          sx={{
                            fontWeight: 600,
                            lineHeight: 1.3,
                            mb: 0.5,
                          }}
                        >
                          {scenario.name}
                        </Typography>
                        <Chip
                          label={scenario.status}
                          size="small"
                          color={getStatusColor(scenario.status)}
                          onClick={(e) => e.stopPropagation()}
                          sx={{
                            fontWeight: 500,
                            textTransform: "capitalize",
                          }}
                        />
                      </Box>
                    </Box>

                    {/* Description */}
                    {scenario.description && (
                      <Box
                        sx={{
                          display: "flex",
                          alignItems: "flex-start",
                          gap: 1,
                          mb: 2,
                        }}
                      >
                        <DescriptionIcon
                          fontSize="small"
                          sx={{ color: "text.secondary", mt: 0.5, flexShrink: 0 }}
                        />
                        <Typography
                          variant="body2"
                          color="text.secondary"
                          sx={{
                            lineHeight: 1.5,
                            display: "-webkit-box",
                            WebkitLineClamp: 2,
                            WebkitBoxOrient: "vertical",
                            overflow: "hidden",
                          }}
                        >
                          {scenario.description}
                        </Typography>
                      </Box>
                    )}

                    {/* Objective Information */}
                    {scenario.global_objective_type && (
                      <Box
                        sx={{
                          display: "flex",
                          alignItems: "center",
                          gap: 1,
                          mb: 2,
                          p: 1.5,
                          borderRadius: 1,
                          bgcolor: (theme) => theme.palette.mode === "dark" 
                            ? "rgba(25, 118, 210, 0.12)" 
                            : "rgba(25, 118, 210, 0.06)",
                        }}
                      >
                        <ObjectiveIcon
                          fontSize="small"
                          sx={{ color: "primary.main", flexShrink: 0 }}
                        />
                        <Box sx={{ flex: 1, minWidth: 0 }}>
                          <Typography
                            variant="caption"
                            color="text.secondary"
                            sx={{ display: "block", mb: 0.5 }}
                          >
                            Objective
                          </Typography>
                          <Typography
                            variant="body2"
                            sx={{
                              fontWeight: 500,
                              overflow: "hidden",
                              textOverflow: "ellipsis",
                              whiteSpace: "nowrap",
                            }}
                          >
                            {scenario.global_objective_type}
                            {scenario.global_objective_target && (
                              <Typography
                                component="span"
                                variant="body2"
                                color="primary.main"
                                sx={{ ml: 0.5, fontWeight: 600 }}
                              >
                                {scenario.global_objective_target}
                              </Typography>
                            )}
                          </Typography>
                        </Box>
                      </Box>
                    )}

                    {/* Footer with Date */}
                    <Box
                      sx={{
                        display: "flex",
                        alignItems: "center",
                        gap: 0.5,
                        mt: "auto",
                        pt: 2,
                        borderTop: "1px solid",
                        borderColor: "divider",
                      }}
                    >
                      <CalendarIcon
                        fontSize="small"
                        sx={{ color: "text.secondary", fontSize: 16 }}
                      />
                      <Typography
                        variant="caption"
                        color="text.secondary"
                        sx={{ fontSize: "0.75rem" }}
                      >
                        Created {formatDate(scenario.created_at)}
                      </Typography>
                    </Box>
                  </CardContent>

                  {/* Actions */}
                  <CardActions
                    sx={{
                      justifyContent: "flex-end",
                      px: 2,
                      pb: 2,
                      pt: 0,
                      gap: 0.5,
                    }}
                    onClick={(e) => e.stopPropagation()}
                  >
                    <IconButton
                      size="small"
                      onClick={(e) => handleDeleteScenario(scenario.id, e)}
                      disabled={deleting}
                      color="error"
                      sx={{
                        "&:hover": {
                          bgcolor: "error.light",
                          color: "error.contrastText",
                        },
                      }}
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
            {/* Objective Type */}
            <FormControl fullWidth required>
              <InputLabel>Global Objective Type</InputLabel>
              <Select
                value={newObjectiveType}
                onChange={(e) => setNewObjectiveType(e.target.value)}
                label="Global Objective Type"
              >
                {OBJECTIVE_TYPES.map((type) => (
                  <MenuItem key={type} value={type}>
                    {type}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            {/* Objective Target */}
            <Box
              sx={{
                display: "flex",
                gap: 1,
                alignItems: "flex-start",
              }}
            >
              <TextField
                label="Global Objective Target"
                required
                type="number"
                value={newTargetValue}
                onChange={(e) => setNewTargetValue(e.target.value)}
                sx={{ flex: 1 }}
              />
              <FormControl sx={{ minWidth: 80 }}>
                <Select
                  value={newTargetType}
                  onChange={(e) =>
                    setNewTargetType(e.target.value as "%" | "$")
                  }
                >
                  <MenuItem value="%">%</MenuItem>
                  <MenuItem value="$">$</MenuItem>
                </Select>
              </FormControl>
            </Box>
            {/* Description field hidden but state maintained */}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button
            onClick={() => {
              setCreateDialogOpen(false);
              setNewScenarioName("");
              setNewScenarioDescription("");
              setNewObjectiveType("");
              setNewTargetValue("");
              setNewTargetType("%");
            }}
            disabled={creating}
          >
            Cancel
          </Button>
          <Button
            onClick={handleCreateScenario}
            variant="contained"
            disabled={
              creating ||
              !newScenarioName.trim() ||
              !newObjectiveType.trim() ||
              !newTargetValue.trim()
            }
          >
            {creating ? "Creating..." : "Create"}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default ScenariosList;
