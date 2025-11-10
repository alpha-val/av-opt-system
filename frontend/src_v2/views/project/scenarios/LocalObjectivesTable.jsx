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
import { ExpandMore as ExpandMoreIcon, ExpandLess as ExpandLessIcon } from "@mui/icons-material";

const LocalObjectivesTable = ({ analysis }) => {
  const [expandedRows, setExpandedRows] = React.useState({});

  const toggleRow = (index) => {
    setExpandedRows((prev) => ({
      ...prev,
      [index]: !prev[index],
    }));
  };

  if (!analysis.local_objectives || analysis.local_objectives.length === 0) {
    return (
      <Paper sx={{ p: 2 }}>
        <Typography variant="body2" color="text.secondary">
          No local objectives found
        </Typography>
      </Paper>
    );
  }

  return (
    <Paper>
      <Box sx={{ p: 2 }}>
        <Typography variant="h6" gutterBottom>
          Local Objectives ({analysis.local_objectives.length})
        </Typography>
      </Box>
      <TableContainer>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell width="50px" />
              <TableCell>Entity Name</TableCell>
              <TableCell>Type</TableCell>
              <TableCell>Parameter</TableCell>
              <TableCell>Base Value</TableCell>
              <TableCell align="right">Relevance Score</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {analysis.local_objectives.map((objective, index) => (
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
                  <TableCell>{objective.entity_name}</TableCell>
                  <TableCell>
                    <Chip label={objective.entity_type} size="small" />
                  </TableCell>
                  <TableCell>{objective.parameter}</TableCell>
                  <TableCell>
                    {objective.base_value} {objective.base_unit || ""}
                  </TableCell>
                  <TableCell align="right">
                    <Chip
                      label={(objective.relevance_score * 100).toFixed(0) + "%"}
                      size="small"
                      color={objective.relevance_score > 0.7 ? "success" : objective.relevance_score > 0.4 ? "warning" : "default"}
                    />
                  </TableCell>
                </TableRow>
                <TableRow>
                  <TableCell colSpan={6} sx={{ py: 0 }}>
                    <Collapse in={expandedRows[index]} timeout="auto" unmountOnExit>
                      <Box sx={{ p: 2 }}>
                        {objective.rationale && (
                          <Box sx={{ mb: 1 }}>
                            <Typography variant="subtitle2">Rationale:</Typography>
                            <Typography variant="body2">{objective.rationale}</Typography>
                          </Box>
                        )}
                        {objective.evidence && objective.evidence.length > 0 && (
                          <Box>
                            <Typography variant="subtitle2">Evidence:</Typography>
                            <ul style={{ margin: 0, paddingLeft: 20 }}>
                              {objective.evidence.map((ev, i) => (
                                <li key={i}>
                                  <Typography variant="body2">{ev}</Typography>
                                </li>
                              ))}
                            </ul>
                          </Box>
                        )}
                      </Box>
                    </Collapse>
                  </TableCell>
                </TableRow>
              </React.Fragment>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Paper>
  );
};

export default LocalObjectivesTable;

