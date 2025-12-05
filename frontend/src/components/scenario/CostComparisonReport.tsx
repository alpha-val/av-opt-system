import React, { useState } from "react";
import {
  Box,
  Stack,
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
  getLeverInfo?: (componentId: string) => { lever_values: Record<string, any>, lever_types: Record<string, string> } | null;
}

/**
 * Component to display a single row of the cost comparison report
 */
const CostComparisonRowComponent: React.FC<{ 
  row: CostComparisonRow;
  getLeverInfo?: (componentId: string) => { lever_values: Record<string, any>, lever_types: Record<string, string> } | null;
}> = ({
  row,
  getLeverInfo,
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

  // Determine border color based on cost difference (reversed logic)
  const getBorderColor = (): string | null => {
    if (difference === null || difference === undefined) {
      return null;
    }
    if (difference > 0) {
      return "#f97316"; // Orange for positive (cost increase)
    } else if (difference < 0) {
      return "#2E7D32"; // Green for negative (cost decrease)
    }
    return null;
  };

  const borderColor = getBorderColor();

  // Render difference indicator
  const renderDifferenceIndicator = () => {
    if (difference === null || percentage === null) {
      return (
        <Box sx={{ display: "flex", alignItems: "center", justifyContent: "flex-end", gap: 1 }}>
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
      <Box sx={{ display: "flex", alignItems: "center", justifyContent: "flex-end", gap: 1 }}>
        {isIncrease && <TrendingUpIcon fontSize="small" color="error" />}
        {isDecrease && <TrendingDownIcon fontSize="small" color="success" />}
        {!isIncrease && !isDecrease && (
          <RemoveIcon fontSize="small" color="disabled" />
        )}
        <Box sx={{ textAlign: "right" }}>
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

  // Get best match info for summary
  const bestMatch = row.tabular_matches.length > 0 ? row.tabular_matches[0] : null;
  const bestMatchScore = bestMatch ? (bestMatch.score * 100).toFixed(1) : null;
  const bestMatchCost = bestMatch ? formatCost(bestMatch.cost_info) : null;

  // Get lever information for this component
  const leverInfo = getLeverInfo ? getLeverInfo(row.entity_id) : null;
  const leverValues = leverInfo?.lever_values || {};
  const leverTypes = leverInfo?.lever_types || {};
  
  // Format levers for display
  const formatLevers = (): string => {
    if (!leverInfo || Object.keys(leverValues).length === 0) {
      return "No levers used";
    }
    
    const leverEntries = Object.entries(leverValues)
      .map(([leverId, value]) => {
        const leverType = leverTypes[leverId] || "Floating";
        const displayValue = typeof value === "number" 
          ? value.toLocaleString(undefined, { maximumFractionDigits: 2 })
          : String(value);
        return `${leverId}: ${displayValue} (${leverType})`;
      });
    
    return leverEntries.join("; ");
  };

  return (
    <>
      <TableRow 
        sx={{ 
          "& > *": { borderBottom: "unset" }, 
          backgroundColor: open ? "secondary.veryLight" : "transparent",
          ...(borderColor && {
            borderLeft: `4px solid ${borderColor}`,
          }),
        }}
      >
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
          <Box>
            <Typography variant="body2" sx={{ fontWeight: 600, mb: 0.5 }}>
              {row.entity_name}
            </Typography>
            <Box sx={{ display: "flex", flexDirection: "column", gap: 0.5, mt: 0.5 }}>
              {bestMatch && (
                <Typography variant="caption" color="text.secondary">
                  Best Match: {bestMatchCost} ({bestMatchScore}%)
                </Typography>
              )}
              {leverInfo && Object.keys(leverValues).length > 0 && (
                <Typography variant="caption" color="text.secondary">
                  Levers: {formatLevers()}
                </Typography>
              )}
            </Box>
          </Box>
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
              : <Chip label="No matches" size="small" color="error" />}
          </Typography>
        </TableCell>
        <TableCell align="right">{renderDifferenceIndicator()}</TableCell>
      </TableRow>
      <TableRow>
        <TableCell style={{ paddingBottom: 0, paddingTop: 0 }} colSpan={5}>
          <Collapse in={open} timeout="auto" unmountOnExit>
            <Box sx={{ margin: 2 }}>
              <Typography variant="h6" gutterBottom component="div">
                Matching Tabular Components
              </Typography>
              <Table size="small" aria-label="tabular matches">
                <TableHead>
                  <TableRow>
                    <TableCell>Component Name</TableCell>
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
 * Displays a table comparing base case costs with matching tabular component costs
 */
const CostComparisonReport: React.FC<CostComparisonReportProps> = ({
  reportData,
  getLeverInfo,
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
            <TableCell>Component Name</TableCell>
            <TableCell align="right">Base Case Cost</TableCell>
            <TableCell align="center">Matching Components</TableCell>
            <TableCell align="right">Cost Difference</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {reportData.map((row) => (
            <CostComparisonRowComponent 
              key={row.entity_id} 
              row={row} 
              getLeverInfo={getLeverInfo}
            />
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );
};

export default CostComparisonReport;

