import React from "react";
import {
  Box,
  Typography,
  Paper,
  List,
  ListItem,
  ListItemText,
  Chip,
} from "@mui/material";

const CostDriversDisplay = ({ costEstimation }) => {
  if (!costEstimation.cost_drivers || costEstimation.cost_drivers.length === 0) {
    return (
      <Paper sx={{ p: 2 }}>
        <Typography variant="body2" color="text.secondary">
          No cost drivers identified
        </Typography>
      </Paper>
    );
  }

  return (
    <Paper sx={{ p: 2 }}>
      <Typography variant="h6" gutterBottom>
        Cost Drivers ({costEstimation.cost_drivers.length})
      </Typography>
      <List>
        {costEstimation.cost_drivers.map((driver, index) => (
          <ListItem key={index} divider>
            <ListItemText
              primary={driver.entity_name}
              secondary={
                <Box>
                  <Typography variant="caption" display="block">
                    {driver.entity_type} • {driver.parameter}
                  </Typography>
                  {driver.base_value && (
                    <Typography variant="caption" display="block">
                      Base: {driver.base_value} {driver.base_unit || ""}
                    </Typography>
                  )}
                  {driver.resized_value && (
                    <Typography variant="caption" display="block">
                      Resized: {driver.resized_value} {driver.base_unit || ""}
                    </Typography>
                  )}
                  {driver.change_percentage && (
                    <Typography variant="caption" display="block">
                      Change: {driver.change_percentage}%
                    </Typography>
                  )}
                </Box>
              }
            />
            <Chip
              label={`${(driver.relevance_score * 100).toFixed(0)}%`}
              size="small"
            />
          </ListItem>
        ))}
      </List>
    </Paper>
  );
};

export default CostDriversDisplay;

