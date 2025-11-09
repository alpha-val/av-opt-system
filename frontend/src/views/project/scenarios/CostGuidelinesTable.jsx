import React from "react";
import {
  Box,
  Typography,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
} from "@mui/material";

const CostGuidelinesTable = ({ costEstimation }) => {
  if (!costEstimation.cost_guidelines || costEstimation.cost_guidelines.length === 0) {
    return (
      <Paper sx={{ p: 2 }}>
        <Typography variant="body2" color="text.secondary">
          No cost guidelines available
        </Typography>
      </Paper>
    );
  }

  return (
    <Paper>
      <Box sx={{ p: 2 }}>
        <Typography variant="h6" gutterBottom>
          Cost Guidelines ({costEstimation.cost_guidelines.length})
        </Typography>
      </Box>
      <TableContainer>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Item</TableCell>
              <TableCell align="right">Base Cost</TableCell>
              <TableCell>Currency</TableCell>
              <TableCell>Basis Year</TableCell>
              <TableCell>Scaling Rule</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {costEstimation.cost_guidelines.map((guideline, index) => (
              <TableRow key={index}>
                <TableCell>{guideline.item}</TableCell>
                <TableCell align="right">
                  {guideline.base_cost_value
                    ? guideline.base_cost_value.toLocaleString()
                    : "N/A"}
                </TableCell>
                <TableCell>{guideline.currency || "USD"}</TableCell>
                <TableCell>{guideline.basis_year || "N/A"}</TableCell>
                <TableCell>{guideline.scaling_rule || "N/A"}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Paper>
  );
};

export default CostGuidelinesTable;

