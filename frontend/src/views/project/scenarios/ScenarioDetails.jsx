import React, { useEffect, useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import {
  Box,
  Paper,
  Typography,
  Button,
  Chip,
  Grid,
  Tabs,
  Tab,
  IconButton,
  Menu,
  MenuItem,
  Alert,
  CircularProgress,
  TextField,
  FormControl,
  InputLabel,
  Select,
} from "@mui/material";
import {
  TrendingUp,
  AttachMoney,
  Speed,
  Edit as EditIcon,
  Delete as DeleteIcon,
  MoreVert as MoreVertIcon,
} from "@mui/icons-material";
import {
  fetchScenario,
  analyzeScenario,
  deleteScenario,
} from "../../../redux/scenarioSlice";

const ScenarioDetail = ({
  scenarioId,
  scenario: initialScenario,
  projectId,
  onClose,
}) => {
  const dispatch = useDispatch();

  const [activeTab, setActiveTab] = useState(0);
  const [menuAnchor, setMenuAnchor] = useState(null);
  const [goal, setGoal] = useState("");
  const [description, setDescription] = useState("");
  const [changeType, setChangeType] = useState("");

  const scenario =
    useSelector((state) => state.scenarios?.byId?.[scenarioId]) ||
    initialScenario;
  const costEstimate = useSelector(
    (state) => state.scenarios?.costEstimates?.[scenarioId]
  );
  const loading = useSelector((state) => state.scenarios?.loading || false);
  const analyzing = useSelector((state) => state.scenarios?.analyzing || false);
  const error = useSelector((state) => state.scenarios?.error);

  const isAnalyzing =
    analyzing ||
    scenario?.status === "analyzing" ||
    scenario?.compute_state === "running" ||
    scenario?.compute_state === "queued";

  console.log("[ScenarioDetails] scenario:", scenario);
  console.log("[ScenarioDetails] costEstimate:", costEstimate);
  console.log("[ScenarioDetails] isAnalyzing:", isAnalyzing);

  useEffect(() => {
    if (scenarioId && !initialScenario) {
      dispatch(fetchScenario(scenarioId));
    }
  }, [scenarioId, initialScenario, dispatch]);

  useEffect(() => {
    if (scenario) {
      setGoal(scenario.goal || "");
      setDescription(scenario.description || "");
      setChangeType(scenario.change_type || "");
    }
  }, [scenario]);

  const handleMenuClick = (event) => {
    setMenuAnchor(event.currentTarget);
  };

  const handleMenuClose = () => {
    setMenuAnchor(null);
  };

  const handleEdit = () => {
    handleMenuClose();
  };

  const handleDelete = () => {
    if (window.confirm("Are you sure you want to delete this scenario?")) {
      dispatch(deleteScenario(scenarioId));
      handleMenuClose();
      if (onClose) onClose();
    }
  };

  const handleGoalChange = (event) => {
    setGoal(event.target.value);
  };

  const handleDescriptionChange = (event) => {
    setDescription(event.target.value);
  };

  const handleChangeTypeChange = (event) => {
    setChangeType(event.target.value);
  };

  const handleAnalyze = async () => {
    const updates = {};

    if (description && description.trim() !== scenario.description) {
      updates.description = description;
    }

    if (goal && goal !== scenario.goal) {
      updates.goal = goal;
    }

    if (changeType && changeType !== scenario.change_type) {
      updates.change_type = changeType;
    }

    try {
      await dispatch(
        analyzeScenario({
          scenarioId,
          updates: Object.keys(updates).length > 0 ? updates : null,
        })
      ).unwrap();

      console.log("[ScenarioDetails] Analysis triggered successfully");
    } catch (err) {
      console.error("[ScenarioDetails] Failed to trigger analysis:", err);
    }
  };

  const getGoalIcon = (goal) => {
    switch (goal) {
      case "increase_production":
        return <TrendingUp />;
      case "reduce_cost":
        return <AttachMoney />;
      default:
        return <Speed />;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case "ready":
        return "success";
      case "analyzing":
        return "warning";
      case "draft":
        return "default";
      case "archived":
        return "error";
      default:
        return "default";
    }
  };

  if (loading && !scenario) {
    return (
      <Box
        sx={{
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          minHeight: 400,
        }}
      >
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error">{error}</Alert>
      </Box>
    );
  }

  if (!scenario) {
    return (
      <Box sx={{ p: 0 }}>
        <Alert severity="warning">Scenario not found</Alert>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 0 }}>
      {/* Header */}
      <Box sx={{ mb: 3 }}>
        {/* Title and Actions */}
        <Box
          sx={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
          }}
        >
          <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
            {getGoalIcon(scenario.goal)}
            <Typography variant="h4">{scenario.name}</Typography>
          </Box>
          <Box sx={{ display: "flex", gap: 1 }}>
            <Button
              variant="contained"
              onClick={handleAnalyze}
              disabled={isAnalyzing || !description.trim()}
              startIcon={isAnalyzing ? <CircularProgress size={20} /> : null}
            >
              {isAnalyzing ? "Analyzing..." : "Run Analysis"}
            </Button>
            <IconButton onClick={handleMenuClick}>
              <MoreVertIcon />
            </IconButton>
          </Box>
        </Box>

        <Menu
          anchorEl={menuAnchor}
          open={Boolean(menuAnchor)}
          onClose={handleMenuClose}
        >
          <MenuItem onClick={handleEdit}>
            <EditIcon fontSize="small" sx={{ mr: 1 }} />
            Edit Scenario
          </MenuItem>
          <MenuItem onClick={handleDelete}>
            <DeleteIcon fontSize="small" sx={{ mr: 1 }} />
            Delete Scenario
          </MenuItem>
        </Menu>
      </Box>

      {isAnalyzing && (
        <Alert severity="info" sx={{ mb: 3 }}>
          Cost estimation is in progress. This may take a few moments...
        </Alert>
      )}

      {scenario.status === "ready" && scenario.compute_state === "succeeded" && (
        <Alert severity="success" sx={{ mb: 3 }}>
          Analysis completed successfully! View results in the Cost Estimate tab.
        </Alert>
      )}

      {scenario.compute_state === "failed" && (
        <Alert severity="error" sx={{ mb: 3 }}>
          Analysis failed. Please try again or check your inputs.
        </Alert>
      )}

      {/* Overview Cards */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        {/* Scenario Info */}
        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Scenario Overview
            </Typography>

            <Box sx={{ mb: 2 }}>
              <FormControl fullWidth sx={{ mb: 2 }}>
                <InputLabel>What are you trying to achieve?</InputLabel>
                <Select
                  value={goal}
                  onChange={handleGoalChange}
                  label="What are you trying to achieve?"
                  disabled={isAnalyzing}
                >
                  <MenuItem value="increase_production">
                    Increase Production
                  </MenuItem>
                  <MenuItem value="reduce_cost">Reduce Cost</MenuItem>
                  <MenuItem value="improve_quality">Improve Quality</MenuItem>
                  <MenuItem value="change_technology">
                    Change Technology
                  </MenuItem>
                  <MenuItem value="other">Other</MenuItem>
                </Select>
              </FormControl>

              <Typography variant="body2" color="text.secondary" gutterBottom>
                Description
              </Typography>
              <TextField
                fullWidth
                multiline
                rows={6}
                value={description}
                onChange={handleDescriptionChange}
                placeholder="Describe your scenario here. Include goals, changes to make, equipment to add/remove, and any constraints..."
                variant="outlined"
                disabled={isAnalyzing}
                sx={{
                  mb: 2,
                  "& .MuiOutlinedInput-root": {
                    fontFamily: "monospace",
                    fontSize: "0.9rem",
                  },
                }}
              />

              <FormControl fullWidth sx={{ mb: 1 }}>
                <InputLabel>Type of Change</InputLabel>
                <Select
                  value={changeType}
                  onChange={handleChangeTypeChange}
                  label="Type of Change"
                  disabled={isAnalyzing}
                >
                  <MenuItem value="equipment">Equipment</MenuItem>
                  <MenuItem value="process">Process</MenuItem>
                  <MenuItem value="capacity">Capacity</MenuItem>
                  <MenuItem value="location">Location</MenuItem>
                  <MenuItem value="technology">Technology</MenuItem>
                </Select>
              </FormControl>

              <Typography
                variant="caption"
                color="text.secondary"
                sx={{ mt: 1, display: "block" }}
              >
                Edit the fields above and click "Run Analysis" to estimate costs
              </Typography>
            </Box>

            <Grid container spacing={2}>
              <Grid item xs={6} sm={4}>
                <Typography variant="body2" color="text.secondary">
                  Status
                </Typography>
                <Chip
                  label={scenario.status}
                  color={getStatusColor(scenario.status)}
                  size="small"
                  sx={{ mt: 0.5 }}
                />
              </Grid>
              <Grid item xs={6} sm={4}>
                <Typography variant="body2" color="text.secondary">
                  Change Type
                </Typography>
                <Chip
                  label={scenario.change_type}
                  variant="outlined"
                  size="small"
                  sx={{ mt: 0.5 }}
                />
              </Grid>
              <Grid item xs={6} sm={4}>
                <Typography variant="body2" color="text.secondary">
                  Compute State
                </Typography>
                <Chip
                  label={scenario.compute_state || "idle"}
                  variant="outlined"
                  size="small"
                  sx={{ mt: 0.5 }}
                />
              </Grid>
            </Grid>
          </Paper>
        </Grid>
      </Grid>

      {/* Tabs */}
      <Paper sx={{ mb: 3 }}>
        <Tabs value={activeTab} onChange={(e, v) => setActiveTab(v)}>
          <Tab label="Configuration" />
          <Tab label="Cost Estimate" />
          <Tab label="Results" />
        </Tabs>
      </Paper>

      {/* Tab Content */}
      {activeTab === 0 && (
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>
            Scenario Configuration
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Configuration details will be displayed here...
          </Typography>
        </Paper>
      )}

      {activeTab === 1 && (
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>
            Cost Estimate
          </Typography>
          {costEstimate ? (
            <Box>
              <Typography variant="body2" sx={{ mb: 2 }}>
                <strong>Status:</strong> {costEstimate.status}
              </Typography>
              <Typography variant="body2" sx={{ mb: 2 }}>
                <strong>Confidence:</strong> {costEstimate.confidence}
              </Typography>
              <Typography variant="body2" sx={{ mb: 2 }}>
                <strong>Estimated at:</strong> {costEstimate.estimated_at}
              </Typography>
              {costEstimate.cost_breakdown && (
                <Box sx={{ mt: 2 }}>
                  <Typography variant="subtitle1" gutterBottom>
                    Cost Breakdown:
                  </Typography>
                  <pre
                    style={{
                      backgroundColor: "#f5f5f5",
                      padding: "16px",
                      borderRadius: "4px",
                      overflow: "auto",
                    }}
                  >
                    {JSON.stringify(costEstimate.cost_breakdown, null, 2)}
                  </pre>
                </Box>
              )}
            </Box>
          ) : scenario.status === "ready" ? (
            <Typography variant="body2" color="text.secondary">
              Loading cost estimate...
            </Typography>
          ) : (
            <Typography variant="body2" color="text.secondary">
              Run analysis to generate cost estimate
            </Typography>
          )}
        </Paper>
      )}

      {activeTab === 2 && (
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>
            Results
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Results will be displayed here after analysis completes...
          </Typography>
        </Paper>
      )}
    </Box>
  );
};

export default ScenarioDetail;
