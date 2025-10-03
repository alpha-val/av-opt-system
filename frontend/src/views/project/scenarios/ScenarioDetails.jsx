import React, { useEffect, useState, useMemo } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useDispatch, useSelector } from "react-redux";
import {
  Box,
  Paper,
  Typography,
  Button,
  Chip,
  Grid,
  Card,
  CardContent,
  Breadcrumbs,
  Link,
  Tabs,
  Tab,
  IconButton,
  Menu,
  MenuItem,
  Alert,
  CircularProgress,
} from "@mui/material";
import {
  ArrowBack,
  Add as AddIcon,
  MoreVert as MoreVertIcon,
  TrendingUp,
  AttachMoney,
  Speed,
  Edit as EditIcon,
  Delete as DeleteIcon,
} from "@mui/icons-material";
import {
  fetchScenario,
  updateScenario,
  deleteScenario,
} from "../../../redux/scenarioSlice";
import { fetchOptions } from "../../../redux/optionSlice";
import OptionsTable from "./options/OptionsTabularView";
import OptionComparisonView from "./options/OptionsComparisonView";
import CreateOptionDialog from "./options/CreateOptionDialog";

const ScenarioDetail = () => {
  const { projectId, scenarioId } = useParams();
  const navigate = useNavigate();
  const dispatch = useDispatch();

  const [activeTab, setActiveTab] = useState(0);
  const [menuAnchor, setMenuAnchor] = useState(null);
  const [createOptionDialogOpen, setCreateOptionDialogOpen] = useState(false);

  const scenario = useSelector((state) => state.scenarios?.byId?.[scenarioId]);
  const options = useSelector(
    (state) => state.options?.byScenario?.[scenarioId] || []
  );
  const loading = useSelector((state) => state.scenarios?.loading || false);
  const error = useSelector((state) => state.scenarios?.error);

  useEffect(() => {
    if (scenarioId) {
      dispatch(fetchScenario(scenarioId));
      dispatch(fetchOptions(scenarioId));
    }
  }, [scenarioId, dispatch]);

  const handleBack = () => {
    navigate(`/projects/${projectId}/scenarios`);
  };

  const handleMenuClick = (event) => {
    setMenuAnchor(event.currentTarget);
  };

  const handleMenuClose = () => {
    setMenuAnchor(null);
  };

  const handleEdit = () => {
    // TODO: Open edit dialog
    handleMenuClose();
  };

  const handleDelete = () => {
    if (window.confirm("Are you sure you want to delete this scenario?")) {
      dispatch(deleteScenario(scenarioId));
      handleMenuClose();
      navigate(`/projects/${projectId}/scenarios`);
    }
  };

  const handleAnalyze = () => {
    dispatch(
      updateScenario({
        scenarioId,
        updates: { status: "analyzing", compute_state: "queued" },
      })
    );
    // TODO: Trigger backend analysis
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

  const selectedOption = useMemo(() => {
    return options.find((opt) => opt.selected);
  }, [options]);

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
      <Box sx={{ p: 3 }}>
        <Alert severity="warning">Scenario not found</Alert>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ mb: 3 }}>
        {/* Breadcrumbs */}
        <Breadcrumbs sx={{ mb: 2 }}>
          <Link
            component="button"
            variant="body2"
            onClick={() => navigate("/projects")}
            sx={{ textDecoration: "none" }}
          >
            Projects
          </Link>
          <Link
            component="button"
            variant="body2"
            onClick={() => navigate(`/projects/${projectId}`)}
            sx={{ textDecoration: "none" }}
          >
            Project
          </Link>
          <Link
            component="button"
            variant="body2"
            onClick={handleBack}
            sx={{ textDecoration: "none" }}
          >
            Scenarios
          </Link>
          <Typography color="text.primary">{scenario.name}</Typography>
        </Breadcrumbs>

        {/* Title and Actions */}
        <Box
          sx={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
          }}
        >
          <Box sx={{ display: "flex", alignItems: "center", gap: 2 }}>
            <IconButton onClick={handleBack}>
              <ArrowBack />
            </IconButton>
            <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
              {getGoalIcon(scenario.goal)}
              <Typography variant="h4">{scenario.name}</Typography>
            </Box>
          </Box>
          <Box sx={{ display: "flex", gap: 1 }}>
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={() => setCreateOptionDialogOpen(true)}
            >
              Add Option
            </Button>
            {scenario.status === "draft" && options.length === 0 && (
              <Button
                variant="outlined"
                onClick={handleAnalyze}
                disabled={scenario.compute_state === "running"}
              >
                {scenario.compute_state === "running"
                  ? "Analyzing..."
                  : "Generate Options"}
              </Button>
            )}
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

      {/* Overview Cards */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        {/* Scenario Info */}
        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Scenario Overview
            </Typography>

            <Box sx={{ mb: 2 }}>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Description
              </Typography>
              <Typography variant="body1">
                {scenario.description || "No description provided"}
              </Typography>
            </Box>

            <Grid container spacing={2}>
              <Grid item xs={6} sm={3}>
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
              <Grid item xs={6} sm={3}>
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
              <Grid item xs={6} sm={3}>
                <Typography variant="body2" color="text.secondary">
                  Goal
                </Typography>
                <Typography variant="body1" sx={{ mt: 0.5 }}>
                  {scenario.goal.replace(/_/g, " ")}
                </Typography>
              </Grid>
              <Grid item xs={6} sm={3}>
                <Typography variant="body2" color="text.secondary">
                  Options
                </Typography>
                <Typography variant="body1" sx={{ mt: 0.5 }}>
                  {scenario.option_count || options.length}
                </Typography>
              </Grid>
            </Grid>
          </Paper>
        </Grid>

        {/* Target and Constraints */}
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 3, height: "100%" }}>
            <Typography variant="h6" gutterBottom>
              Target & Constraints
            </Typography>

            <Box sx={{ mb: 2 }}>
              <Typography variant="body2" color="text.secondary">
                Target
              </Typography>
              <Typography variant="body1" sx={{ fontWeight: 600 }}>
                {scenario.target.metric}: {scenario.target.value > 0 ? "+" : ""}
                {scenario.target.value}
                {scenario.target.unit}
              </Typography>
            </Box>

            {scenario.constraints && (
              <>
                {scenario.constraints.budget_capex && (
                  <Box sx={{ mb: 1 }}>
                    <Typography variant="body2" color="text.secondary">
                      Budget (CAPEX)
                    </Typography>
                    <Typography variant="body1">
                      ${scenario.constraints.budget_capex.toLocaleString()}
                    </Typography>
                  </Box>
                )}
                {scenario.constraints.timeline_months && (
                  <Box sx={{ mb: 1 }}>
                    <Typography variant="body2" color="text.secondary">
                      Timeline
                    </Typography>
                    <Typography variant="body1">
                      {scenario.constraints.timeline_months} months
                    </Typography>
                  </Box>
                )}
                {scenario.constraints.use_existing_equipment_only && (
                  <Chip
                    label="Use existing equipment only"
                    size="small"
                    color="info"
                    sx={{ mt: 1 }}
                  />
                )}
              </>
            )}
          </Paper>
        </Grid>
      </Grid>

      {/* Selected Option Summary */}
      {selectedOption && (
        <Alert severity="info" sx={{ mb: 3 }}>
          <Typography variant="body2">
            <strong>Selected Option:</strong> {selectedOption.name}
            {selectedOption.estimates?.capex && (
              <>
                {" "}
                • CAPEX: $
                {selectedOption.estimates.capex.value.toLocaleString()}
              </>
            )}
            {selectedOption.estimates?.opex_per_year && (
              <>
                {" "}
                • OPEX/year: $
                {selectedOption.estimates.opex_per_year.value.toLocaleString()}
              </>
            )}
          </Typography>
        </Alert>
      )}

      {/* Tabs */}
      <Paper sx={{ mb: 3 }}>
        <Tabs value={activeTab} onChange={(e, v) => setActiveTab(v)}>
          <Tab label={`Options (${options.length})`} />
          <Tab label="Comparison" disabled={options.length < 2} />
          <Tab label="Analysis" disabled={options.length === 0} />
        </Tabs>
      </Paper>

      {/* Tab Content */}
      {activeTab === 0 && (
        <OptionsTable
          options={options}
          scenarioId={scenarioId}
          onAddOption={() => setCreateOptionDialogOpen(true)}
        />
      )}
      {activeTab === 1 && options.length >= 2 && (
        // <OptionComparisonView options={options} />
        <div>Comparison view coming soon...</div>
      )}
      {activeTab === 2 && options.length > 0 && (
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>
            Cost Analysis
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Analysis features coming soon...
          </Typography>
        </Paper>
      )}

      {/* Create Option Dialog */}
      <CreateOptionDialog
        open={createOptionDialogOpen}
        onClose={() => setCreateOptionDialogOpen(false)}
        scenarioId={scenarioId}
        scenario={scenario}
      />
    </Box>
  );
};

export default ScenarioDetail;
