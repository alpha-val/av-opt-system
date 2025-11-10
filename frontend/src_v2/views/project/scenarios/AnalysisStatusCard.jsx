import React from "react";
import { useDispatch, useSelector } from "react-redux";
import {
  Box,
  Paper,
  Typography,
  Button,
  CircularProgress,
  Alert,
} from "@mui/material";
import { PlayArrow as RunIcon } from "@mui/icons-material";
import {
  analyzeScenario,
  selectAnalysisLoading,
  selectScenarioError,
} from "../../../redux/scenarioSlice";

const AnalysisStatusCard = ({ scenario }) => {
  const dispatch = useDispatch();
  const loading = useSelector((state) =>
    selectAnalysisLoading(state, scenario.id)
  );
  const error = useSelector(selectScenarioError);

  const handleRunAnalysis = async () => {
    try {
      await dispatch(analyzeScenario(scenario.id)).unwrap();
    } catch (err) {
      console.error("Failed to analyze scenario:", err);
    }
  };

  return (
    <Paper sx={{ p: 3 }}>
      <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <Box>
          <Typography variant="h6" gutterBottom>
            Analysis Status
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {scenario.analysis
              ? `Analysis completed on ${new Date(scenario.analysis.analysis_timestamp).toLocaleString()}`
              : "No analysis has been run yet"}
          </Typography>
        </Box>
        <Button
          variant="contained"
          startIcon={loading ? <CircularProgress size={16} /> : <RunIcon />}
          onClick={handleRunAnalysis}
          disabled={loading}
        >
          {loading ? "Analyzing..." : scenario.analysis ? "Re-analyze" : "Run Analysis"}
        </Button>
      </Box>
      {error && (
        <Alert severity="error" sx={{ mt: 2 }}>
          {error}
        </Alert>
      )}
    </Paper>
  );
};

export default AnalysisStatusCard;

