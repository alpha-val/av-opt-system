import React, { useEffect, useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import {
  Box,
  Paper,
  Typography,
  Button,
  Chip,
  Grid,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Divider,
  Card,
  CardContent,
  CircularProgress,
  Alert,
  IconButton,
  Tabs,
  Tab,
} from "@mui/material";
import {
  PlayArrow,
  Assessment,
  CheckCircle,
  TrendingUp,
  AttachMoney,
  Close as CloseIcon,
  Warning as WarningIcon,
} from "@mui/icons-material";
import {
  fetchScenario,
  analyzeScenario,
  updateScenario,
  fetchCostEstimate,
} from "../../../redux/scenarioSlice";
import { useDialogs } from "../../../hooks/useDialogs/useDialogs";
import BaseCaseDetails from "../../../components/BaseCaseDetails";
import {
  fetchProjectEntitiesRelations,
  selectEntitiesByProject,
} from "../../../redux/dataSlice";
import CostEstimateJSON from "./CostEstimateJSON";
import CostDetails from "./CostDetails";
import CostBasisOptions from "./CostBasisOptions";

const ScenarioDetail = ({
  scenarioId,
  scenario: initialScenario,
  projectId,
  onClose,
}) => {
  const dispatch = useDispatch();
  const dialogs = useDialogs();

  // Redux selectors
  const scenario =
    useSelector((state) => state.scenarios.byId[scenarioId]) || initialScenario;

  // Get all entities for the current project, sorted by type then name
  const rawEntities =
    useSelector((state) => selectEntitiesByProject(state, projectId)) || [];

  const entities = React.useMemo(() => {
    return [...rawEntities].sort((a, b) => {
      const typeA = a.type || "Unknown";
      const typeB = b.type || "Unknown";
      if (typeA !== typeB) {
        return typeA.localeCompare(typeB);
      }
      const nameA = a.properties?.name || a.name || "Unnamed Entity";
      const nameB = b.properties?.name || b.name || "Unnamed Entity";
      return nameA.localeCompare(nameB);
    });
  }, [rawEntities]);

  const costEstimate = useSelector(
    (state) => state.scenarios.costEstimates[scenarioId]
  );

  const analyzing = useSelector((state) => state.scenarios.analyzing);
  const loading = useSelector((state) => state.scenarios.loading);

  // Form state
  const [name, setName] = useState(scenario?.name || "");
  const [description, setDescription] = useState(scenario?.description || "");
  const [goal, setGoal] = useState(scenario?.goal || "increase_production");
  const [changeType, setChangeType] = useState(
    scenario?.change_type || "equipment"
  );

  // Tab state
  const [tabIndex, setTabIndex] = useState(0);

  // Track selected entities from BaseCaseTable
  const [selectedEntities, setSelectedEntities] = useState([]);

  useEffect(() => {
    if (scenarioId) {
      dispatch(fetchScenario(scenarioId));
      dispatch(fetchCostEstimate(scenarioId));
    }
  }, [scenarioId, dispatch]);

  useEffect(() => {
    if (scenario) {
      setName(scenario.name || "");
      setDescription(scenario.description || "");
      setGoal(scenario.goal || "increase_production");
      setChangeType(scenario.change_type || "equipment");
    }
  }, [scenario]);

  useEffect(() => {
    if (projectId) {
      dispatch(
        fetchProjectEntitiesRelations({ projectId, include_metadata: true })
      );
    }
  }, [dispatch, projectId]);

  const handleRunAnalysis = async () => {
    try {
      await dispatch(
        analyzeScenario({
          scenarioId,
          updates: {
            name,
            description,
            goal,
            change_type: changeType,
            selected_entities: selectedEntities.map((e) => e.id),
          },
        })
      ).unwrap();
    } catch (error) {
      console.error("[ScenarioDetails] Analysis failed:", error);
      await dialogs.alert(
        `Failed to run analysis: ${error.message || "Unknown error"}`,
        {
          title: "Analysis Failed",
          okText: "OK",
        }
      );
    }
  };

  const formatCurrency = (value) => {
    if (value == null) return "N/A";
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  const formatDate = (dateString) => {
    if (!dateString) return "N/A";
    return new Date(dateString).toLocaleString();
  };

  const getConfidenceColor = (confidence) => {
    switch (confidence) {
      case "high":
        return "success";
      case "medium":
        return "warning";
      case "low":
        return "error";
      default:
        return "default";
    }
  };

  const hasCostData = (costObj) => {
    if (!costObj) return false;
    return Object.values(costObj).some((value) => value !== null);
  };

  if (!scenario && loading) {
    return (
      <Box
        sx={{
          minHeight: "100vh",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        <CircularProgress />
      </Box>
    );
  }

  if (!scenario) {
    return (
      <Box
        sx={{
          minHeight: "100vh",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        <Alert severity="error">Scenario not found</Alert>
      </Box>
    );
  }

  // Callback to handle entity selection from BaseCaseTable
  const handleEntitySelection = (entities) => {
    setSelectedEntities(entities);
  };

  return (
    <Box sx={{ minHeight: "100vh", display: "flex", flexDirection: "column" }}>
      {/* Main Content */}
      <Box sx={{ flex: 1, p: 0 }}>
        <Grid container spacing={3} sx={{ height: "100%" }}>
          {/* Column 2: Tabs for Base Case and Cost Estimates */}
          <Grid item xs={12} md={9.6}>
            <Paper sx={{ p: 3, height: "100%" }}>
              <Tabs
                value={tabIndex}
                onChange={(_, newValue) => setTabIndex(newValue)}
                sx={{ mb: 2 }}
              >
                <Tab label="Base Case" />
                <Tab label="Options" />
              </Tabs>

              {/* Tab 1: Base Case */}
              {tabIndex === 0 && (
                <Grid xs={12} md={2.4}>
                  <Paper
                    elevation={0}
                    sx={{
                      p: 3,
                      height: "100%",
                      display: "flex",
                      flexDirection: "row",
                      gap: 3,
                      backgroundColor: "#f9f9f9",
                    }}
                  >
                    <Box>
                      <Typography variant="h6" gutterBottom>
                        Scenario Settings
                      </Typography>
                      <Divider sx={{ mb: 2 }} />

                      <Box
                        sx={{
                          flex: 1,
                          display: "flex",
                          flexDirection: "column",
                          gap: 2,
                        }}
                      >
                        <TextField
                          fullWidth
                          label="Scenario Name"
                          value={name}
                          onChange={(e) => setName(e.target.value)}
                          size="small"
                        />

                        <TextField
                          fullWidth
                          multiline
                          rows={3}
                          label="Description"
                          value={description}
                          onChange={(e) => setDescription(e.target.value)}
                          size="small"
                          helperText="Describe what you want to change"
                        />

                        <FormControl fullWidth size="small">
                          <InputLabel>Goal</InputLabel>
                          <Select
                            value={goal}
                            onChange={(e) => setGoal(e.target.value)}
                            label="Goal"
                          >
                            <MenuItem value="increase_production">
                              Increase Production
                            </MenuItem>
                            <MenuItem value="reduce_capex">Reduce Cost</MenuItem>
                            <MenuItem value="improve_quality">
                              Improve Quality
                            </MenuItem>
                            <MenuItem value="change_technology">
                              Change Technology
                            </MenuItem>
                          </Select>
                        </FormControl>

                        <FormControl fullWidth size="small">
                          <InputLabel>Change Type</InputLabel>
                          <Select
                            value={changeType}
                            onChange={(e) => setChangeType(e.target.value)}
                            label="Change Type"
                          >
                            <MenuItem value="equipment">Equipment</MenuItem>
                            <MenuItem value="process">Process</MenuItem>
                            <MenuItem value="capacity">Capacity</MenuItem>
                            <MenuItem value="location">Location</MenuItem>
                          </Select>
                        </FormControl>

                        <Box>
                          <Typography
                            variant="caption"
                            color="text.secondary"
                            gutterBottom
                          >
                            Status
                          </Typography>
                          <Box sx={{ mt: 0.5 }}>
                            <Chip
                              label={scenario.status}
                              color={
                                scenario.status === "ready"
                                  ? "success"
                                  : "default"
                              }
                              size="small"
                            />
                          </Box>
                        </Box>

                        {/* Run Analysis Button */}
                        <Button
                          fullWidth
                          variant="contained"
                          size="medium"
                          startIcon={
                            analyzing ? (
                              <CircularProgress size={20} color="inherit" />
                            ) : (
                              <PlayArrow />
                            )
                          }
                          onClick={handleRunAnalysis}
                          disabled={analyzing || selectedEntities.length === 0}
                          sx={{ mt: 1 }}
                        >
                          {analyzing ? "Analyzing..." : "Run Analysis"}
                        </Button>
                      </Box>
                    </Box>
                    <Box>
                      <Typography variant="h6" gutterBottom>
                        Base Case Entities
                      </Typography>
                      <Divider sx={{ mb: 2 }} />
                      <BaseCaseDetails
                        entities={entities || []}
                        cbEntitySelection={handleEntitySelection}
                      />
                    </Box>
                  </Paper>
                </Grid>
              )}

              {/* Tab 2: Options */}
              {tabIndex === 1 && (
                <Box>
                  <CostBasisOptions data={costEstimate} />
                </Box>
              )}
            </Paper>
          </Grid>
        </Grid>
      </Box>
    </Box>
  );
};

export default ScenarioDetail;
