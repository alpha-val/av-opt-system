import React, { useState, useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import {
  Box,
  Tabs,
  Tab,
  Paper,
  Typography,
  CircularProgress,
  Alert,
  Button,
  IconButton,
} from "@mui/material";
import {
  ArrowBack as BackIcon,
  Edit as EditIcon,
} from "@mui/icons-material";
import {
  fetchScenarioWithAnalysis,
  selectCurrentScenario,
  selectScenariosLoading,
  selectScenarioError,
} from "../../../redux/scenarioSlice";

// Import tab content components (will be created)
import OverviewTab from "./tabs/OverviewTab";
import AnalysisTab from "./tabs/AnalysisTab";
import ResizingTab from "./tabs/ResizingTab";
import RecommendationsTab from "./tabs/RecommendationsTab";
import CostEstimationTab from "./tabs/CostEstimationTab";
import ReportTab from "./tabs/ReportTab";

const ScenarioDetails = ({ scenarioId, onBack, onEdit }) => {
  const dispatch = useDispatch();
  const scenario = useSelector(selectCurrentScenario);
  const loading = useSelector(selectScenariosLoading);
  const error = useSelector(selectScenarioError);
  const [activeTab, setActiveTab] = useState(0);

  useEffect(() => {
    if (scenarioId) {
      dispatch(fetchScenarioWithAnalysis(scenarioId));
    }
  }, [dispatch, scenarioId]);

  const handleTabChange = (event, newValue) => {
    setActiveTab(newValue);
  };

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

  if (!scenario) {
    return (
      <Alert severity="info" sx={{ mb: 2 }}>
        Scenario not found
      </Alert>
    );
  }

  return (
    <Box>
      {/* Header */}
      <Box sx={{ display: "flex", alignItems: "center", mb: 3 }}>
        {onBack && (
          <IconButton onClick={onBack} sx={{ mr: 1 }}>
            <BackIcon />
          </IconButton>
        )}
        <Typography variant="h5" sx={{ flexGrow: 1 }}>
          {scenario.name}
        </Typography>
        {onEdit && (
          <Button
            startIcon={<EditIcon />}
            onClick={() => onEdit(scenario)}
            variant="outlined"
            size="small"
          >
            Edit
          </Button>
        )}
      </Box>

      {/* Description */}
      {scenario.description && (
        <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
          {scenario.description}
        </Typography>
      )}

      {/* Tabs */}
      <Paper elevation={0} sx={{ borderBottom: 1, borderColor: "divider" }}>
        <Tabs value={activeTab} onChange={handleTabChange}>
          <Tab label="Overview" />
          <Tab label="Analysis" />
          <Tab label="Resizing" />
          <Tab label="Recommendations" />
          <Tab label="Cost Estimation" />
          <Tab label="Report" />
        </Tabs>
      </Paper>

      {/* Tab Content */}
      <Box sx={{ mt: 3 }}>
        {activeTab === 0 && <OverviewTab scenario={scenario} />}
        {activeTab === 1 && <AnalysisTab scenario={scenario} />}
        {activeTab === 2 && <ResizingTab scenario={scenario} />}
        {activeTab === 3 && <RecommendationsTab scenario={scenario} />}
        {activeTab === 4 && <CostEstimationTab scenario={scenario} />}
        {activeTab === 5 && <ReportTab scenario={scenario} />}
      </Box>
    </Box>
  );
};

export default ScenarioDetails;

