import React from "react";
import { Box, Typography, Paper } from "@mui/material";
import { Folder as FolderIcon } from "@mui/icons-material";

const ScenariosTab = ({ projectId }) => {
  return (
    <Box sx={{ p: 3 }}>
      <Paper elevation={1} sx={{ p: 4, textAlign: "center" }}>
        <FolderIcon sx={{ fontSize: 64, color: "text.secondary", mb: 2 }} />
        <Typography variant="h5" gutterBottom>
          Scenarios
        </Typography>
        <Typography variant="body1" color="text.secondary">
          This section will display project scenarios.
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
          Project ID: {projectId}
        </Typography>
      </Paper>
    </Box>
  );
};

export default ScenariosTab;

