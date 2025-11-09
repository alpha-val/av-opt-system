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
  resizeSystem,
  selectResizingLoading,
  selectScenarioError,
} from "../../../redux/scenarioSlice";

const ResizingStatusCard = ({ scenario }) => {
  const dispatch = useDispatch();
  const loading = useSelector((state) =>
    selectResizingLoading(state, scenario.id)
  );
  const error = useSelector(selectScenarioError);

  const handleApplyResizing = async () => {
    try {
      await dispatch(
        resizeSystem({ scenarioId: scenario.id, userConstraints: [] })
      ).unwrap();
    } catch (err) {
      console.error("Failed to resize system:", err);
    }
  };

  return (
    <Paper sx={{ p: 3 }}>
      <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <Box>
          <Typography variant="h6" gutterBottom>
            Resizing Status
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {scenario.resizing
              ? `Resizing completed on ${new Date(scenario.resizing.resizing_timestamp).toLocaleString()}`
              : "No resizing has been applied yet"}
          </Typography>
        </Box>
        <Button
          variant="contained"
          startIcon={loading ? <CircularProgress size={16} /> : <RunIcon />}
          onClick={handleApplyResizing}
          disabled={loading || !scenario.analysis}
        >
          {loading ? "Resizing..." : "Apply Resizing"}
        </Button>
      </Box>
      {error && (
        <Alert severity="error" sx={{ mt: 2 }}>
          {error}
        </Alert>
      )}
      {!scenario.analysis && (
        <Alert severity="warning" sx={{ mt: 2 }}>
          Analysis must be completed before resizing can be applied.
        </Alert>
      )}
    </Paper>
  );
};

export default ResizingStatusCard;

