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
  Divider,
} from "@mui/material";
import { PlayArrow as PlayArrowIcon, Stop as StopIcon } from "@mui/icons-material";
import {
  ExpandMore as ExpandMoreIcon,
  Input as InputIcon,
  Calculate as CalculateIcon,
} from "@mui/icons-material";
import {
  Add as AddIcon,
  Delete as DeleteIcon,
  ArrowBack as ArrowBackIcon,
} from "@mui/icons-material";
import ObjectiveDetailsForm from "../../components/scenario/ObjectiveDetailsForm";
import AnalysisOptionsForm from "../../components/scenario/AnalysisOptionsForm";
import BaseCaseRecommendationView from "../../components/scenario/BaseCaseRecommendationView";
import LocalObjectiveInputs from "../../components/scenario/LocalObjectiveInputs";
import EntityAttributesWithRecommendations from "../../components/scenario/EntityAttributesWithRecommendations";
import CreateCostEstimateDialog from "../../components/scenario/CreateCostEstimateDialog";
import CalculateCostDialog from "../../components/scenario/CalculateCostDialog";
import CostComparisonReport from "../../components/scenario/CostComparisonReport";
import ProgressWidget from "../../components/common/ProgressWidget";
import { useDialogs } from "../../hooks/useDialogs";
import { useProgress } from "../../hooks/useProgress";
import {
  fetchScenarioById,
  selectCurrentScenario,
  selectScenariosLoading,
  selectScenariosError,
  updateScenario,
  runAnalysis,
  runAnalysisV2,
  runAnalysisV4,
  cancelAnalysisV4,
  selectScenarioRunningAnalysis,
  selectCurrentAnalysisJobId,
  clearError,
  clearAnalysisJobId,
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
import { costEstimateApi, scenarioApi } from "../../services/api";

interface ScenarioDetailsProps {
  scenarioId?: string;
  projectId?: string;
  onBack?: () => void;
}

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
      style={{ height: "100%" }}
    >
      {value === index && <Box sx={{ height: "100%" }}>{children}</Box>}
    </div>
  );
};

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
  const runningAnalysisFromRedux = useSelector(selectScenarioRunningAnalysis);
  const currentAnalysisJobId = useSelector(selectCurrentAnalysisJobId);
  const updating = useSelector((state: any) => state.scenarios.loading.update);
  
  // Connect to WebSocket for progress updates
  const progress = useProgress(currentAnalysisJobId);
  
  // Determine if analysis is running: check Redux state, scenario status, or WebSocket status
  // Analysis is NOT running if WebSocket status is "completed" or "failed"
  const runningAnalysis = useMemo(() => {
    // If WebSocket is connected and reports completed or failed, analysis is definitely not running
    if (progress.connected && (progress.status === "completed" || progress.status === "failed")) {
      return false;
    }
    // If WebSocket is connected and reports in_progress or started, analysis is running
    if (progress.connected && (progress.status === "in_progress" || progress.status === "started")) {
      return true;
    }
    // Otherwise, check Redux state and scenario status (fallback when WebSocket not connected)
    return runningAnalysisFromRedux || scenario?.status === "processing";
  }, [runningAnalysisFromRedux, scenario?.status, progress.status, progress.connected]);
  
  // Track if we've already handled completion to avoid multiple refreshes
  const completionHandledRef = useRef<string | null>(null);
  
  // Refresh scenario data when analysis completes
  useEffect(() => {
    if ((progress.status === "completed" || progress.status === "failed") && 
        currentAnalysisJobId && 
        completionHandledRef.current !== currentAnalysisJobId) {
      // Mark as handled
      completionHandledRef.current = currentAnalysisJobId;
      
      // Refresh scenario to get updated status
      if (scenarioId) {
        dispatch(fetchScenarioById(scenarioId) as any);
      }
      
      // Clear job ID after a short delay to allow UI to update
      setTimeout(() => {
        dispatch(clearAnalysisJobId());
        completionHandledRef.current = null;
      }, 1000);
    }
  }, [progress.status, currentAnalysisJobId, scenarioId, dispatch]);

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
  const [calculateCostDialogOpen, setCalculateCostDialogOpen] = useState(false);
  const [calculating, setCalculating] = useState(false);
  const [entitySelections, setEntitySelections] = useState<Record<string, boolean>>({});

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

  // Workflow options
  const [useV2Workflow, setUseV2Workflow] = useState<boolean>(false);
  const [useV3Workflow, setUseV3Workflow] = useState<boolean>(true);
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
      // Only fetch if scenario is not loaded or ID doesn't match
      if (!scenario || scenario.id !== scenarioId) {
        dispatch(fetchScenarioById(scenarioId) as any);
      }
    }
    if (projectId) {
      // Only fetch if project is not loaded or ID doesn't match
      if (!project || project.id !== projectId) {
        dispatch(fetchProjectById(projectId) as any);
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [scenarioId, projectId]); // Only depend on IDs, not on loaded data

  /**
   * Fetch cost estimates when scenario changes
   */
  useEffect(() => {
    if (scenarioId) {
      dispatch(fetchCostEstimates(scenarioId) as any);
    }
  }, [scenarioId, dispatch]);

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

        // Use separate target and unit fields
        const newTargetValue = scenario.global_objective_target || "";
        const newTargetType = (scenario.global_objective_unit || "%") as "%" | "$" | "tpd" | "gpm";

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
      case ScenarioStatus.CANCELLED:
        return "default";
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

    // Create update payload with separate target and unit
    const updateData: ScenarioUpdate = {
      global_objective_type: formData.type,
      global_objective_target: formData.targetValue,
      global_objective_unit: formData.targetType,
      objective_description: description || undefined,
    };

    // Dispatch update
    dispatch(updateScenario({ scenarioId, data: updateData }) as any).then(
      (result: any) => {
        if (updateScenario.fulfilled.match(result)) {
        } else {
          // console.log(
          //   "[ScenarioDetails] updateScenario rejected",
          //   result.error
          // );
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
   * Handle calculating cost
   */
  const handleCalculateCost = async (data: {
    name: string;
    description?: string;
    topK: number;
  }) => {
    console.log('! ! ! ! ! \n\n Handling calculate cost:', data);
    if (!scenario || !projectId || !scenarioId) {
      return;
    }
    console.log('! ! ! ! ! \n\n Scenario, projectId, scenarioId:', scenario, projectId, scenarioId);
    setCalculating(true);
    try {
      // Get list of selected entities
      const selectedEntities = Object.keys(entitySelections).filter(
        (id) => entitySelections[id] !== false
      );

      if (selectedEntities.length === 0) {
        alert("Please select at least one entity to calculate costs");
        return;
      }

      // Call the cost estimation API
      const result = await costEstimateApi.calculateCost({
        scenario_description: data.description || `Cost estimate for ${scenario.name}`,
        project_id: projectId,
        scenario_id: scenarioId,
        selected_entities: selectedEntities,
        entity_selection_state: entitySelections,
        top_k: data.topK,
      });

      // Create a cost estimate record with the calculated data
      const costEstimateData: CostEstimateCreate = {
        name: data.name,
        description: data.description,
        scenario_id: scenarioId,
      };
      
      await dispatch(createCostEstimate(costEstimateData) as any);
      
      // Refresh cost estimates list
      await dispatch(fetchCostEstimates(scenarioId) as any);
      
      // Close dialog and switch to Cost Estimates tab
      setCalculateCostDialogOpen(false);
      setActiveTab(2);
    } catch (error) {
      console.error("Failed to calculate cost:", error);
      alert("Failed to calculate cost. Please try again.");
    } finally {
      setCalculating(false);
    }
  };

  /**
   * Handle entity selection change from EntityAttributesWithRecommendations
   */
  const handleEntitySelectionChange = useCallback(
    (selections: Record<string, boolean>) => {
      setEntitySelections(selections);
    },
    []
  );

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
      scenario.global_objective_target !== objectiveForm.targetValue ||
      scenario.global_objective_unit !== objectiveForm.targetType
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

    // Dispatch run analysis action (V3, V2, or V1)
    if (useV3Workflow) {
      // console.log('[ScenarioDetails] Starting V3 analysis for scenario:', scenarioId);
      // console.log('[ScenarioDetails] useV3Workflow is:', useV3Workflow);
      const result = await dispatch(runAnalysisV4(scenarioId) as any);
      // console.log('[ScenarioDetails] runAnalysisV4 result:', result);
      // console.log('[ScenarioDetails] runAnalysisV4 result type:', result.type);
      if (runAnalysisV4.fulfilled.match(result)) {
        // console.log('[ScenarioDetails] Analysis started successfully, payload:', result.payload);
        // console.log('[ScenarioDetails] analysisResult from payload:', result.payload?.analysisResult);
        // console.log('[ScenarioDetails] job_id from analysisResult:', result.payload?.analysisResult?.job_id);
      } else if (runAnalysisV4.rejected.match(result)) {
        // console.error('[ScenarioDetails] Analysis failed:', result.payload);
        setAnalysisError(result.payload as string);
      } else {
        // console.warn('[ScenarioDetails] Unexpected result type:', result.type);
      }
    } else if (useV2Workflow) {
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
            <Box sx={{ mr: 6 }}>
              <Button onClick={onBack} sx={{ textTransform: "none" }}>
                ← Back to All Scenarios
              </Button>
            </Box>
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

      {/* Progress Widget - Show when analysis is running */}
      {currentAnalysisJobId && runningAnalysis && (
        <Box sx={{ mb: 2, px: 0 }}>
          <ProgressWidget
            jobId={currentAnalysisJobId}
            title="Scenario Analysis Progress"
            onDismiss={() => {
              dispatch(clearAnalysisJobId());
            }}
          />
        </Box>
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
        <Box sx={{ p: 0 }}>
          {/* Scenario Info Panel */}
          {/* <Paper elevation={0} sx={{ p: 1, mb: 3, backgroundColor: "#f9f9f9" }}>
            <Typography variant="h4" component="h1" gutterBottom>
              {scenario.name} ID: {scenario.id}
            </Typography>
            {scenario.description && (
              <Typography variant="body1" color="text.secondary" gutterBottom>
                Description:{" "}
                {scenario.description || "No description available"}
              </Typography>
            )}
          </Paper> */}

          {/* Tabbed Interface */}
          <Paper
            elevation={0}
            sx={{
              flex: 1,
              display: "flex",
              flexDirection: "row",
              minHeight: "600px",
              p: 0,
            }}
          >
            {/* Left Side: Vertical Tabs */}
            <Box
              sx={{
                borderRight: 1,
                borderColor: "divider",
                minWidth: 200,
                backgroundColor: (theme) =>
                  theme.palette.mode === "dark"
                    ? "rgba(255, 255, 255, 0.05)"
                    : "rgba(0, 0, 0, 0.02)",
              }}
            >
              <Tabs
                value={activeTab}
                orientation="vertical"
                onChange={(_, newValue) => setActiveTab(newValue)}
                aria-label="scenario details tabs"
                sx={{
                  "& .MuiTab-root": {
                    fontSize: "small",
                    alignItems: "flex-start",
                    textAlign: "left",
                    minHeight: 48,
                    paddingLeft: 2,
                  },
                }}
              >
                <Tab label="Objectives" id="scenario-tab-0" />
                <Tab label="System Design" id="scenario-tab-1" />
                <Tab label="Cost Estimates" id="scenario-tab-2" />
                <Tab label="Report" id="scenario-tab-3" />
              </Tabs>
            </Box>

            {/* Right Side: Tab Content */}
            <Box sx={{ flex: 1, overflow: "auto", ml: 2 }}>
              <Box sx={{ p: 2, pb: 0, pt: 0, mb: 2 }}>
                <Typography variant="h6">Scenario Details</Typography>
                <Typography variant="body1" color="text.secondary">
                  {scenario.global_objective_type} by{" "}
                  {scenario.global_objective_target}
                  {scenario.global_objective_unit}
                </Typography>
              </Box>
              <Divider />
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
                    <Box sx={{ display: "flex", gap: 1 }}>
                      {runningAnalysis && currentAnalysisJobId && (
                        <Tooltip title="Cancel running analysis" arrow>
                          <Button
                            variant="outlined"
                            color="error"
                            size="small"
                            startIcon={<StopIcon />}
                            onClick={async () => {
                              if (currentAnalysisJobId && scenarioId) {
                                try {
                                  // cancelAnalysisV4 already fetches and updates the scenario
                                  await dispatch(
                                    cancelAnalysisV4({
                                      scenarioId,
                                      jobId: currentAnalysisJobId,
                                    }) as any
                                  );
                                  // Clear job ID after cancellation
                                  dispatch(clearAnalysisJobId());
                                } catch (error) {
                                  console.error("Failed to cancel analysis:", error);
                                  // Clear job ID even on error
                                  dispatch(clearAnalysisJobId());
                                }
                              }
                            }}
                            disabled={!currentAnalysisJobId}
                          >
                            Cancel Analysis
                          </Button>
                        </Tooltip>
                      )}
                      <Tooltip title={getRunAnalysisTooltip()} arrow>
                        <span>
                          <Button
                            variant="contained"
                            color="primary"
                            size="small"
                            startIcon={
                              runningAnalysis ? (
                                <CircularProgress size={20} color="inherit" />
                              ) : (
                                <PlayArrowIcon />
                              )
                            }
                            onClick={handleRunAnalysis}
                            disabled={runningAnalysis || !canRunAnalysis()}
                          >
                            {runningAnalysis ? "Running..." : "Run Analysis"}
                          </Button>
                        </span>
                      </Tooltip>
                    </Box>
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
                    disabled={runningAnalysis}
                  />

                  {/* <AnalysisOptionsForm
                    useV2Workflow={useV2Workflow}
                    extractSummary={extractSummary}
                    onUseV2WorkflowChange={setUseV2Workflow}
                    onExtractSummaryChange={setExtractSummary}
                  /> */}
                </Box>
              </TabPanel>

              {/* Tab 1: System Design */}
              <TabPanel value={activeTab} index={1}>
                <Box sx={{ p: 3 }}>
                  <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", mb: 2 }}>
                    <Typography variant="h6" gutterBottom>
                      Base Case Entities with Recommendations
                    </Typography>
                    <Button
                      variant="contained"
                      color="primary"
                      startIcon={<CalculateIcon />}
                      onClick={() => setCalculateCostDialogOpen(true)}
                      disabled={Object.keys(entitySelections).length === 0}
                    >
                      Calculate Cost
                    </Button>
                  </Box>
                  <EntityAttributesWithRecommendations
                    scenarioId={scenarioId || ""}
                    globalObjectiveType={scenarioObjectiveType}
                    globalObjectiveTarget={scenarioObjectiveTarget}
                    globalObjectiveUnit={scenario?.global_objective_unit}
                    onEntitySelectionChange={handleEntitySelectionChange}
                  />
                </Box>
              </TabPanel>

              {/* Tab 2: Cost Estimate */}
              <TabPanel value={activeTab} index={2}>
                <Box sx={{ p: 3 }}>
                  {selectedCostEstimateId && currentCostEstimate ? (
                    /* Cost Estimate Details View */
                    <Box>
                      {/* Back Button */}
                      <Box sx={{ mb: 2 }}>
                        <Button
                          startIcon={<ArrowBackIcon />}
                          size="small"
                          onClick={() => {
                            setSelectedCostEstimateId(null);
                            dispatch(clearCurrentCostEstimate());
                          }}
                        >
                          Back to All Cost Estimates
                        </Button>
                      </Box>

                      {/* Cost Estimate Header */}
                      <Paper elevation={0} sx={{ p: 3, mb: 2 }}>
                        <Box
                          sx={{
                            display: "flex",
                            justifyContent: "space-between",
                            alignItems: "flex-start",
                            gap: 2,
                          }}
                        >
                          {/* Left: Cost Estimate Info */}
                          <Box sx={{ flex: 1, minWidth: 0 }}>
                            {/* Title and Description */}
                            <Typography variant="h5" gutterBottom>
                              {currentCostEstimate.name}
                            </Typography>
                            {currentCostEstimate.description && (
                              <Typography
                                variant="body1"
                                color="text.secondary"
                                sx={{ mb: 2 }}
                              >
                                {currentCostEstimate.description}
                              </Typography>
                            )}

                            {/* Scenario Objective */}
                            {scenario?.global_objective_target && (
                              <Box
                                sx={{
                                  display: "flex",
                                  flexDirection: "row",
                                  gap: 1,
                                  alignItems: "center",
                                  mb: 2,
                                  p: 1,
                                  borderRadius: 1,
                                  bgcolor: (theme) =>
                                    theme.palette.mode === "dark"
                                      ? "rgba(255, 255, 255, 0.05)"
                                      : "rgba(0, 0, 0, 0.02)",
                                }}
                              >
                                <Typography
                                  variant="body2"
                                  color="text.secondary"
                                >
                                  Scenario Objective:
                                </Typography>
                                <Typography variant="body2" fontWeight="medium">
                                  {scenario?.global_objective_type}
                                </Typography>
                                <Typography
                                  variant="body2"
                                  color="text.secondary"
                                >
                                  by
                                </Typography>
                                <Typography variant="body2" fontWeight="medium">
                                  {scenario?.global_objective_target}
                                </Typography>
                              </Box>
                            )}

                            {/* Metadata */}
                            <Typography
                              variant="caption"
                              color="text.secondary"
                            >
                              Created:{" "}
                              {formatDate(currentCostEstimate.created_at)} |{" "}
                              Updated:{" "}
                              {formatDate(currentCostEstimate.updated_at)}
                            </Typography>
                          </Box>

                          {/* Right: Actions */}
                          <Box
                            sx={{
                              display: "flex",
                              flexDirection: "column",
                              alignItems: "flex-end",
                              gap: 1,
                            }}
                          >
                            <Button
                              variant="contained"
                              size="small"
                              startIcon={<CalculateIcon />}
                            >
                              Calculate Cost Estimate
                            </Button>
                            <IconButton
                              color="error"
                              size="small"
                              onClick={() =>
                                handleDeleteCostEstimate(currentCostEstimate.id)
                              }
                              disabled={deletingCostEstimate}
                            >
                              <DeleteIcon />
                            </IconButton>
                          </Box>
                        </Box>
                      </Paper>

                      {/* Step 1: System Design Inputs */}
                      <Accordion sx={{ backgroundColor: "#f9f9f9", mb: 1 }}>
                        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                          <InputIcon sx={{ mr: 1 }} />
                          <Box>
                            <Typography variant="h6" gutterBottom>
                              Local Objective Inputs
                            </Typography>
                            <Typography variant="body2" color="text.secondary">
                              Configure attribute types and review redesign
                              values based on global objective target.
                            </Typography>
                          </Box>
                        </AccordionSummary>
                        <AccordionDetails>
                          <Box sx={{ mb: 4 }}>
                            <LocalObjectiveInputs
                              scenarioId={scenarioId || ""}
                              globalObjectiveType={
                                scenario?.global_objective_type
                              }
                              globalObjectiveTarget={
                                scenario?.global_objective_target
                              }
                              globalObjectiveUnit={
                                scenario?.global_objective_unit
                              }
                              costEstimateId={
                                selectedCostEstimateId || undefined
                              }
                            />
                          </Box>
                        </AccordionDetails>
                      </Accordion>

                      {/* Step 2: Cost Comparison Report */}
                      <Accordion sx={{ backgroundColor: "#f9f9f9", mb: 1 }}>
                        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                          <CalculateIcon sx={{ mr: 1 }} />
                          <Box>
                            <Typography variant="h6" gutterBottom>
                              Cost Comparison Report
                            </Typography>
                            <Typography variant="body2" color="text.secondary">
                              Compare base case costs with matching tabular entity costs.
                            </Typography>
                          </Box>
                        </AccordionSummary>
                        <AccordionDetails>
                          <Box sx={{ mb: 2 }}>
                            <CostComparisonReport
                              reportData={
                                currentCostEstimate?.metadata?.cost_comparison_report || []
                              }
                            />
                          </Box>
                        </AccordionDetails>
                      </Accordion>
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
                          sx={{
                            display: "flex",
                            justifyContent: "center",
                            p: 4,
                          }}
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
                                    Created:{" "}
                                    {formatDate(costEstimate.created_at)}
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

                  {/* Calculate Cost Dialog */}
                  <CalculateCostDialog
                    open={calculateCostDialogOpen}
                    onClose={() => setCalculateCostDialogOpen(false)}
                    onCalculate={handleCalculateCost}
                    calculating={calculating}
                    defaultName={scenario?.name ? `${scenario.name} - Cost Estimate` : ""}
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
            </Box>
          </Paper>
        </Box>
      ) : (
        <Alert severity="warning">Scenario not found</Alert>
      )}
    </Box>
  );
};

export default ScenarioDetails;
