import React, { useState } from "react";
import {
  Box,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Typography,
  IconButton,
  Collapse,
  Chip,
  Alert,
} from "@mui/material";
import {
  KeyboardArrowDown as KeyboardArrowDownIcon,
  KeyboardArrowUp as KeyboardArrowUpIcon,
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  Remove as RemoveIcon,
} from "@mui/icons-material";
import { CostComparisonRow, CostInfo } from "../../types/api";

interface CostComparisonReportProps {
  reportData: CostComparisonRow[];
}

/**
 * Component to display a single row of the cost comparison report
 */
const CostComparisonRowComponent: React.FC<{ row: CostComparisonRow }> = ({
  row,
}) => {
  const [open, setOpen] = useState(false);

  // Format cost value
  const formatCost = (costInfo: CostInfo): string => {
    if (costInfo.value === null || costInfo.value === undefined) {
      return "N/A";
    }
    const currency = costInfo.currency || "USD";
    const value = costInfo.value.toLocaleString(undefined, {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    });
    return `${currency} ${value}`;
  };

  // Calculate cost difference
  const getCostDifference = (): {
    difference: number | null;
    percentage: number | null;
  } => {
    const baseValue = row.base_cost_info.value;
    if (
      baseValue === null ||
      baseValue === undefined ||
      row.tabular_matches.length === 0
    ) {
      return { difference: null, percentage: null };
    }

    // Use the top match (highest score)
    const topMatch = row.tabular_matches[0];
    const tabularValue = topMatch.cost_info.value;

    if (tabularValue === null || tabularValue === undefined) {
      return { difference: null, percentage: null };
    }

    const difference = tabularValue - baseValue;
    const percentage = baseValue !== 0 ? (difference / baseValue) * 100 : 0;

    return { difference, percentage };
  };

  const { difference, percentage } = getCostDifference();

  // Render difference indicator
  const renderDifferenceIndicator = () => {
    if (difference === null || percentage === null) {
      return (
        <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
          <RemoveIcon fontSize="small" color="disabled" />
          <Typography variant="body2" color="text.secondary">
            N/A
          </Typography>
        </Box>
      );
    }

    const isIncrease = difference > 0;
    const isDecrease = difference < 0;

    return (
      <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
        {isIncrease && <TrendingUpIcon fontSize="small" color="error" />}
        {isDecrease && <TrendingDownIcon fontSize="small" color="success" />}
        {!isIncrease && !isDecrease && (
          <RemoveIcon fontSize="small" color="disabled" />
        )}
        <Box>
          <Typography
            variant="body2"
            color={isIncrease ? "error.main" : isDecrease ? "success.main" : "text.secondary"}
            sx={{ fontWeight: 600 }}
          >
            {difference > 0 ? "+" : ""}
            {difference.toLocaleString(undefined, {
              minimumFractionDigits: 2,
              maximumFractionDigits: 2,
            })}
          </Typography>
          <Typography
            variant="caption"
            color={isIncrease ? "error.main" : isDecrease ? "success.main" : "text.secondary"}
          >
            ({percentage > 0 ? "+" : ""}
            {percentage.toFixed(1)}%)
          </Typography>
        </Box>
      </Box>
    );
  };

  return (
    <>
      <TableRow sx={{ "& > *": { borderBottom: "unset" } }}>
        <TableCell>
          <IconButton
            aria-label="expand row"
            size="small"
            onClick={() => setOpen(!open)}
            disabled={row.tabular_matches.length === 0}
          >
            {open ? <KeyboardArrowUpIcon /> : <KeyboardArrowDownIcon />}
          </IconButton>
        </TableCell>
        <TableCell component="th" scope="row">
          <Typography variant="body2" sx={{ fontWeight: 600 }}>
            {row.entity_name}
          </Typography>
        </TableCell>
        <TableCell>
          <Chip label={row.entity_type} size="small" />
        </TableCell>
        <TableCell align="right">
          <Typography variant="body2">
            {formatCost(row.base_cost_info)}
          </Typography>
        </TableCell>
        <TableCell align="center">
          <Typography variant="body2">
            {row.tabular_matches.length > 0
              ? `${row.tabular_matches.length} match${row.tabular_matches.length > 1 ? "es" : ""}`
              : "No matches"}
          </Typography>
        </TableCell>
        <TableCell align="right">{renderDifferenceIndicator()}</TableCell>
      </TableRow>
      <TableRow>
        <TableCell style={{ paddingBottom: 0, paddingTop: 0 }} colSpan={6}>
          <Collapse in={open} timeout="auto" unmountOnExit>
            <Box sx={{ margin: 2 }}>
              <Typography variant="h6" gutterBottom component="div">
                Matching Tabular Entities
              </Typography>
              <Table size="small" aria-label="tabular matches">
                <TableHead>
                  <TableRow>
                    <TableCell>Entity Name</TableCell>
                    <TableCell>Type</TableCell>
                    <TableCell align="right">Cost</TableCell>
                    <TableCell align="right">Match Score</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {row.tabular_matches.map((match, idx) => (
                    <TableRow key={`${match.entity_id}-${idx}`}>
                      <TableCell>{match.entity_name}</TableCell>
                      <TableCell>
                        <Chip label={match.entity_type} size="small" />
                      </TableCell>
                      <TableCell align="right">
                        {formatCost(match.cost_info)}
                      </TableCell>
                      <TableCell align="right">
                        <Chip
                          label={`${(match.score * 100).toFixed(1)}%`}
                          size="small"
                          color={
                            match.score > 0.8
                              ? "success"
                              : match.score > 0.5
                              ? "warning"
                              : "default"
                          }
                        />
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </Box>
          </Collapse>
        </TableCell>
      </TableRow>
    </>
  );
};

/**
 * Cost Comparison Report Component
 * Displays a table comparing base case costs with matching tabular entity costs
 */
const CostComparisonReport: React.FC<CostComparisonReportProps> = ({
  reportData,
}) => {
  if (!reportData || reportData.length === 0) {
    return (
      <Alert severity="info">
        <Typography variant="body2">
          No cost comparison data available. Run cost calculation to generate a
          report.
        </Typography>
      </Alert>
    );
  }

  return (
    <TableContainer component={Paper} variant="outlined">
      <Table aria-label="cost comparison table">
        <TableHead>
          <TableRow>
            <TableCell sx={{ width: 50 }} />
            <TableCell>Entity Name</TableCell>
            <TableCell>Entity Type</TableCell>
            <TableCell align="right">Base Case Cost</TableCell>
            <TableCell align="center">Matching Entities</TableCell>
            <TableCell align="right">Cost Difference</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {reportData.map((row) => (
            <CostComparisonRowComponent key={row.entity_id} row={row} />
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );
};

export default CostComparisonReport;

