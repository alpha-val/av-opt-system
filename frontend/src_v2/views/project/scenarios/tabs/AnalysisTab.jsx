import React from "react";
import { Box, Typography, Paper, Alert } from "@mui/material";
import AnalysisStatusCard from "../AnalysisStatusCard";
import LocalObjectivesTable from "../LocalObjectivesTable";
import AssumptionsConstraints from "../AssumptionsConstraints";

const AnalysisTab = ({ scenario }) => {
  return (
    <Box>
      <AnalysisStatusCard scenario={scenario} />
      {scenario.analysis ? (
        <>
          <Box sx={{ mt: 3 }}>
            <LocalObjectivesTable analysis={scenario.analysis} />
          </Box>
          <Box sx={{ mt: 3 }}>
            <AssumptionsConstraints analysis={scenario.analysis} />
          </Box>
        </>
      ) : (
        <Alert severity="info" sx={{ mt: 2 }}>
          No analysis data available. Run analysis to see results.
        </Alert>
      )}
    </Box>
  );
};

export default AnalysisTab;

