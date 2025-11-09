import React from "react";
import { Box, Typography, Grid, Chip } from "@mui/material";
import {
  ArrowUpward as IncreaseIcon,
  ArrowDownward as DecreaseIcon,
  Remove as NeutralIcon,
} from "@mui/icons-material";

const ExpectedEffects = ({ expectedEffects }) => {
  const getDirectionIcon = (direction) => {
    switch (direction) {
      case "increase":
        return <IncreaseIcon color="success" fontSize="small" />;
      case "decrease":
        return <DecreaseIcon color="error" fontSize="small" />;
      default:
        return <NeutralIcon color="disabled" fontSize="small" />;
    }
  };

  return (
    <Box>
      <Typography variant="subtitle2" gutterBottom>
        Expected Effects:
      </Typography>
      <Grid container spacing={2}>
        {Object.entries(expectedEffects).map(([metric, effect]) => (
          <Grid item xs={12} sm={6} md={4} key={metric}>
            <Box
              sx={{
                p: 1.5,
                border: 1,
                borderColor: "divider",
                borderRadius: 1,
              }}
            >
              <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 0.5 }}>
                {getDirectionIcon(effect.direction)}
                <Typography variant="body2" fontWeight={500}>
                  {metric.charAt(0).toUpperCase() + metric.slice(1)}
                </Typography>
              </Box>
              {effect.estimate_pct && (
                <Typography variant="body2" color="text.secondary">
                  {effect.estimate_pct}
                </Typography>
              )}
              {effect.notes && (
                <Typography variant="caption" color="text.secondary" display="block" sx={{ mt: 0.5 }}>
                  {effect.notes}
                </Typography>
              )}
            </Box>
          </Grid>
        ))}
      </Grid>
    </Box>
  );
};

export default ExpectedEffects;

