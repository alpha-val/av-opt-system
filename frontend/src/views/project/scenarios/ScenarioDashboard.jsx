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
import AssignmentOutlinedIcon from "@mui/icons-material/AssignmentOutlined";
import CreateScenarioDialog from "./CreateScenarioDialog";
import ScenarioDetail from "./ScenarioDetails";
import { useDispatch, useSelector } from "react-redux";
import { fetchScenarios, deleteScenario } from "../../../redux/scenarioSlice";
import { useDialogs } from "../../../hooks/useDialogs/useDialogs";

const Scenarios = () => {
  const { projectId } = useParams();
  const dispatch = useDispatch();
  const dialogs = useDialogs();

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

  const handleDelete = async () => {
    if (selectedScenario) {
      const confirmed = await dialogs.confirm(
        `Are you sure you want to delete scenario "${selectedScenario.name}"? This action cannot be undone.`,
        {
          title: "Delete Scenario",
          okText: "Delete",
          cancelText: "Cancel",
          severity: "error",
          warningMsg:
            "Deleting a scenario will remove all associated data and cannot be undone.",
        }
      );

      if (confirmed) {
        try {
          await dispatch(deleteScenario(selectedScenario.id)).unwrap();

          // Clear active scenario if it was deleted
          if (activeScenarioId === selectedScenario.id) {
            setActiveScenarioId(null);
          }

          console.log(
            "[ScenarioDashboard] Scenario deleted:",
            selectedScenario.id
          );
        } catch (error) {
          console.error(
            "[ScenarioDashboard] Failed to delete scenario:",
            error
          );

          // Show error message
          await dialogs.alert(
            `Failed to delete scenario: ${error.message || "Unknown error"}`,
            {
              title: "Delete Failed",
              okText: "OK",
            }
          );
        }
      }

      handleMenuClose();
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
      <Box sx={{ p: 0, minHeight: "100%" }}>
        {/* Breadcrumb Navigation */}
        <Box
          sx={{
            mb: 3,
            display: "flex",
            justifyContent: "start",
            alignItems: "center",
            gap: 2,
          }}
        >
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
            <Box
              sx={{
                display: "flex",
                alignItems: "center",
                gap: 1,
              }}
            >
              <AssignmentOutlinedIcon fontSize="small" color="action" />
              <Typography variant="h6" color="text.primary">
                {activeScenario?.name || "Loading..."}
              </Typography>
            </Box>
          </Breadcrumbs>
          <Box>
            <Typography variant="body2" color="text.secondary">
              Updated{" "}
              {new Date(activeScenario?.updated_at).toLocaleDateString()}
            </Typography>
          </Box>
        </Box>

        {/* Scenario Detail Component */}
        <ScenarioDetail
          scenarioId={activeScenarioId}
          scenario={activeScenario}
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
          justifyContent: "flex-start",
          alignItems: "center",
          gap: 2,
          mb: 3,
        }}
      >
        <Typography variant="h4">Scenarios</Typography>
        {scenarios.length > 0 && (
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => setCreateDialogOpen(true)}
          >
            Add Scenario
          </Button>
        )}
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
            Create your first scenario to explore different configurations
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
