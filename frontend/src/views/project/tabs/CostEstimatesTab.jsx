import React from "react";
import { Box, Typography, Paper } from "@mui/material";
import { Calculate as CalculateIcon } from "@mui/icons-material";

const CostEstimatesTab = ({ projectId }) => {
  return (
    <Box sx={{ p: 3 }}>
      <Paper elevation={1} sx={{ p: 4, textAlign: "center" }}>
        <CalculateIcon sx={{ fontSize: 64, color: "text.secondary", mb: 2 }} />
        <Typography variant="h5" gutterBottom>
          Cost Estimates
        </Typography>
        <Typography variant="body1" color="text.secondary">
          This section will display cost estimates for the project.
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
          Project ID: {projectId}
        </Typography>
      </Paper>
    </Box>
  );
};

export default CostEstimatesTab;

