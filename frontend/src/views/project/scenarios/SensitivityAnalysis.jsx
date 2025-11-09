import React from "react";
import {
  Box,
  Typography,
  Paper,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  List,
  ListItem,
  ListItemText,
} from "@mui/material";
import { ExpandMore as ExpandMoreIcon } from "@mui/icons-material";

const SensitivityAnalysis = ({ costEstimation }) => {
  if (!costEstimation.sensitivity_analysis) {
    return (
      <Paper sx={{ p: 2 }}>
        <Typography variant="body2" color="text.secondary">
          No sensitivity analysis available
        </Typography>
      </Paper>
    );
  }

  const sensitivity = costEstimation.sensitivity_analysis;

  return (
    <Paper sx={{ p: 2 }}>
      <Typography variant="h6" gutterBottom>
        Sensitivity Analysis
      </Typography>

      {sensitivity.high_impact_parameters &&
        sensitivity.high_impact_parameters.length > 0 && (
          <Accordion defaultExpanded>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Typography variant="subtitle1" color="error">
                High Impact ({sensitivity.high_impact_parameters.length})
              </Typography>
            </AccordionSummary>
            <AccordionDetails>
              <List>
                {sensitivity.high_impact_parameters.map((param, index) => (
                  <ListItem key={index}>
                    <ListItemText
                      primary={param.parameter}
                      secondary={`Change: ${param.change_percentage}% • Method: ${param.calculation_method}`}
                    />
                  </ListItem>
                ))}
              </List>
            </AccordionDetails>
          </Accordion>
        )}

      {sensitivity.moderate_impact_parameters &&
        sensitivity.moderate_impact_parameters.length > 0 && (
          <Accordion>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Typography variant="subtitle1" color="warning.main">
                Moderate Impact ({sensitivity.moderate_impact_parameters.length})
              </Typography>
            </AccordionSummary>
            <AccordionDetails>
              <List>
                {sensitivity.moderate_impact_parameters.map((param, index) => (
                  <ListItem key={index}>
                    <ListItemText
                      primary={param.parameter}
                      secondary={`Change: ${param.change_percentage}% • Method: ${param.calculation_method}`}
                    />
                  </ListItem>
                ))}
              </List>
            </AccordionDetails>
          </Accordion>
        )}

      {sensitivity.low_impact_parameters &&
        sensitivity.low_impact_parameters.length > 0 && (
          <Accordion>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Typography variant="subtitle1" color="text.secondary">
                Low Impact ({sensitivity.low_impact_parameters.length})
              </Typography>
            </AccordionSummary>
            <AccordionDetails>
              <List>
                {sensitivity.low_impact_parameters.map((param, index) => (
                  <ListItem key={index}>
                    <ListItemText
                      primary={param.parameter}
                      secondary={`Change: ${param.change_percentage}% • Method: ${param.calculation_method}`}
                    />
                  </ListItem>
                ))}
              </List>
            </AccordionDetails>
          </Accordion>
        )}
    </Paper>
  );
};

export default SensitivityAnalysis;

