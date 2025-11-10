import React from "react";
import {
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
  Box,
  Chip,
} from "@mui/material";
import { CheckCircle } from "@mui/icons-material";

const OptionComparisonView = ({ options }) => {
  const getBestValue = (field) => {
    const values = options
      .map((opt) => {
        if (field === "capex") return opt.estimates?.capex?.value;
        if (field === "opex") return opt.estimates?.opex_per_year?.value;
        if (field === "timeline") return opt.estimates?.timeline?.value;
        return null;
      })
      .filter((v) => v !== null && v !== undefined);

    return field === "timeline" ? Math.min(...values) : Math.min(...values);
  };

  const bestCapex = getBestValue("capex");
  const bestOpex = getBestValue("opex");
  const bestTimeline = getBestValue("timeline");

  return (
    <Paper>
      <Box sx={{ p: 2 }}>
        <Typography variant="h6" gutterBottom>
          Option Comparison
        </Typography>
      </Box>
      <TableContainer>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Criteria</TableCell>
              {options.map((option) => (
                <TableCell key={option.id} align="center">
                  <Box>
                    <Typography variant="body2" fontWeight={600}>
                      {option.name}
                    </Typography>
                    {option.selected && (
                      <Chip
                        label="Selected"
                        size="small"
                        color="primary"
                        sx={{ mt: 0.5 }}
                      />
                    )}
                  </Box>
                </TableCell>
              ))}
            </TableRow>
          </TableHead>
          <TableBody>
            <TableRow>
              <TableCell>CAPEX</TableCell>
              {options.map((option) => (
                <TableCell key={option.id} align="center">
                  {option.estimates?.capex ? (
                    <Box
                      sx={{
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        gap: 1,
                      }}
                    >
                      <Typography variant="body2">
                        ${option.estimates.capex.value.toLocaleString()}
                      </Typography>
                      {option.estimates.capex.value === bestCapex && (
                        <CheckCircle color="success" fontSize="small" />
                      )}
                    </Box>
                  ) : (
                    "-"
                  )}
                </TableCell>
              ))}
            </TableRow>
            <TableRow>
              <TableCell>OPEX/Year</TableCell>
              {options.map((option) => (
                <TableCell key={option.id} align="center">
                  {option.estimates?.opex_per_year ? (
                    <Box
                      sx={{
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        gap: 1,
                      }}
                    >
                      <Typography variant="body2">
                        ${option.estimates.opex_per_year.value.toLocaleString()}
                      </Typography>
                      {option.estimates.opex_per_year.value === bestOpex && (
                        <CheckCircle color="success" fontSize="small" />
                      )}
                    </Box>
                  ) : (
                    "-"
                  )}
                </TableCell>
              ))}
            </TableRow>
            <TableRow>
              <TableCell>Timeline</TableCell>
              {options.map((option) => (
                <TableCell key={option.id} align="center">
                  {option.estimates?.timeline ? (
                    <Box
                      sx={{
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        gap: 1,
                      }}
                    >
                      <Typography variant="body2">
                        {option.estimates.timeline.value}{" "}
                        {option.estimates.timeline.unit}
                      </Typography>
                      {option.estimates.timeline.value === bestTimeline && (
                        <CheckCircle color="success" fontSize="small" />
                      )}
                    </Box>
                  ) : (
                    "-"
                  )}
                </TableCell>
              ))}
            </TableRow>
            <TableRow>
              <TableCell>Risk Level</TableCell>
              {options.map((option) => (
                <TableCell key={option.id} align="center">
                  {option.estimates?.risk_level ? (
                    <Chip
                      label={option.estimates.risk_level}
                      size="small"
                      color={
                        option.estimates.risk_level === "low"
                          ? "success"
                          : option.estimates.risk_level === "medium"
                          ? "warning"
                          : "error"
                      }
                    />
                  ) : (
                    "-"
                  )}
                </TableCell>
              ))}
            </TableRow>
            <TableRow>
              <TableCell>Confidence</TableCell>
              {options.map((option) => (
                <TableCell key={option.id} align="center">
                  {option.confidence !== undefined
                    ? `${Math.round(option.confidence * 100)}%`
                    : "-"}
                </TableCell>
              ))}
            </TableRow>
          </TableBody>
        </Table>
      </TableContainer>
    </Paper>
  );
};

export default OptionComparisonView;
