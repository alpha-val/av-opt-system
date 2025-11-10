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
  Chip,
  Collapse,
  IconButton,
} from "@mui/material";
import {
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  ArrowUpward as IncreaseIcon,
  ArrowDownward as DecreaseIcon,
} from "@mui/icons-material";

const ResizedParametersTable = ({ resizing }) => {
  const [expandedRows, setExpandedRows] = React.useState({});

  const toggleRow = (index) => {
    setExpandedRows((prev) => ({
      ...prev,
      [index]: !prev[index],
    }));
  };

  if (!resizing.resized_parameters || resizing.resized_parameters.length === 0) {
    return (
      <Paper sx={{ p: 2 }}>
        <Typography variant="body2" color="text.secondary">
          No resized parameters
        </Typography>
      </Paper>
    );
  }

  return (
    <Paper>
      <Box sx={{ p: 2 }}>
        <Typography variant="h6" gutterBottom>
          Resized Parameters ({resizing.resized_parameters.length})
        </Typography>
        {resizing.calculation_summary && (
          <Typography variant="body2" color="text.secondary">
            {resizing.calculation_summary}
          </Typography>
        )}
      </Box>
      <TableContainer>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell width="50px" />
              <TableCell>Parameter</TableCell>
              <TableCell>Original Value</TableCell>
              <TableCell>Resized Value</TableCell>
              <TableCell align="right">Change</TableCell>
              <TableCell>Method</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {resizing.resized_parameters.map((param, index) => {
              const changePct = param.calculation_details?.change_percentage || 0;
              const isIncrease = changePct > 0;
              return (
                <React.Fragment key={index}>
                  <TableRow hover>
                    <TableCell>
                      <IconButton
                        size="small"
                        onClick={() => toggleRow(index)}
                      >
                        {expandedRows[index] ? <ExpandLessIcon /> : <ExpandMoreIcon />}
                      </IconButton>
                    </TableCell>
                    <TableCell>{param.parameter}</TableCell>
                    <TableCell>
                      {param.original_value} {param.unit || ""}
                    </TableCell>
                    <TableCell>
                      {param.resized_value} {param.unit || ""}
                    </TableCell>
                    <TableCell align="right">
                      <Box sx={{ display: "flex", alignItems: "center", justifyContent: "flex-end", gap: 0.5 }}>
                        {isIncrease ? (
                          <IncreaseIcon color="success" fontSize="small" />
                        ) : (
                          <DecreaseIcon color="error" fontSize="small" />
                        )}
                        <Typography
                          variant="body2"
                          color={isIncrease ? "success.main" : "error.main"}
                        >
                          {Math.abs(changePct).toFixed(2)}%
                        </Typography>
                      </Box>
                    </TableCell>
                    <TableCell>
                      <Chip label={param.calculation_method} size="small" />
                    </TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell colSpan={6} sx={{ py: 0 }}>
                      <Collapse in={expandedRows[index]} timeout="auto" unmountOnExit>
                        <Box sx={{ p: 2 }}>
                          {param.calculation_details && (
                            <Box>
                              <Typography variant="subtitle2">Calculation Details:</Typography>
                              <pre style={{ margin: 0, fontSize: "0.875rem" }}>
                                {JSON.stringify(param.calculation_details, null, 2)}
                              </pre>
                            </Box>
                          )}
                          <Box sx={{ mt: 1 }}>
                            <Typography variant="caption" color="text.secondary">
                              Confidence: {(param.confidence * 100).toFixed(0)}%
                            </Typography>
                          </Box>
                        </Box>
                      </Collapse>
                    </TableCell>
                  </TableRow>
                </React.Fragment>
              );
            })}
          </TableBody>
        </Table>
      </TableContainer>
    </Paper>
  );
};

export default ResizedParametersTable;

