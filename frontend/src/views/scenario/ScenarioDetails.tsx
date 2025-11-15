import React, {
  useEffect,
  useState,
  useRef,
  useMemo,
  useCallback,
} from "react";
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
  Tooltip,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Grid,
  Card,
  CardContent,
  IconButton,
} from "@mui/material";
import SummarizeOutlinedIcon from "@mui/icons-material/SummarizeOutlined";
import ChecklistOutlinedIcon from "@mui/icons-material/ChecklistOutlined";
import { ExpandMore as ExpandMoreIcon } from "@mui/icons-material";
import { PlayArrow as PlayArrowIcon } from "@mui/icons-material";
import {
  Add as AddIcon,
  Delete as DeleteIcon,
  ArrowBack as ArrowBackIcon,
} from "@mui/icons-material";
import ObjectiveDetailsForm from "../../components/scenario/ObjectiveDetailsForm";
import AnalysisOptionsForm from "../../components/scenario/AnalysisOptionsForm";
import BaseCaseRecommendationView from "../../components/scenario/BaseCaseRecommendationView";
import LocalObjectives from "../../components/scenario/LocalObjectives";
import CreateCostEstimateDialog from "../../components/scenario/CreateCostEstimateDialog";
import SystemDesignInputs from "../../components/scenario/SystemDesignInputs";
import { useDialogs } from "../../hooks/useDialogs";
import {
  fetchScenarioById,
  selectCurrentScenario,
  selectScenariosLoading,
  selectScenariosError,
  updateScenario,
  runAnalysis,
  runAnalysisV2,
  selectScenarioRunningAnalysis,
  clearError,
} from "../../redux/scenariosSlice";
import {
  fetchCostEstimates,
  fetchCostEstimateById,
  createCostEstimate,
  deleteCostEstimate,
  selectCostEstimatesByScenario,
  selectCurrentCostEstimate,
  selectCostEstimatesLoading,
  selectCostEstimatesError,
  selectCostEstimateCreating,
  selectCostEstimateDeleting,
  clearError as clearCostEstimatesError,
  clearCurrentCostEstimate,
} from "../../redux/costEstimatesSlice";
import {
  fetchProjectById,
  selectCurrentProject,
} from "../../redux/projectsSlice";
import {
  ScenarioStatus,
  ScenarioUpdate,
  CostEstimateCreate,
} from "../../types/api";

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
  const dialogs = useDialogs();

  // Use memoized selectors to prevent unnecessary re-renders
  const scenario = useSelector(selectCurrentScenario);
  const project = useSelector(selectCurrentProject);
  const loading = useSelector(selectScenariosLoading);
  const error = useSelector(selectScenariosError);
  const runningAnalysis = useSelector(selectScenarioRunningAnalysis);
  const updating = useSelector((state: any) => state.scenarios.loading.update);

  // Memoize extracted scenario properties to prevent unnecessary re-renders
  // Only recalculate when the actual scenario data changes, not when object reference changes
  const scenarioIdFromStore = useMemo(() => scenario?.id, [scenario?.id]);
  const scenarioObjectiveType = useMemo(
    () => scenario?.global_objective_type,
    [scenario?.global_objective_type]
  );
  const scenarioObjectiveTarget = useMemo(
    () => scenario?.global_objective_target,
    [scenario?.global_objective_target]
  );
  const scenarioObjectiveDescription = useMemo(
    () => scenario?.objective_description,
    [scenario?.objective_description]
  );
  const [activeTab, setActiveTab] = useState<number>(0);

  // Cost estimate state
  const [createCostEstimateDialogOpen, setCreateCostEstimateDialogOpen] =
    useState(false);
  const [selectedCostEstimateId, setSelectedCostEstimateId] = useState<
    string | null
  >(null);

  // Cost estimates data
  const costEstimatesSelector = useMemo(
    () => (scenarioId ? selectCostEstimatesByScenario(scenarioId) : undefined),
    [scenarioId]
  );
  const costEstimates = useSelector((state: any) =>
    costEstimatesSelector ? costEstimatesSelector(state) : []
  );
  const currentCostEstimate = useSelector(selectCurrentCostEstimate);
  const costEstimatesLoading = useSelector(selectCostEstimatesLoading);
  const costEstimatesError = useSelector(selectCostEstimatesError);
  const creatingCostEstimate = useSelector(selectCostEstimateCreating);
  const deletingCostEstimate = useSelector(selectCostEstimateDeleting);

  // Objective details form state (combined)
  const [objectiveForm, setObjectiveForm] = useState({
    type: "",
    targetValue: "",
    targetType: "%" as "%" | "$",
    description: "",
  });
  const [objectiveError, setObjectiveError] = useState<string | null>(null);
  const [analysisError, setAnalysisError] = useState<string | null>(null);

  // V2 workflow options
  const [useV2Workflow, setUseV2Workflow] = useState<boolean>(true);
  const [extractSummary, setExtractSummary] = useState<boolean>(false);
  const [extractionScope, setExtractionScope] = useState<
    "exact" | "with_relationships" | "with_context"
  >("exact");

  // Track if we've initialized the form to prevent re-initialization
  const formInitializedRef = useRef<string | null>(null);

  /**
   * Fetch scenario and project data
   */
  useEffect(() => {
    if (scenarioId) {
      if (!scenarioIdFromStore || scenarioIdFromStore !== scenarioId) {
        dispatch(fetchScenarioById(scenarioId) as any);
      }
    }
    if (projectId) {
      if (!project || project.id !== projectId) {
        dispatch(fetchProjectById(projectId) as any);
      }
    }
    // Fetch cost estimates for this scenario
    if (scenarioId) {
      dispatch(fetchCostEstimates(scenarioId) as any);
    }
  }, [scenarioId, projectId, scenarioIdFromStore, project?.id, dispatch]);

  /**
   * Initialize form with scenario data when scenario loads
   * Only initializes once per scenario to prevent focus loss
   * Re-initializes when scenario data becomes available after mount
   */
  useEffect(() => {
    // Only initialize when scenario is loaded and matches the route scenarioId
    if (scenario && scenario.id === scenarioId) {
      // Check if we haven't initialized for this scenario yet
      const needsInitialization = formInitializedRef.current !== scenarioId;

      // Also check if form is empty but scenario has data (data loaded after mount)
      const formIsEmpty =
        !objectiveForm.type &&
        !objectiveForm.targetValue &&
        !objectiveForm.description;
      const scenarioHasData =
        scenario.global_objective_type ||
        scenario.global_objective_target ||
        scenario.objective_description;

      if (needsInitialization || (formIsEmpty && scenarioHasData)) {
        const newObjectiveType = scenario.global_objective_type || "";
        const newObjectiveDescription = scenario.objective_description || "";

        // Parse target value and type from global_objective_target
        let newTargetValue = "";
        let newTargetType: "%" | "$" = "%";
        if (scenario.global_objective_target) {
          const match =
            scenario.global_objective_target.match(/^([\d.]+)([%$])$/);
          if (match) {
            newTargetValue = match[1];
            newTargetType = match[2] as "%" | "$";
          } else {
            newTargetValue = scenario.global_objective_target;
          }
        }

        // Set initial values using combined state
        setObjectiveForm({
          type: newObjectiveType,
          targetValue: newTargetValue,
          targetType: newTargetType,
          description: newObjectiveDescription,
        });

        // Mark as initialized for this scenario
        formInitializedRef.current = scenarioId;
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [
    scenarioId,
    scenario?.id,
    scenario?.global_objective_type,
    scenario?.global_objective_target,
    scenario?.objective_description,
  ]);
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
   * Handle objective form field changes
   * Memoized to prevent unnecessary re-renders of ObjectiveDetailsForm
   */
  const handleObjectiveFormChange = useCallback(
    (field: string, value: string | number): void => {
      setObjectiveForm((prev) => ({
        ...prev,
        [field]: value,
      }));
    },
    []
  );

  /**
   * Handle saving objective details
   */
  const handleSaveObjectiveDetails = (data?: {
    localDescription?: string;
    objectiveForm?: any;
  }): void => {
    if (!scenarioId) return;

    setObjectiveError(null);
    dispatch(clearError());

    // Use data from parameter if provided, otherwise use state
    const formData = data?.objectiveForm || objectiveForm;
    const description = data?.localDescription ?? formData.description;

    // Validate objective fields
    if (!formData.type) {
      setObjectiveError("Global objective type is required");
      return;
    }
    if (!formData.targetValue || formData.targetValue.trim().length === 0) {
      setObjectiveError("Global objective target is required");
      return;
    }

    // Build global objective target string
    const globalObjectiveTarget = `${formData.targetValue}${formData.targetType}`;

    // Create update payload
    const updateData: ScenarioUpdate = {
      global_objective_type: formData.type,
      global_objective_target: globalObjectiveTarget,
      objective_description: description || undefined,
    };

    // Dispatch update
    dispatch(updateScenario({ scenarioId, data: updateData }) as any).then(
      (result: any) => {
        if (updateScenario.fulfilled.match(result)) {
        } else {
          console.log(
            "[ScenarioDetails] updateScenario rejected",
            result.error
          );
        }
      }
    );
  };

  /**
   * Check if analysis can be run
   */
  const canRunAnalysis = (): boolean => {
    if (!scenario || !project) return false;

    // Check objective details
    if (
      !objectiveForm.type ||
      !objectiveForm.targetValue ||
      objectiveForm.targetValue.trim().length === 0
    ) {
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

    // if (
    //   !objectiveForm.type ||
    //   !objectiveForm.targetValue ||
    //   objectiveForm.targetValue.trim().length === 0
    // ) {
    //   return "Please complete objective details (type and target)";
    // }

    const hasBaseCaseFiles =
      project.base_case_documents && project.base_case_documents.length > 0;

    if (!hasBaseCaseFiles) {
      return "Base case documents are required. Please upload base case documents in the Sources tab.";
    }

    return "";
  };

  /**
   * Handle creating a new cost estimate
   */
  const handleCreateCostEstimate = (costEstimateData: CostEstimateCreate) => {
    dispatch(createCostEstimate(costEstimateData) as any).then(
      (result: any) => {
        if (createCostEstimate.fulfilled.match(result)) {
          setCreateCostEstimateDialogOpen(false);
        }
      }
    );
  };

  /**
   * Handle deleting a cost estimate
   */
  const handleDeleteCostEstimate = async (costEstimateId: string) => {
    if (!costEstimateId) return;

    // Find cost estimate to show name in warning
    const costEstimateToDelete = costEstimates.find(
      (ce) => ce.id === costEstimateId
    );
    const costEstimateName = costEstimateToDelete?.name || "this cost estimate";

    // Show confirmation dialog
    const confirmed = await dialogs.confirm(
      `Are you sure you want to delete "${costEstimateName}"? This action cannot be undone.`,
      {
        title: "Delete Cost Estimate",
        severity: "error",
        okText: "Delete",
        cancelText: "Cancel",
      }
    );

    if (!confirmed) {
      return;
    }

    dispatch(clearCostEstimatesError());
    dispatch(deleteCostEstimate(costEstimateId) as any).then((result: any) => {
      if (deleteCostEstimate.fulfilled.match(result)) {
        // If we deleted the currently selected cost estimate, clear selection
        if (selectedCostEstimateId === costEstimateId) {
          setSelectedCostEstimateId(null);
          dispatch(clearCurrentCostEstimate());
        }
      }
    });
  };

  /**
   * Handle clicking on a cost estimate card
   */
  const handleCostEstimateClick = (costEstimateId: string) => {
    setSelectedCostEstimateId(costEstimateId);
    dispatch(fetchCostEstimateById(costEstimateId) as any);
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

    if (
      !objectiveForm.type ||
      !objectiveForm.targetValue ||
      objectiveForm.targetValue.trim().length === 0
    ) {
      setAnalysisError(
        "Objective details are required. Please set objective type and target."
      );
      return;
    }

    // Save objective details if they've changed
    if (
      scenario.global_objective_type !== objectiveForm.type ||
      scenario.global_objective_target !==
        `${objectiveForm.targetValue}${objectiveForm.targetType}`
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

    // Dispatch run analysis action (V2 or V1)
    if (useV2Workflow) {
      dispatch(
        runAnalysisV2({
          scenarioId,
          extract_summary: extractSummary,
          extraction_scope: extractionScope,
        }) as any
      ).then((result: any) => {
        if (runAnalysisV2.rejected.match(result)) {
          setAnalysisError(result.payload as string);
        }
      });
    } else {
      dispatch(runAnalysis(scenarioId) as any).then((result: any) => {
        if (runAnalysis.rejected.match(result)) {
          setAnalysisError(result.payload as string);
        }
      });
    }
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
            p: 2,
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
                <Typography color="secondary" sx={{ fontWeight: 600 }}>
                  {scenario.name}
                </Typography>
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
        <Box sx={{ p: 2, pt: 0 }}>
          {/* Scenario Info Panel */}
          <Paper elevation={0} sx={{ p: 1, mb: 3, backgroundColor: "#f9f9f9" }}>
            <Typography variant="h4" component="h1" gutterBottom>
              {scenario.name}  ID: {scenario.id}
            </Typography>
            {scenario.description && (
              <Typography variant="body1" color="text.secondary" gutterBottom>
                Description: {scenario.description || "No description available"}
              </Typography>
            )}
          </Paper>

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
                          : useV2Workflow
                          ? "Run Analysis (V2)"
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

                {/* {!canRunAnalysis() && (
                  <Alert severity="warning" sx={{ mb: 2 }}>
                    {!scenario || !project
                      ? "Scenario or project data not loaded"
                      : !objectiveForm.type ||
                        !objectiveForm.targetValue ||
                        objectiveForm.targetValue.trim().length === 0
                      ? "Please complete objective details (type and target) before running analysis."
                      : "Base case documents are required. Please upload base case documents in the Sources tab before running analysis."}
                  </Alert>
                )} */}

                <ObjectiveDetailsForm
                  objectiveForm={objectiveForm}
                  extractionScope={extractionScope}
                  onChange={handleObjectiveFormChange}
                  onExtractionScopeChange={setExtractionScope}
                  errors={objectiveError}
                  updating={updating}
                  scenarioId={scenarioId || ""}
                  onSave={handleSaveObjectiveDetails}
                />

                <AnalysisOptionsForm
                  useV2Workflow={useV2Workflow}
                  extractSummary={extractSummary}
                  onUseV2WorkflowChange={setUseV2Workflow}
                  onExtractSummaryChange={setExtractSummary}
                />
              </Box>
            </TabPanel>

            {/* Tab 1: System Design */}
            <TabPanel value={activeTab} index={1}>
              <Box sx={{ p: 3 }}>
                <Typography variant="h6" gutterBottom>
                  System Design
                </Typography>

                <Accordion
                  defaultExpanded={false}
                  sx={{ backgroundColor: "#f9f9f9", mb: 2 }}
                >
                  <AccordionSummary
                    expandIcon={<ExpandMoreIcon />}
                    aria-controls="recommendations-content"
                    id="recommendations-header"
                  >
                    <SummarizeOutlinedIcon sx={{ mr: 1 }} />
                    <Typography variant="subtitle1" fontWeight={600}>
                      Base Case Recommendations
                    </Typography>
                  </AccordionSummary>
                  <AccordionDetails>
                    <BaseCaseRecommendationView scenarioId={scenarioId || ""} />
                  </AccordionDetails>
                </Accordion>

                <Accordion
                  defaultExpanded={false}
                  sx={{ backgroundColor: "#f9f9f9", mb: 2 }}
                >
                  <AccordionSummary
                    expandIcon={<ExpandMoreIcon />}
                    aria-controls="system-parameters-content"
                    id="system-parameters-header"
                  >
                    <ChecklistOutlinedIcon sx={{ mr: 1 }} />
                    <Typography variant="subtitle1" fontWeight={600}>
                      System Parameters
                    </Typography>
                  </AccordionSummary>
                  <AccordionDetails>
                    <LocalObjectives scenarioId={scenarioId || ""} />
                  </AccordionDetails>
                </Accordion>
              </Box>
            </TabPanel>

            {/* Tab 2: Cost Estimate */}
            <TabPanel value={activeTab} index={2}>
              <Box sx={{ p: 3 }}>
                {selectedCostEstimateId && currentCostEstimate ? (
                  /* Cost Estimate Details View */
                  <Box>
                    <Box sx={{ display: "flex", alignItems: "center", mb: 3 }}>
                      <Button
                        startIcon={<ArrowBackIcon />}
                        onClick={() => {
                          setSelectedCostEstimateId(null);
                          dispatch(clearCurrentCostEstimate());
                        }}
                        sx={{ mr: 2 }}
                      >
                        Back to Cost Estimates
                      </Button>
                    </Box>

                    <Paper sx={{ p: 3, mb: 2 }}>
                      <Box
                        sx={{
                          display: "flex",
                          justifyContent: "space-between",
                          alignItems: "flex-start",
                          mb: 2,
                        }}
                      >
                        <Box>
                          <Typography variant="h5" gutterBottom>
                            {currentCostEstimate.name}
                          </Typography>
                          {currentCostEstimate.description && (
                            <Typography variant="body1" color="text.secondary">
                              {currentCostEstimate.description}
                            </Typography>
                          )}
                        </Box>
                        <IconButton
                          color="error"
                          onClick={() =>
                            handleDeleteCostEstimate(currentCostEstimate.id)
                          }
                          disabled={deletingCostEstimate}
                        >
                          <DeleteIcon />
                        </IconButton>
                      </Box>
                      <Typography variant="caption" color="text.secondary">
                        Created: {formatDate(currentCostEstimate.created_at)} |
                        Updated: {formatDate(currentCostEstimate.updated_at)}
                      </Typography>
                    </Paper>

                    {/* Step 1: System Design Inputs */}
                    <Box sx={{ mb: 4 }}>
                      <SystemDesignInputs
                        scenarioId={scenarioId || ""}
                        globalObjectiveType={scenario?.global_objective_type}
                        globalObjectiveTarget={
                          scenario?.global_objective_target
                        }
                        costEstimateId={selectedCostEstimateId || undefined}
                      />
                    </Box>
                  </Box>
                ) : (
                  /* Cost Estimates List View */
                  <Box>
                    <Box
                      sx={{
                        display: "flex",
                        justifyContent: "space-between",
                        alignItems: "center",
                        mb: 3,
                      }}
                    >
                      <Typography variant="h6">
                        Cost Estimates ({costEstimates.length})
                      </Typography>
                      <Button
                        variant="contained"
                        startIcon={<AddIcon />}
                        onClick={() => setCreateCostEstimateDialogOpen(true)}
                        disabled={creatingCostEstimate || !scenarioId}
                      >
                        New Cost Estimate
                      </Button>
                    </Box>

                    {costEstimatesError && (
                      <Alert
                        severity="error"
                        sx={{ mb: 2 }}
                        onClose={() => dispatch(clearCostEstimatesError())}
                      >
                        {costEstimatesError}
                      </Alert>
                    )}

                    {costEstimatesLoading.fetch ? (
                      <Box
                        sx={{ display: "flex", justifyContent: "center", p: 4 }}
                      >
                        <CircularProgress />
                      </Box>
                    ) : costEstimates.length === 0 ? (
                      <Alert severity="info">
                        <Typography variant="body2">
                          No cost estimates created yet. Click "New Cost
                          Estimate" to create one.
                        </Typography>
                      </Alert>
                    ) : (
                      <Grid container spacing={2}>
                        {costEstimates.map((costEstimate) => (
                          <Grid
                            item
                            xs={12}
                            sm={6}
                            md={4}
                            key={costEstimate.id}
                          >
                            <Card
                              variant="outlined"
                              sx={{
                                height: "100%",
                                cursor: "pointer",
                                transition: "transform 0.2s, box-shadow 0.2s",
                                "&:hover": {
                                  transform: "translateY(-2px)",
                                  boxShadow: 3,
                                },
                              }}
                              onClick={() =>
                                handleCostEstimateClick(costEstimate.id)
                              }
                            >
                              <CardContent>
                                <Typography
                                  variant="h6"
                                  component="h3"
                                  sx={{ fontWeight: 600, mb: 1 }}
                                >
                                  {costEstimate.name}
                                </Typography>
                                {costEstimate.description && (
                                  <Typography
                                    variant="body2"
                                    color="text.secondary"
                                    sx={{ mb: 2 }}
                                  >
                                    {costEstimate.description}
                                  </Typography>
                                )}
                                <Typography
                                  variant="caption"
                                  color="text.secondary"
                                >
                                  Created: {formatDate(costEstimate.created_at)}
                                </Typography>
                              </CardContent>
                            </Card>
                          </Grid>
                        ))}
                      </Grid>
                    )}
                  </Box>
                )}

                {/* Create Cost Estimate Dialog */}
                <CreateCostEstimateDialog
                  open={createCostEstimateDialogOpen}
                  onClose={() => setCreateCostEstimateDialogOpen(false)}
                  onCreate={handleCreateCostEstimate}
                  creating={creatingCostEstimate}
                  scenarioId={scenarioId || ""}
                />
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
        </Box>
      ) : (
        <Alert severity="warning">Scenario not found</Alert>
      )}
    </Box>
  );
};

export default ScenarioDetails;
