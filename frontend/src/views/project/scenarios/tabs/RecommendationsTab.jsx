import React from "react";
import { Box, Alert } from "@mui/material";
import RecommendationsDisplay from "../RecommendationsDisplay";

const RecommendationsTab = ({ scenario }) => {
  return (
    <Box>
      {scenario.recommendation ? (
        <RecommendationsDisplay recommendation={scenario.recommendation} />
      ) : (
        <Alert severity="info">
          No recommendations available. Build recommendations to see results.
        </Alert>
      )}
    </Box>
  );
};

export default RecommendationsTab;

