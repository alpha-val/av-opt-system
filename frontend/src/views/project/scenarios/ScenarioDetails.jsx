import React from "react";
import { Box } from "@mui/material";
import ScenarioAnalysis from "../../../components/ScenarioAnalysis";

const ScenarioDetails = ({ scenario, onClose }) => {
  console.log("ScenarioDetails props:", scenario); 
  const scenarioId = scenario?.id;
  const projectId = scenario?.properties.project_id;
  const docId = scenario?.properties.doc_id;
  return (
    <Box sx={{ minHeight: "100vh", display: "flex", flexDirection: "column" }}>
      <ScenarioAnalysis
        scenario={scenario}
        onClose={onClose}
      />
    </Box>
  );
};

export default ScenarioDetails;
