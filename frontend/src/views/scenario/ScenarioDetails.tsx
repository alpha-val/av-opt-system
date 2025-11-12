import React, { useEffect, useState } from "react";
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
  Tabs,
  Tab,
  Card,
  CardContent,
  TextField,
  MenuItem,
  Select,
  FormControl,
  InputLabel,
  Tooltip,
} from "@mui/material";
import { PlayArrow as PlayArrowIcon } from "@mui/icons-material";
import {
  fetchScenarioById,
  selectCurrentScenario,
  selectScenariosLoading,
  selectScenariosError,
  updateScenario,
  runAnalysis,
  selectScenarioRunningAnalysis,
  clearError,
} from "../../redux/scenariosSlice";
import {
  fetchProjectById,
  selectCurrentProject,
} from "../../redux/projectsSlice";
import { ScenarioStatus, ScenarioUpdate } from "../../types/api";

const OBJECTIVE_TYPES = [
  "increase production",
  "reduce capex",
  "reduce wastage",
  "improve efficiency",
  "reduce opex",
  "optimize capacity",
];

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
const ScenarioDetails: React.FC<ScenarioDetailsProps> = ({
  scenarioId: propScenarioId,
  projectId: propProjectId,
  onBack,
}) => {
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
  const runningAnalysis = useSelector(selectScenarioRunningAnalysis);
  const updating = useSelector((state: any) => state.scenarios.loading.update);
  const [activeTab, setActiveTab] = useState<number>(0);

  // Objective details form state
  const [objectiveType, setObjectiveType] = useState<string>("");
  const [targetValue, setTargetValue] = useState<string>("");
  const [targetType, setTargetType] = useState<"%" | "$">("%");
  const [objectiveDescription, setObjectiveDescription] = useState<string>("");
  const [objectiveError, setObjectiveError] = useState<string | null>(null);
  const [analysisError, setAnalysisError] = useState<string | null>(null);

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
   * Initialize form with scenario data when scenario loads
   */
  useEffect(() => {
    if (scenario && scenario.id === scenarioId) {
      setObjectiveType(scenario.global_objective_type || "");
      // Parse target value and type from global_objective_target
      if (scenario.global_objective_target) {
        const match =
          scenario.global_objective_target.match(/^([\d.]+)([%$])$/);
        if (match) {
          setTargetValue(match[1]);
          setTargetType(match[2] as "%" | "$");
        } else {
          setTargetValue(scenario.global_objective_target);
        }
      }
      setObjectiveDescription(scenario.objective_description || "");
    }
  }, [scenario, scenarioId]);

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

  /**
   * Handle saving objective details
   */
  const handleSaveObjectiveDetails = (): void => {
    if (!scenarioId) return;

    setObjectiveError(null);
    dispatch(clearError());

    // Validate objective fields
    if (!objectiveType) {
      setObjectiveError("Global objective type is required");
      return;
    }
    if (!targetValue || targetValue.trim().length === 0) {
      setObjectiveError("Global objective target is required");
      return;
    }

    // Build global objective target string
    const globalObjectiveTarget = `${targetValue}${targetType}`;

    // Create update payload
    const updateData: ScenarioUpdate = {
      global_objective_type: objectiveType,
      global_objective_target: globalObjectiveTarget,
      objective_description: objectiveDescription || undefined,
    };

    // Dispatch update
    dispatch(updateScenario({ scenarioId, data: updateData }) as any);
  };

  /**
   * Check if analysis can be run
   */
  const canRunAnalysis = (): boolean => {
    if (!scenario || !project) return false;

    // Check objective details
    if (!objectiveType || !targetValue || targetValue.trim().length === 0) {
      return false;
    }

    // Check if base case documents are uploaded (required)
    const hasBaseCaseFiles =
      project.base_case_documents && project.base_case_documents.length > 0;

    return hasBaseCaseFiles;
  };

  /**
   * Get tooltip message for Run Analysis button
   */
  const getRunAnalysisTooltip = (): string => {
    if (!scenario || !project) {
      return "Scenario or project data not loaded";
    }

    if (!objectiveType || !targetValue || targetValue.trim().length === 0) {
      return "Please complete objective details (type and target)";
    }

    const hasBaseCaseFiles =
      project.base_case_documents && project.base_case_documents.length > 0;

    if (!hasBaseCaseFiles) {
      return "Base case documents are required. Please upload base case documents in the Sources tab.";
    }

    return "";
  };

  /**
   * Handle running analysis
   */
  const handleRunAnalysis = async (): Promise<void> => {
    if (!scenarioId) return;

    setAnalysisError(null);
    dispatch(clearError());

    // Validate requirements
    if (!scenario) {
      setAnalysisError("Scenario data not loaded");
      return;
    }

    if (!project) {
      setAnalysisError("Project data not loaded");
      return;
    }

    if (!objectiveType || !targetValue || targetValue.trim().length === 0) {
      setAnalysisError(
        "Objective details are required. Please set objective type and target."
      );
      return;
    }

    // Save objective details if they've changed
    if (
      scenario.global_objective_type !== objectiveType ||
      scenario.global_objective_target !== `${targetValue}${targetType}`
    ) {
      await handleSaveObjectiveDetails();
      // Refresh scenario data
      await dispatch(fetchScenarioById(scenarioId) as any);
    }

    // Check if base case documents are uploaded (required)
    if (
      !project.base_case_documents ||
      project.base_case_documents.length === 0
    ) {
      setAnalysisError(
        "Base case documents are required. Please upload base case documents in the Sources tab before running analysis."
      );
      return;
    }

    // Dispatch run analysis action
    dispatch(runAnalysis(scenarioId) as any).then((result: any) => {
      if (runAnalysis.rejected.match(result)) {
        setAnalysisError(result.payload as string);
      }
    });
  };

  interface TabPanelProps {
    children?: React.ReactNode;
    index: number;
    value: number;
  }

  const TabPanel: React.FC<TabPanelProps> = ({ children, value, index }) => {
    return (
      <div
        role="tabpanel"
        hidden={value !== index}
        id={`scenario-tabpanel-${index}`}
        aria-labelledby={`scenario-tab-${index}`}
      >
        {value === index && <Box sx={{ pt: 3 }}>{children}</Box>}
      </div>
    );
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
              <Box
                sx={{
                  display: "flex",
                  flexDirection: "row",
                  alignItems: "center",
                  gap: 2,
                }}
              >
                <Typography variant="h6" component="h2">
                  {scenario.name}
                </Typography>
                <Typography variant="body1" color="text.secondary">
                  {scenario.description || "No description available"}
                </Typography>
              </Box>
            )}{" "}
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
          {/* <Paper elevation={0} sx={{ p: 1, mb: 3, backgroundColor: "#f9f9f9" }}>
            <Typography variant="h4" component="h1" gutterBottom>
              {scenario.name}
            </Typography>
            {scenario.description && (
              <Typography variant="body1" color="text.secondary" gutterBottom>
                Description: {scenario.description || "No description available"}
              </Typography>
            )}
          </Paper> */}

          {/* Tabbed Interface */}
          <Paper sx={{ flex: 1, display: "flex", flexDirection: "column" }}>
            <Box sx={{ borderBottom: 1, borderColor: "divider" }}>
              <Tabs
                value={activeTab}
                onChange={(_, newValue) => setActiveTab(newValue)}
                aria-label="scenario details tabs"
              >
                <Tab label="Objectives" id="scenario-tab-0" />
                <Tab label="System Design" id="scenario-tab-1" />
                <Tab label="Cost Estimate" id="scenario-tab-2" />
                <Tab label="Report" id="scenario-tab-3" />
              </Tabs>
            </Box>

            {/* Tab 0: Objectives */}
            <TabPanel value={activeTab} index={0}>
              <Box sx={{ p: 3 }}>
                <Box
                  sx={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    mb: 3,
                  }}
                >
                  <Typography variant="h6">Objective Details</Typography>
                  <Tooltip title={getRunAnalysisTooltip()} arrow>
                    <span>
                      <Button
                        variant="contained"
                        color="primary"
                        size="small"
                        startIcon={
                          runningAnalysis ? (
                            <CircularProgress size={20} />
                          ) : (
                            <PlayArrowIcon />
                          )
                        }
                        onClick={handleRunAnalysis}
                        disabled={runningAnalysis || !canRunAnalysis()}
                      >
                        {runningAnalysis
                          ? "Running Analysis..."
                          : "Run Analysis"}
                      </Button>
                    </span>
                  </Tooltip>
                </Box>

                {(objectiveError || analysisError) && (
                  <Alert
                    severity="error"
                    sx={{ mb: 2 }}
                    onClose={() => {
                      setObjectiveError(null);
                      setAnalysisError(null);
                      dispatch(clearError());
                    }}
                  >
                    {objectiveError || analysisError}
                  </Alert>
                )}

                {!canRunAnalysis() && (
                  <Alert severity="warning" sx={{ mb: 2 }}>
                    {!scenario || !project
                      ? "Scenario or project data not loaded"
                      : !objectiveType ||
                        !targetValue ||
                        targetValue.trim().length === 0
                      ? "Please complete objective details (type and target) before running analysis."
                      : "Base case documents are required. Please upload base case documents in the Sources tab before running analysis."}
                  </Alert>
                )}

                <Card>
                  <CardContent>
                    {objectiveError && (
                      <Alert
                        severity="error"
                        sx={{ mb: 2 }}
                        onClose={() => setObjectiveError(null)}
                      >
                        {objectiveError}
                      </Alert>
                    )}

                    <Box
                      sx={{ display: "flex", flexDirection: "column", gap: 2 }}
                    >
                      {/* Global Objective Type */}
                      <FormControl fullWidth required>
                        <InputLabel>Global Objective Type</InputLabel>
                        <Select
                          value={objectiveType}
                          onChange={(e) => setObjectiveType(e.target.value)}
                          label="Global Objective Type"
                        >
                          {OBJECTIVE_TYPES.map((type) => (
                            <MenuItem key={type} value={type}>
                              {type}
                            </MenuItem>
                          ))}
                        </Select>
                      </FormControl>

                      {/* Global Objective Target */}
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
                          value={targetValue}
                          onChange={(e) => setTargetValue(e.target.value)}
                          sx={{ flex: 1 }}
                        />
                        <FormControl sx={{ minWidth: 80 }}>
                          <Select
                            value={targetType}
                            onChange={(e) =>
                              setTargetType(e.target.value as "%" | "$")
                            }
                          >
                            <MenuItem value="%">%</MenuItem>
                            <MenuItem value="$">$</MenuItem>
                          </Select>
                        </FormControl>
                      </Box>

                      {/* Objective Description */}
                      <TextField
                        label="Objective Description (Optional)"
                        fullWidth
                        multiline
                        rows={3}
                        value={objectiveDescription}
                        onChange={(e) =>
                          setObjectiveDescription(e.target.value)
                        }
                        inputProps={{ maxLength: 500 }}
                        helperText={`${objectiveDescription.length}/500 characters`}
                      />

                      <Box
                        sx={{
                          display: "flex",
                          justifyContent: "flex-end",
                          mt: 2,
                        }}
                      >
                        <Button
                          variant="outlined"
                          onClick={handleSaveObjectiveDetails}
                          disabled={updating}
                        >
                          {updating ? "Saving..." : "Save Objective Details"}
                        </Button>
                      </Box>
                    </Box>
                  </CardContent>
                </Card>
              </Box>
            </TabPanel>

            {/* Tab 1: Entities */}
            <TabPanel value={activeTab} index={1}>
              <Box sx={{ p: 3 }}>
                <Typography variant="h6" gutterBottom>
                  System Design Criteria
                </Typography>
                <Alert severity="info" sx={{ mt: 2 }}>
                  <Typography variant="body2">
                    This is a placeholder for the system design criteria view.
                    The actual implementation will display extracted information
                    from the scenario analysis.
                  </Typography>
                </Alert>
              </Box>
            </TabPanel>

            {/* Tab 2: Cost Estimate */}
            <TabPanel value={activeTab} index={2}>
              <Box sx={{ p: 3 }}>
                <Typography variant="h6" gutterBottom>
                  Cost Estimate
                </Typography>
                <Alert severity="info" sx={{ mt: 2 }}>
                  <Typography variant="body2">
                    This is a placeholder for the cost estimate view. The actual
                    implementation will display cost estimation results from the
                    scenario analysis.
                  </Typography>
                </Alert>
              </Box>
            </TabPanel>

            {/* Tab 3: Report */}
            <TabPanel value={activeTab} index={3}>
              <Box sx={{ p: 3 }}>
                <Typography variant="h6" gutterBottom>
                  Scenario Report
                </Typography>
                <Alert severity="info" sx={{ mt: 2 }}>
                  <Typography variant="body2">
                    This is a placeholder for the scenario report view. The
                    actual implementation will display the generated markdown
                    report for this scenario.
                  </Typography>
                </Alert>
              </Box>
            </TabPanel>
          </Paper>
        </>
      ) : (
        <Alert severity="warning">Scenario not found</Alert>
      )}
    </Box>
  );
};

export default ScenarioDetails;
