import React from "react";
import { useDispatch, useSelector } from "react-redux";
import {
  Box,
  Paper,
  Typography,
  Button,
  CircularProgress,
  Alert,
  FormControlLabel,
  Switch,
} from "@mui/material";
import { PlayArrow as RunIcon } from "@mui/icons-material";
import {
  prepareCostEstimation,
  selectCostEstimationLoading,
  selectScenarioError,
} from "../../../redux/scenarioSlice";

const CostEstimationStatus = ({ scenario }) => {
  const dispatch = useDispatch();
  const loading = useSelector((state) =>
    selectCostEstimationLoading(state, scenario.id)
  );
  const error = useSelector(selectScenarioError);
  const [generateEstimates, setGenerateEstimates] = React.useState(false);

  const handlePrepareCostEstimation = async () => {
    try {
      await dispatch(
        prepareCostEstimation({
          scenarioId: scenario.id,
          generateEstimates,
        })
      ).unwrap();
    } catch (err) {
      console.error("Failed to prepare cost estimation:", err);
    }
  };

  return (
    <Paper sx={{ p: 3 }}>
      <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <Box>
          <Typography variant="h6" gutterBottom>
            Cost Estimation Status
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {scenario.cost_estimation
              ? `Cost estimation prepared on ${new Date(scenario.cost_estimation.prepared_timestamp).toLocaleString()}`
              : "No cost estimation data available"}
          </Typography>
        </Box>
        <Box sx={{ display: "flex", flexDirection: "column", gap: 1, alignItems: "flex-end" }}>
          <FormControlLabel
            control={
              <Switch
                checked={generateEstimates}
                onChange={(e) => setGenerateEstimates(e.target.checked)}
                size="small"
              />
            }
            label="Generate Estimates"
          />
          <Button
            variant="contained"
            startIcon={loading ? <CircularProgress size={16} /> : <RunIcon />}
            onClick={handlePrepareCostEstimation}
            disabled={loading || !scenario.analysis}
          >
            {loading ? "Preparing..." : "Prepare Cost Data"}
          </Button>
        </Box>
      </Box>
      {error && (
        <Alert severity="error" sx={{ mt: 2 }}>
          {error}
        </Alert>
      )}
      {!scenario.analysis && (
        <Alert severity="warning" sx={{ mt: 2 }}>
          Analysis must be completed before cost estimation can be prepared.
        </Alert>
      )}
    </Paper>
  );
};

export default CostEstimationStatus;

