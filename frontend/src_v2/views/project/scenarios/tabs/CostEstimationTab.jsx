import React from "react";
import { Box, Alert } from "@mui/material";
import CostEstimationStatus from "../CostEstimationStatus";
import CostGuidelinesTable from "../CostGuidelinesTable";
import CostDriversDisplay from "../CostDriversDisplay";
import SensitivityAnalysis from "../SensitivityAnalysis";

const CostEstimationTab = ({ scenario }) => {
  return (
    <Box>
      <CostEstimationStatus scenario={scenario} />
      {scenario.cost_estimation ? (
        <>
          <Box sx={{ mt: 3 }}>
            <CostGuidelinesTable costEstimation={scenario.cost_estimation} />
          </Box>
          <Box sx={{ mt: 3 }}>
            <CostDriversDisplay costEstimation={scenario.cost_estimation} />
          </Box>
          <Box sx={{ mt: 3 }}>
            <SensitivityAnalysis costEstimation={scenario.cost_estimation} />
          </Box>
        </>
      ) : (
        <Alert severity="info" sx={{ mt: 2 }}>
          No cost estimation data available. Prepare cost estimation to see results.
        </Alert>
      )}
    </Box>
  );
};

export default CostEstimationTab;

