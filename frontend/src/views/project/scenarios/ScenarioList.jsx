import React, { useMemo, useState, useCallback, useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import {
  Box,
  Typography,
  Chip,
  Menu,
  MenuItem,
  ListItemIcon,
  ListItemText,
  IconButton,
  Button,
  TextField,
  InputAdornment,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  CircularProgress,
  Alert,
} from "@mui/material";
import {
  Delete as DeleteIcon,
  Edit as EditIcon,
  Visibility as ViewIcon,
  PlayArrow as RunIcon,
  MoreVert as MoreVertIcon,
  Search as SearchIcon,
  FilterList as FilterIcon,
  Add as AddIcon,
} from "@mui/icons-material";
import {
  fetchScenariosByProject,
  deleteScenario,
  selectScenariosByProject,
  selectScenariosLoading,
  selectScenarioError,
  clearError,
} from "../../../redux/scenarioSlice";
import { useDialogs } from "../../../hooks/useDialogs/useDialogs";

const ScenarioList = ({ projectId, onViewScenario, onCreateScenario, onEditScenario }) => {
  const dispatch = useDispatch();
  const dialogs = useDialogs();
  const scenarios = useSelector((state) => selectScenariosByProject(state, projectId));
  const loading = useSelector(selectScenariosLoading);
  const error = useSelector(selectScenarioError);
  const [contextMenu, setContextMenu] = useState(null);
  const [selectedScenario, setSelectedScenario] = useState(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");

  // Fetch scenarios on mount
  useEffect(() => {
    if (projectId) {
      dispatch(fetchScenariosByProject(projectId));
    }
  }, [dispatch, projectId]);

  // Clear error after display
  useEffect(() => {
    if (error) {
      const timer = setTimeout(() => {
        dispatch(clearError());
      }, 5000);
      return () => clearTimeout(timer);
    }
  }, [error, dispatch]);

  const handleOptionsClick = useCallback((event, scenario) => {
    event.preventDefault();
    event.stopPropagation();
    setSelectedScenario(scenario);
    setContextMenu({ mouseX: event.clientX + 2, mouseY: event.clientY - 6 });
  }, []);

  const handleContextMenuClose = useCallback(() => {
    setContextMenu(null);
    setSelectedScenario(null);
  }, []);

  const handleDeleteScenario = useCallback(async () => {
    const scenarioToDelete = selectedScenario;
    handleContextMenuClose();
    await new Promise((resolve) => setTimeout(resolve, 200));
    if (!scenarioToDelete) return;
    
    const confirm = await dialogs.confirm(
      "Delete Scenario",
      `Are you sure you want to delete the scenario "${scenarioToDelete?.name}"? This action cannot be undone.`
    );
    if (!confirm) return;

    const result = await dispatch(deleteScenario(scenarioToDelete.id));
    if (deleteScenario.fulfilled.match(result)) {
      console.log("Scenario deleted successfully");
    } else {
      console.error("Failed to delete scenario:", result.payload);
    }
  }, [selectedScenario, handleContextMenuClose, dispatch, dialogs]);

  const handleViewScenario = useCallback((scenario) => {
    if (onViewScenario) {
      onViewScenario(scenario);
    }
  }, [onViewScenario]);

  const handleEditScenario = useCallback((scenario) => {
    handleContextMenuClose();
    if (onEditScenario) {
      onEditScenario(scenario);
    }
  }, [onEditScenario, handleContextMenuClose]);

  // Format date for display
  const formatDate = (dateString) => {
    if (!dateString) return "N/A";
    const date = new Date(dateString);
    const options = {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    };
    return date.toLocaleString("en-US", options);
  };

  // Get status chip
  const getStatusChip = (status) => {
    const statusConfig = {
      draft: { color: "default", label: "Draft" },
      analyzing: { color: "info", label: "Analyzing" },
      ready: { color: "success", label: "Ready" },
      archived: { color: "default", label: "Archived" },
    };
    const config = statusConfig[status] || { color: "default", label: status };
    return (
      <Chip
        label={config.label}
        size="small"
        color={config.color}
        variant="outlined"
      />
    );
  };

  // Get goal type display
  const getGoalTypeDisplay = (globalObjective) => {
    if (!globalObjective) return "N/A";
    const goalType = globalObjective.goal_type || "";
    return goalType
      .split("_")
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
      .join(" ");
  };

  // Filter scenarios
  const filteredScenarios = useMemo(() => {
    let filtered = scenarios;

    // Filter by search term
    if (searchTerm) {
      const term = searchTerm.toLowerCase();
      filtered = filtered.filter(
        (scenario) =>
          scenario.name?.toLowerCase().includes(term) ||
          scenario.description?.toLowerCase().includes(term) ||
          getGoalTypeDisplay(scenario.global_objective).toLowerCase().includes(term)
      );
    }

    // Filter by status
    if (statusFilter !== "all") {
      filtered = filtered.filter((scenario) => scenario.status === statusFilter);
    }

    return filtered;
  }, [scenarios, searchTerm, statusFilter]);

  if (loading.fetch) {
    return (
      <Box sx={{ display: "flex", justifyContent: "center", p: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ mb: 2 }}>
        {error}
      </Alert>
    );
  }

  if (scenarios.length === 0) {
    return (
      <Box sx={{ mt: 3, textAlign: "center", py: 4 }}>
        <Typography variant="body1" color="text.secondary" gutterBottom>
          No scenarios created yet.
        </Typography>
        {onCreateScenario && (
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={onCreateScenario}
            sx={{ mt: 2 }}
          >
            Create Scenario
          </Button>
        )}
      </Box>
    );
  }

  return (
    <Box sx={{ mt: 3 }}>
      {/* Header and Filters */}
      <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", mb: 2 }}>
        <Typography variant="h6">
          Scenarios ({filteredScenarios.length})
        </Typography>
        {onCreateScenario && (
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={onCreateScenario}
            size="small"
          >
            Create Scenario
          </Button>
        )}
      </Box>

      {/* Search and Filter */}
      <Box sx={{ display: "flex", gap: 2, mb: 2 }}>
        <TextField
          placeholder="Search scenarios..."
          size="small"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <SearchIcon />
              </InputAdornment>
            ),
          }}
          sx={{ flexGrow: 1 }}
        />
        <TextField
          select
          size="small"
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          SelectProps={{
            native: true,
          }}
          sx={{ minWidth: 150 }}
        >
          <option value="all">All Status</option>
          <option value="draft">Draft</option>
          <option value="analyzing">Analyzing</option>
          <option value="ready">Ready</option>
          <option value="archived">Archived</option>
        </TextField>
      </Box>

      {/* Scenarios Table */}
      <TableContainer component={Paper} variant="outlined">
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Name</TableCell>
              <TableCell>Goal</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Created</TableCell>
              <TableCell>Updated</TableCell>
              <TableCell align="right">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {filteredScenarios.map((scenario) => (
              <TableRow
                key={scenario.id}
                hover
                sx={{ cursor: "pointer" }}
                onClick={() => handleViewScenario(scenario)}
              >
                <TableCell>
                  <Typography variant="body2" fontWeight={500}>
                    {scenario.name}
                  </Typography>
                  {scenario.description && (
                    <Typography variant="caption" color="text.secondary" display="block">
                      {scenario.description.substring(0, 60)}
                      {scenario.description.length > 60 ? "..." : ""}
                    </Typography>
                  )}
                </TableCell>
                <TableCell>
                  {getGoalTypeDisplay(scenario.global_objective)}
                </TableCell>
                <TableCell>{getStatusChip(scenario.status)}</TableCell>
                <TableCell>{formatDate(scenario.created_at)}</TableCell>
                <TableCell>{formatDate(scenario.updated_at)}</TableCell>
                <TableCell align="right" onClick={(e) => e.stopPropagation()}>
                  <IconButton
                    size="small"
                    onClick={(e) => handleOptionsClick(e, scenario)}
                  >
                    <MoreVertIcon />
                  </IconButton>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Context Menu */}
      <Menu
        open={contextMenu !== null}
        onClose={handleContextMenuClose}
        anchorReference="anchorPosition"
        anchorPosition={
          contextMenu !== null
            ? { top: contextMenu.mouseY, left: contextMenu.mouseX }
            : undefined
        }
      >
        <MenuItem onClick={() => handleViewScenario(selectedScenario)}>
          <ListItemIcon>
            <ViewIcon fontSize="small" />
          </ListItemIcon>
          <ListItemText>View Details</ListItemText>
        </MenuItem>
        <MenuItem onClick={() => handleEditScenario(selectedScenario)}>
          <ListItemIcon>
            <EditIcon fontSize="small" />
          </ListItemIcon>
          <ListItemText>Edit</ListItemText>
        </MenuItem>
        <MenuItem
          onClick={handleDeleteScenario}
          disabled={loading.delete}
          sx={{
            color: "error.main",
            "&:hover": {
              backgroundColor: "error.light",
            },
          }}
        >
          <ListItemIcon>
            <DeleteIcon fontSize="small" sx={{ color: "inherit" }} />
          </ListItemIcon>
          <ListItemText>
            {loading.delete ? "Deleting..." : "Delete"}
          </ListItemText>
        </MenuItem>
      </Menu>
    </Box>
  );
};

export default ScenarioList;

