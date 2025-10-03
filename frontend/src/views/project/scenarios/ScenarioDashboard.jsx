import React, { useState, useEffect } from "react";
import { useParams } from "react-router-dom";
import {
  Box,
  Button,
  Grid,
  Card,
  CardContent,
  CardActions,
  Typography,
  Chip,
  IconButton,
  Menu,
  MenuItem,
  Breadcrumbs,
  Link,
} from "@mui/material";
import {
  Add as AddIcon,
  MoreVert as MoreVertIcon,
  TrendingUp,
  AttachMoney,
  Speed,
  NavigateNext as NavigateNextIcon,
} from "@mui/icons-material";
import CreateScenarioDialog from "./CreateScenarioDialog";
import ScenarioDetail from "./ScenarioDetails";
import { useDispatch, useSelector } from "react-redux";
import { fetchScenarios, deleteScenario } from "../../../redux/scenarioSlice";

const Scenarios = () => {
  const { projectId } = useParams();
  const dispatch = useDispatch();

  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [menuAnchor, setMenuAnchor] = useState(null);
  const [selectedScenario, setSelectedScenario] = useState(null);
  const [activeScenarioId, setActiveScenarioId] = useState(null);

  const scenarios = useSelector(
    (state) => state.scenarios.byProject[projectId] || []
  );
  const loading = useSelector((state) => state.scenarios.loading);
  const activeScenario = useSelector(
    (state) => state.scenarios?.byId?.[activeScenarioId]
  );

  useEffect(() => {
    console.log(
      "[ScenarioDashboard] Fetching scenarios for project:",
      projectId
    );
    if (projectId) {
      dispatch(fetchScenarios(projectId));
    }
  }, [projectId, dispatch]);

  const handleMenuClick = (event, scenario) => {
    event.stopPropagation();
    setMenuAnchor(event.currentTarget);
    setSelectedScenario(scenario);
  };

  const handleMenuClose = () => {
    setMenuAnchor(null);
    setSelectedScenario(null);
  };

  const handleDelete = () => {
    if (selectedScenario) {
      dispatch(deleteScenario(selectedScenario.id));
      handleMenuClose();
      // If viewing the deleted scenario, go back to list
      if (activeScenarioId === selectedScenario.id) {
        setActiveScenarioId(null);
      }
    }
  };

  const handleCardClick = (scenarioId) => {
    setActiveScenarioId(scenarioId);
  };

  const handleBackToList = () => {
    setActiveScenarioId(null);
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

  // Show scenario detail view
  if (activeScenarioId) {
    return (
      <Box sx={{ p: 0 }}>
        {/* Breadcrumb Navigation */}
        <Box sx={{ mb: 3 }}>
          <Breadcrumbs
            separator={<NavigateNextIcon fontSize="small" />}
            aria-label="breadcrumb"
          >
            <Link
              component="button"
              variant="h6"
              underline="none"
              color={"primary.main"}
              onClick={handleBackToList}
              sx={{
                cursor: "pointer",
                "&:hover": { color: "primary.main" },
              }}
            >
              All Scenarios
            </Link>
            <Typography variant="h6" color="text.primary">
              {activeScenario?.name || "Loading..."}
            </Typography>
          </Breadcrumbs>
        </Box>

        {/* Scenario Detail Component */}
        <ScenarioDetail
          scenarioId={activeScenarioId}
          projectId={projectId}
          onClose={handleBackToList}
        />
      </Box>
    );
  }

  // Show scenario list view (default)
  return (
    <Box sx={{ p: 0 }}>
      {/* Header */}
      <Box
        sx={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          mb: 3,
        }}
      >
        <Typography variant="h4">Scenarios</Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => setCreateDialogOpen(true)}
        >
          Add Scenario
        </Button>
      </Box>

      {/* Empty State */}
      {scenarios.length === 0 && !loading ? (
        <Box
          sx={{
            textAlign: "center",
            py: 8,
            px: 2,
            bgcolor: "grey.50",
            borderRadius: 2,
            border: "2px dashed",
            borderColor: "grey.300",
          }}
        >
          <Typography variant="h6" color="text.secondary" gutterBottom>
            No scenarios yet
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            Create your first scenario to explore different options
          </Typography>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => setCreateDialogOpen(true)}
          >
            Create Scenario
          </Button>
        </Box>
      ) : (
        /* Scenario Cards Grid */
        <Grid container spacing={3}>
          {scenarios.map((scenario) => (
            <Grid xs={12} sm={6} md={4} key={scenario.id}>
              <Card
                sx={{
                  cursor: "pointer",
                  "&:hover": { boxShadow: 4 },
                  transition: "box-shadow 0.3s",
                  height: "100%",
                  display: "flex",
                  flexDirection: "column",
                }}
                onClick={() => handleCardClick(scenario.id)}
              >
                <CardContent sx={{ flexGrow: 1 }}>
                  <Box
                    sx={{
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "flex-start",
                      mb: 2,
                    }}
                  >
                    <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                      {getGoalIcon(scenario.goal)}
                      <Typography variant="h6" component="div">
                        {scenario.name}
                      </Typography>
                    </Box>
                    <IconButton
                      size="small"
                      onClick={(e) => handleMenuClick(e, scenario)}
                    >
                      <MoreVertIcon />
                    </IconButton>
                  </Box>

                  <Typography
                    variant="body2"
                    color="text.secondary"
                    sx={{ mb: 2 }}
                  >
                    {scenario.description || "No description"}
                  </Typography>

                  <Box sx={{ mb: 2 }}>
                    <Chip
                      label={scenario.status}
                      color={getStatusColor(scenario.status)}
                      size="small"
                      sx={{ mr: 1 }}
                    />
                    <Chip
                      label={scenario.change_type}
                      variant="outlined"
                      size="small"
                    />
                  </Box>

                  {scenario.target && (
                    <Typography variant="body2" sx={{ mb: 1 }}>
                      <strong>Target:</strong> {scenario.target.metric}{" "}
                      {scenario.target.value > 0 ? "+" : ""}
                      {scenario.target.value}
                      {scenario.target.unit}
                    </Typography>
                  )}

                  {scenario.option_count !== undefined && (
                    <Typography variant="body2" color="primary">
                      <strong>{scenario.option_count}</strong> option
                      {scenario.option_count !== 1 ? "s" : ""} generated
                    </Typography>
                  )}
                </CardContent>

                <CardActions>
                  <Button
                    size="small"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleCardClick(scenario.id);
                    }}
                  >
                    View Details
                  </Button>
                </CardActions>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}

      {/* Context Menu */}
      <Menu
        anchorEl={menuAnchor}
        open={Boolean(menuAnchor)}
        onClose={handleMenuClose}
      >
        <MenuItem
          onClick={() => {
            // TODO: Add edit functionality
            handleMenuClose();
          }}
        >
          Edit
        </MenuItem>
        <MenuItem
          onClick={() => {
            // TODO: Add duplicate logic
            handleMenuClose();
          }}
        >
          Duplicate
        </MenuItem>
        <MenuItem onClick={handleDelete}>Delete</MenuItem>
      </Menu>

      {/* Create Dialog */}
      <CreateScenarioDialog
        open={createDialogOpen}
        onClose={() => setCreateDialogOpen(false)}
        projectId={projectId}
      />
    </Box>
  );
};

export default Scenarios;
