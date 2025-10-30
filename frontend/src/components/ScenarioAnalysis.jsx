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
  Grid,
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

  const projectId = scenario?.properties.project_id || "";
  const artifactType = "scenario_analysis";
  const userId = scenario?.properties.user_id || "";

  const [file, setFile] = useState(null);
  const [submitted, setSubmitted] = useState(false);

  const { loading, result, error } = useSelector(
    (state) => state.scenarios.extraction
  );

  const handleChange = (e) => {
    const { name, value } = e.target;

    // Handle nested properties immutably
    setScenarioDetails((prev) => {
      const keys = name.split(".");
      const updatedDetails = { ...prev };

      let current = updatedDetails;
      for (let i = 0; i < keys.length - 1; i++) {
        current[keys[i]] = { ...current[keys[i]] };
        current = current[keys[i]];
      }
      current[keys[keys.length - 1]] = value;

      return updatedDetails;
    });
  };

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
  };

  const handleSubmit = async () => {
    setSubmitted(true);

    // Create a copy of scenarioDetails without the "local_objectives" property
    const { properties, ...rest } = scenarioDetails;
    const { local_objectives, ...purgedScenario } = properties || {};
    
    const scenarioDetailsCopy = {
      ...rest,
      properties: purgedScenario,
    };

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

  // Update scenarioDetails state when extraction result changes
  useEffect(() => {
    if (result && submitted) {
      setScenarioDetails((prev) => ({
        ...prev,
        properties: {
          ...prev.properties,
          ...result.properties, // Merge new properties from the extraction result
        },
      }));
    }
  }, [result, submitted]);

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
            name="properties.goal" // Match the structure of scenarioDetails
            value={scenarioDetails.properties.goal}
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
          name="properties.description" // Match the structure of scenarioDetails
          value={scenarioDetails.properties.description}
          onChange={handleChange}
          size="small"
          helperText="Describe the scenario you want to analyze"
        />

        {/* File Upload */}
        <Box>
          <input type="file" name="file" onChange={handleFileChange} />
        </Box>

        <Button
          variant="contained"
          onClick={handleSubmit}
          disabled={loading || !scenarioDetails.properties.description}
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
              scenarioDetails.properties?.local_objectives?.length > 0
                ? scenarioDetails.properties?.local_objectives
                : result || { result: "No data available" }
            }
            name={false}
            theme="monokai"
            collapsed={false}
          />
        )}
      </Box>

      <Box>
        <Grid container spacing={2} justifyContent="flex-start">
          {scenarioDetails.properties?.local_objectives &&
            scenarioDetails.properties?.local_objectives.length > 0 && (
              <Grid item sx={{ mt: 2, mb: 2 }}>
                <div>
                  <strong>Relevant Entities:</strong>
                  <ul>
                    {scenarioDetails.properties?.local_objectives?.map(
                      (entity, idx) => (
                        <li key={idx}>
                          <strong>{entity.name}</strong>
                          <br />
                          Base values: {JSON.stringify(entity.base_values)},
                          <br />
                          Proposed:{" "}
                          {JSON.stringify(entity.proposed_modifications)}
                          <br />
                          Rationale: {entity.rationale}
                        </li>
                      )
                    )}
                  </ul>
                </div>
              </Grid>
            )}
        </Grid>
      </Box>
    </Box>
  );
};

export default ScenarioAnalysis;
