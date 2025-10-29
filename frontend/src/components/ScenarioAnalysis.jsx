import React, { useState, useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import {
  Box,
  TextField,
  Button,
  Typography,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  CircularProgress,
} from "@mui/material";
import ReactJson from "react-json-view";
import { extractScenarioData } from "../redux/scenarioSlice";

const ScenarioAnalysis = ({ scenario, onClose }) => {
  const dispatch = useDispatch();

  // Initialize scenarioDetails state
  const [scenarioDetails, setScenarioDetails] = useState(
    scenario || {
      scenario_type: "increase_production",
      description: "",
      change_type: "capacity",
    }
  );

  const projectId = scenario?.project_id || "";
  const artifactType = "scenario_analysis";
  const userId = scenario?.user_id || "";

  const [file, setFile] = useState(null); // Separate state for the file
  const [submitted, setSubmitted] = useState(false);

  const { loading, result, error } = useSelector(
    (state) => state.scenarios.extraction
  );

  const handleChange = (e) => {
    const { name, value } = e.target;

    setScenarioDetails((prev) => ({
      ...prev,
      [name]: Array.isArray(value) ? value : value, // Ensure multi-select fields are updated as arrays
    }));
  };

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
  };

  const handleSubmit = async () => {
    setSubmitted(true);
    // Make a copy of scenarioDetails to avoid direct state mutation
    var scenarioDetailsCopy = { ...scenarioDetails };

    delete scenarioDetailsCopy.scenarios;

    dispatch(
      extractScenarioData({
        scenarioDetails: scenarioDetailsCopy,
        file,
        projectId,
        artifactType,
        userId,
      })
    );
  };

  // Handle the "fulfilled" state
  useEffect(() => {
    if (result && submitted) {
      // Perform additional actions if needed, e.g., logging or triggering other updates
    }
  }, [result, submitted]);
  console.log(
    "Rendering ScenarioAnalysis with scenarioDetails:",
    scenarioDetails,
    "and result:",
    result
  );
  return (
    <Box sx={{ p: 3, display: "flex", flexDirection: "column", gap: 3 }}>
      <Typography variant="h5" fontWeight="bold">
        Scenario Analysis
      </Typography>

      {/* Form for Scenario Details */}
      <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
        <FormControl fullWidth size="small">
          <InputLabel>Target or Goal</InputLabel>
          <Select
            name="goal"
            value={scenarioDetails.goal} // Use scenarioDetails state
            onChange={handleChange}
            label="Target or Goal"
          >
            <MenuItem value="increase_production">Increase Production</MenuItem>
            <MenuItem value="reduce_capex">Reduce Capex</MenuItem>
          </Select>
        </FormControl>

        <TextField
          fullWidth
          multiline
          rows={3}
          label="Description"
          name="description"
          value={scenarioDetails.description} // Use scenarioDetails state
          onChange={handleChange}
          size="small"
          helperText="Describe the scenario you want to analyze"
        />

        {/* <FormControl fullWidth size="small">
          <InputLabel>Change Type</InputLabel>
          <Select
            name="change_type"
            value={scenarioDetails.change_type} // Use scenarioDetails state
            onChange={handleChange}
            label="Change Type"
          >
            <MenuItem value="equipment">Equipment</MenuItem>
            <MenuItem value="process">Process</MenuItem>
            <MenuItem value="capacity">Capacity</MenuItem>
          </Select>
        </FormControl> */}

        {/* File Upload */}
        <Box>
          <input type="file" name="file" onChange={handleFileChange} />
        </Box>

        <Button
          variant="contained"
          onClick={handleSubmit}
          disabled={loading || !scenarioDetails.description}
          startIcon={loading && <CircularProgress size={20} color="inherit" />}
        >
          {loading ? "Analyzing..." : "Submit"}
        </Button>
      </Box>

      {/* Result View */}

      <Box>
        <Typography variant="h6" gutterBottom>
          Analysis Result
        </Typography>
        {error ? (
          <Typography color="error">{error}</Typography>
        ) : (
          <ReactJson
            src={
              scenarioDetails.scenarios.length > 0
                ? scenarioDetails.scenarios
                : result || { result: "No data available" }
            }
            name={false}
            theme="monokai"
            collapsed={false}
          />
        )}
      </Box>
    </Box>
  );
};

export default ScenarioAnalysis;
