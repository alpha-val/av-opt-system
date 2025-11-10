import React from "react";
import { Box, Typography, Paper, Alert } from "@mui/material";

const UserConstraintsForm = ({ scenario }) => {
  // TODO: Implement user constraints form
  // This would allow users to add/edit constraints for entities
  return (
    <Paper sx={{ p: 2 }}>
      <Typography variant="h6" gutterBottom>
        User Constraints
      </Typography>
      <Alert severity="info">
        User constraints form will be implemented here. This allows users to specify FIXED or VARIABLE constraints for entity parameters.
      </Alert>
      {scenario.user_constraints && scenario.user_constraints.length > 0 && (
        <Box sx={{ mt: 2 }}>
          <Typography variant="body2">
            {scenario.user_constraints.length} constraint(s) defined
          </Typography>
        </Box>
      )}
    </Paper>
  );
};

export default UserConstraintsForm;

