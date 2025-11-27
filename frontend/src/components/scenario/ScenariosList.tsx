import React, { useEffect, useState, useMemo, useRef } from "react";
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

  // Calculate the next number for "New Scenario" name
  const nextScenarioNumber = useMemo(() => {
    const newScenarioPattern = /^New Scenario(?: \((\d+)\))?$/;
    const matchingScenarios = scenarios.filter((scenario) =>
      newScenarioPattern.test(scenario.name)
    );
    
    if (matchingScenarios.length === 0) {
      return 1;
    }
    
    // Extract numbers from scenario names
    // If a scenario is named "New Scenario" (without number), treat it as 1
    const numbers = matchingScenarios.map((scenario) => {
      const match = scenario.name.match(/^New Scenario(?: \((\d+)\))?$/);
      return match && match[1] ? parseInt(match[1], 10) : 1;
    });
    
    // Return max + 1
    return Math.max(...numbers) + 1;
  }, [scenarios]);

  // Use refs for text inputs to prevent re-renders on every keystroke
  const nameInputRef = useRef<HTMLInputElement>(null);
  const descriptionInputRef = useRef<HTMLTextAreaElement>(null);
  const targetValueInputRef = useRef<HTMLInputElement>(null);
  const objectiveDescriptionInputRef = useRef<HTMLTextAreaElement>(null);

  // Keep state only for Select components (they need to display selected value)
  const [newObjectiveType, setNewObjectiveType] = useState("");
  const [newTargetType, setNewTargetType] = useState<"%" | "$" | "tpd" | "gpm">(
    "%"
  );

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
    // Read values from refs (only when submitting)
    const name = nameInputRef.current?.value.trim() || "";
    const description = descriptionInputRef.current?.value.trim() || "";
    const targetValue = targetValueInputRef.current?.value.trim() || "";
    const objectiveDescription =
      objectiveDescriptionInputRef.current?.value.trim() || "";

    if (!name) {
      return;
    }

    // Validate required objective fields
    if (!newObjectiveType.trim()) {
      return;
    }
    if (!targetValue) {
      return;
    }

    const scenarioData: ScenarioCreate = {
      name,
      description: description || undefined,
      project_id: projectId,
      status: ScenarioStatus.DRAFT,
      global_objective_type: newObjectiveType,
      global_objective_target: targetValue,
      global_objective_unit: newTargetType,
      objective_description: objectiveDescription || undefined,
      configuration: {},
    };

    dispatch(createScenario(scenarioData) as any).then((result: any) => {
      if (createScenario.fulfilled.match(result)) {
        const newScenarioId = result.payload.id;
        // Clear form inputs
        setCreateDialogOpen(false);
        if (nameInputRef.current) nameInputRef.current.value = "";
        if (descriptionInputRef.current) descriptionInputRef.current.value = "";
        if (targetValueInputRef.current) targetValueInputRef.current.value = "";
        if (objectiveDescriptionInputRef.current)
          objectiveDescriptionInputRef.current.value = "";
        setNewObjectiveType("");
        setNewTargetType("%");
        // Navigate to scenario details or use callback
        if (onScenarioSelect) {
          onScenarioSelect(newScenarioId);
        } else {
          navigate(`/projects/${projectId}/scenarios/${newScenarioId}`);
        }
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
   * Uses onScenarioSelect callback if provided, otherwise navigates
   */
  const handleScenarioClick = (scenarioId: string) => {
    if (onScenarioSelect) {
      onScenarioSelect(scenarioId);
    } else {
      navigate(`/projects/${projectId}/scenarios/${scenarioId}`);
    }
  };

  const handleDeleteAllScenarios = () => {
    // dispatch(deleteAllScenarios(projectId) as any);
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
  /**
   * Reset form inputs when dialog opens/closes
   */
  useEffect(() => {
    if (createDialogOpen) {
      // Clear inputs when dialog opens
      if (nameInputRef.current) nameInputRef.current.value = "";
      if (descriptionInputRef.current) descriptionInputRef.current.value = "";
      if (targetValueInputRef.current) targetValueInputRef.current.value = "";
      if (objectiveDescriptionInputRef.current)
        objectiveDescriptionInputRef.current.value = "";
      setNewObjectiveType("");
      setNewTargetType("%");
      // Focus on name input when dialog opens
      setTimeout(() => {
        nameInputRef.current?.focus();
      }, 100);
    }
  }, [createDialogOpen]);

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
              justifyContent: "flex-start",
              alignItems: "center",
              mb: 3,
              gap: 4,
            }}
          >
            <Typography variant="h6">Scenarios ({scenarios.length})</Typography>
            <Box>
              {/* <Button
                variant="outlined"
                color="error"
                startIcon={<DeleteIcon />}
                onClick={() => handleDeleteAllScenarios()}
                disabled={creating}
                sx={{ mr: 1 }}
              >
                Delete All Scenarios
              </Button> */}
              <Button
                variant="contained"
                startIcon={<AddIcon />}
                onClick={() => setCreateDialogOpen(true)}
                disabled={creating}
              >
                Create New Scenario
              </Button>
            </Box>
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
                    bgcolor: (theme) =>
                      theme.palette.mode === "dark"
                        ? "rgba(25, 118, 210, 0.08)"
                        : "rgba(156, 39, 176, 0.04)",
                    "&:hover": {
                      transform: "translateY(-2px)",
                      boxShadow: 3,
                      // borderColor: "secondary.main",
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
                          sx={{
                            color: "text.secondary",
                            mt: 0.5,
                            flexShrink: 0,
                          }}
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
                          bgcolor: (theme) =>
                            theme.palette.mode === "dark"
                              ? "rgba(25, 118, 210, 0.08)"
                              : "rgba(25, 118, 210, 0.04)",
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
                                {scenario.global_objective_target} {scenario.global_objective_unit}
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
              inputRef={nameInputRef}
              label="Scenario Name"
              required
              fullWidth
              defaultValue={`New Scenario (${nextScenarioNumber})`}
              inputProps={{ maxLength: 200 }}
            />
            {/* Scenario Description */}
            {/* <TextField
              inputRef={descriptionInputRef}
              label="Description (Optional)"
              fullWidth
              multiline
              rows={2}
              defaultValue=""
              inputProps={{ maxLength: 500 }}
            /> */}
            {/* Objective Type */}
            <FormControl fullWidth required>
              <InputLabel>Global Objective Type</InputLabel>
              <Select
                value={newObjectiveType}
                defaultValue="increase production"
                placeholder="increase production"
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
                inputRef={targetValueInputRef}
                label="Global Objective Target"
                required
                type="number"
                defaultValue="10"
                sx={{ flex: 1 }}
              />
              <FormControl sx={{ minWidth: 80 }}>
                <Select
                  value={newTargetType}
                  onChange={(e) =>
                    setNewTargetType(
                      e.target.value as "%" | "$" | "tpd" | "gpm"
                    )
                  }
                >
                  <MenuItem value="%">%</MenuItem>
                  <MenuItem value="$">$</MenuItem>
                </Select>
              </FormControl>
            </Box>
            {/* Objective Description */}
            <TextField
              inputRef={objectiveDescriptionInputRef}
              label="Provide additional details about the objective (optional)"
              multiline
              rows={3}
              fullWidth
              defaultValue=""
              inputProps={{ maxLength: 500 }}
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button
            onClick={() => {
              setCreateDialogOpen(false);
              // Clear form inputs
              if (nameInputRef.current) nameInputRef.current.value = "";
              if (descriptionInputRef.current)
                descriptionInputRef.current.value = "";
              if (targetValueInputRef.current)
                targetValueInputRef.current.value = "";
              if (objectiveDescriptionInputRef.current)
                objectiveDescriptionInputRef.current.value = "";
              setNewObjectiveType("");
              setNewTargetType("%");
            }}
            disabled={creating}
          >
            Cancel
          </Button>
          <Button
            onClick={handleCreateScenario}
            variant="contained"
            disabled={creating || !newObjectiveType.trim()}
          >
            {creating ? "Creating..." : "Create"}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default ScenariosList;
