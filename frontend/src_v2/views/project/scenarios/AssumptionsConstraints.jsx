import React from "react";
import {
  Box,
  Typography,
  Paper,
  Grid,
  Chip,
  Accordion,
  AccordionSummary,
  AccordionDetails,
} from "@mui/material";
import { ExpandMore as ExpandMoreIcon } from "@mui/icons-material";

const AssumptionsConstraints = ({ analysis }) => {
  return (
    <Box>
      <Grid container spacing={2}>
        {analysis.assumptions && analysis.assumptions.length > 0 && (
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 2 }}>
              <Typography variant="h6" gutterBottom>
                Assumptions ({analysis.assumptions.length})
              </Typography>
              {analysis.assumptions.map((assumption, index) => (
                <Accordion key={index}>
                  <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                    <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                      <Chip label={assumption.assumption_type} size="small" />
                      <Typography variant="body2" sx={{ flexGrow: 1 }}>
                        {assumption.text.substring(0, 60)}
                        {assumption.text.length > 60 ? "..." : ""}
                      </Typography>
                    </Box>
                  </AccordionSummary>
                  <AccordionDetails>
                    <Typography variant="body2">{assumption.text}</Typography>
                    {assumption.refs && assumption.refs.length > 0 && (
                      <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: "block" }}>
                        References: {assumption.refs.join(", ")}
                      </Typography>
                    )}
                  </AccordionDetails>
                </Accordion>
              ))}
            </Paper>
          </Grid>
        )}

        {analysis.policies && analysis.policies.length > 0 && (
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 2 }}>
              <Typography variant="h6" gutterBottom>
                Policies ({analysis.policies.length})
              </Typography>
              {analysis.policies.map((policy, index) => (
                <Accordion key={index}>
                  <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                    <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                      <Chip label={policy.domain} size="small" />
                      <Typography variant="body2" sx={{ flexGrow: 1 }}>
                        {policy.text.substring(0, 60)}
                        {policy.text.length > 60 ? "..." : ""}
                      </Typography>
                    </Box>
                  </AccordionSummary>
                  <AccordionDetails>
                    <Typography variant="body2">{policy.text}</Typography>
                    {policy.refs && policy.refs.length > 0 && (
                      <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: "block" }}>
                        References: {policy.refs.join(", ")}
                      </Typography>
                    )}
                  </AccordionDetails>
                </Accordion>
              ))}
            </Paper>
          </Grid>
        )}

        {analysis.constraints && analysis.constraints.length > 0 && (
          <Grid item xs={12}>
            <Paper sx={{ p: 2 }}>
              <Typography variant="h6" gutterBottom>
                Constraints ({analysis.constraints.length})
              </Typography>
              {analysis.constraints.map((constraint, index) => (
                <Accordion key={index}>
                  <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                    <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                      <Chip label={constraint.basis} size="small" />
                      <Typography variant="body2" sx={{ flexGrow: 1 }}>
                        {constraint.constraint.substring(0, 60)}
                        {constraint.constraint.length > 60 ? "..." : ""}
                      </Typography>
                    </Box>
                  </AccordionSummary>
                  <AccordionDetails>
                    <Typography variant="body2">{constraint.constraint}</Typography>
                    {constraint.refs && constraint.refs.length > 0 && (
                      <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: "block" }}>
                        References: {constraint.refs.join(", ")}
                      </Typography>
                    )}
                  </AccordionDetails>
                </Accordion>
              ))}
            </Paper>
          </Grid>
        )}
      </Grid>
    </Box>
  );
};

export default AssumptionsConstraints;

