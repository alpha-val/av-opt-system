import React from "react";
import { Box, Typography, Paper, Grid, Chip } from "@mui/material";

const OverviewTab = ({ scenario }) => {
  const formatDate = (dateString) => {
    if (!dateString) return "N/A";
    return new Date(dateString).toLocaleString();
  };

  const getStatusChip = (status) => {
    const statusConfig = {
      draft: { color: "default", label: "Draft" },
      analyzing: { color: "info", label: "Analyzing" },
      ready: { color: "success", label: "Ready" },
      archived: { color: "default", label: "Archived" },
    };
    const config = statusConfig[status] || { color: "default", label: status };
    return <Chip label={config.label} size="small" color={config.color} />;
  };

  return (
    <Box>
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Basic Information
            </Typography>
            <Box sx={{ display: "flex", flexDirection: "column", gap: 1 }}>
              <Box>
                <Typography variant="caption" color="text.secondary">
                  Status
                </Typography>
                <Box sx={{ mt: 0.5 }}>{getStatusChip(scenario.status)}</Box>
              </Box>
              <Box>
                <Typography variant="caption" color="text.secondary">
                  Created
                </Typography>
                <Typography variant="body2">
                  {formatDate(scenario.created_at)}
                </Typography>
              </Box>
              <Box>
                <Typography variant="caption" color="text.secondary">
                  Updated
                </Typography>
                <Typography variant="body2">
                  {formatDate(scenario.updated_at)}
                </Typography>
              </Box>
            </Box>
          </Paper>
        </Grid>
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Global Objective
            </Typography>
            {scenario.global_objective ? (
              <Box sx={{ display: "flex", flexDirection: "column", gap: 1 }}>
                <Box>
                  <Typography variant="caption" color="text.secondary">
                    Goal Type
                  </Typography>
                  <Typography variant="body2">
                    {scenario.global_objective.goal_type
                      ?.split("_")
                      .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
                      .join(" ")}
                  </Typography>
                </Box>
                <Box>
                  <Typography variant="caption" color="text.secondary">
                    Change
                  </Typography>
                  <Typography variant="body2">
                    {scenario.global_objective.change_direction}{" "}
                    {scenario.global_objective.change_magnitude}{" "}
                    {scenario.global_objective.change_unit}
                  </Typography>
                </Box>
                {scenario.global_objective.description && (
                  <Box>
                    <Typography variant="caption" color="text.secondary">
                      Description
                    </Typography>
                    <Typography variant="body2">
                      {scenario.global_objective.description}
                    </Typography>
                  </Box>
                )}
              </Box>
            ) : (
              <Typography variant="body2" color="text.secondary">
                No global objective defined
              </Typography>
            )}
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default OverviewTab;

