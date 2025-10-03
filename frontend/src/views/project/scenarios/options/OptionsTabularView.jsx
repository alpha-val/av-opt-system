import React, { useState } from "react";
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
  IconButton,
  Menu,
  MenuItem,
  Button,
  Radio,
  Tooltip,
} from "@mui/material";
import {
  MoreVert as MoreVertIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  CheckCircle,
  TrendingUp,
  TrendingDown,
  DragHandle,
} from "@mui/icons-material";
import { useDispatch } from "react-redux";
import { deleteOption, selectOption } from "../../../../redux/optionSlice";

const OptionsTable = ({ options, scenarioId, onAddOption }) => {
  const dispatch = useDispatch();
  const [menuAnchor, setMenuAnchor] = useState(null);
  const [selectedOption, setSelectedOption] = useState(null);

  const handleMenuClick = (event, option) => {
    event.stopPropagation();
    setMenuAnchor(event.currentTarget);
    setSelectedOption(option);
  };

  const handleMenuClose = () => {
    setMenuAnchor(null);
    setSelectedOption(null);
  };

  const handleEdit = () => {
    // TODO: Open edit dialog
    handleMenuClose();
  };

  const handleDelete = () => {
    if (window.confirm(`Delete option "${selectedOption.name}"?`)) {
      dispatch(deleteOption(selectedOption.id));
    }
    handleMenuClose();
  };

  const handleSelect = (optionId) => {
    dispatch(selectOption(optionId));
  };

  const getStrategyColor = (strategy) => {
    switch (strategy) {
      case "lowest_capex":
        return "success";
      case "lowest_opex":
        return "info";
      case "fastest":
        return "warning";
      case "balanced":
        return "primary";
      default:
        return "default";
    }
  };

  const getRiskColor = (risk) => {
    switch (risk) {
      case "low":
        return "success";
      case "medium":
        return "warning";
      case "high":
        return "error";
      default:
        return "default";
    }
  };

  if (options.length === 0) {
    return (
      <Paper sx={{ p: 4, textAlign: "center" }}>
        <Typography variant="h6" color="text.secondary" gutterBottom>
          No options yet
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
          Add options to compare different approaches for this scenario
        </Typography>
        <Button variant="contained" onClick={onAddOption}>
          Add First Option
        </Button>
      </Paper>
    );
  }

  return (
    <Paper>
      <TableContainer>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell width={50}>Select</TableCell>
              <TableCell>Option Name</TableCell>
              <TableCell>Strategy</TableCell>
              <TableCell align="right">CAPEX</TableCell>
              <TableCell align="right">OPEX/Year</TableCell>
              <TableCell align="center">Timeline</TableCell>
              <TableCell align="center">Risk</TableCell>
              <TableCell align="center">Confidence</TableCell>
              <TableCell align="center">Changes</TableCell>
              <TableCell width={50}></TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {options.map((option) => (
              <TableRow
                key={option.id}
                hover
                selected={option.selected}
                sx={{
                  backgroundColor: option.selected
                    ? "action.selected"
                    : "inherit",
                }}
              >
                <TableCell>
                  <Radio
                    checked={option.selected || false}
                    onChange={() => handleSelect(option.id)}
                    size="small"
                  />
                </TableCell>
                <TableCell>
                  <Box>
                    <Typography variant="body2" fontWeight={600}>
                      {option.name}
                    </Typography>
                    {option.description && (
                      <Typography variant="caption" color="text.secondary">
                        {option.description}
                      </Typography>
                    )}
                  </Box>
                </TableCell>
                <TableCell>
                  {option.strategy && (
                    <Chip
                      label={option.strategy.replace(/_/g, " ")}
                      size="small"
                      color={getStrategyColor(option.strategy)}
                    />
                  )}
                </TableCell>
                <TableCell align="right">
                  {option.estimates?.capex ? (
                    <Typography variant="body2">
                      ${option.estimates.capex.value.toLocaleString()}
                    </Typography>
                  ) : (
                    <Typography variant="body2" color="text.secondary">
                      -
                    </Typography>
                  )}
                </TableCell>
                <TableCell align="right">
                  {option.estimates?.opex_per_year ? (
                    <Typography variant="body2">
                      ${option.estimates.opex_per_year.value.toLocaleString()}
                    </Typography>
                  ) : (
                    <Typography variant="body2" color="text.secondary">
                      -
                    </Typography>
                  )}
                </TableCell>
                <TableCell align="center">
                  {option.estimates?.timeline ? (
                    <Typography variant="body2">
                      {option.estimates.timeline.value}{" "}
                      {option.estimates.timeline.unit}
                    </Typography>
                  ) : (
                    <Typography variant="body2" color="text.secondary">
                      -
                    </Typography>
                  )}
                </TableCell>
                <TableCell align="center">
                  {option.estimates?.risk_level ? (
                    <Chip
                      label={option.estimates.risk_level}
                      size="small"
                      color={getRiskColor(option.estimates.risk_level)}
                    />
                  ) : (
                    <Typography variant="body2" color="text.secondary">
                      -
                    </Typography>
                  )}
                </TableCell>
                <TableCell align="center">
                  {option.confidence !== undefined ? (
                    <Typography variant="body2">
                      {Math.round(option.confidence * 100)}%
                    </Typography>
                  ) : (
                    <Typography variant="body2" color="text.secondary">
                      -
                    </Typography>
                  )}
                </TableCell>
                <TableCell align="center">
                  <Box
                    sx={{ display: "flex", justifyContent: "center", gap: 0.5 }}
                  >
                    {option.specs?.equipment_changes?.length > 0 && (
                      <Tooltip
                        title={`${option.specs.equipment_changes.length} equipment changes`}
                      >
                        <Chip
                          label={option.specs.equipment_changes.length}
                          size="small"
                        />
                      </Tooltip>
                    )}
                    {option.specs?.process_changes?.length > 0 && (
                      <Tooltip
                        title={`${option.specs.process_changes.length} process changes`}
                      >
                        <Chip
                          label={option.specs.process_changes.length}
                          size="small"
                          color="primary"
                        />
                      </Tooltip>
                    )}
                  </Box>
                </TableCell>
                <TableCell>
                  <IconButton
                    size="small"
                    onClick={(e) => handleMenuClick(e, option)}
                  >
                    <MoreVertIcon />
                  </IconButton>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      <Menu
        anchorEl={menuAnchor}
        open={Boolean(menuAnchor)}
        onClose={handleMenuClose}
      >
        <MenuItem onClick={handleEdit}>
          <EditIcon fontSize="small" sx={{ mr: 1 }} />
          Edit
        </MenuItem>
        <MenuItem onClick={handleDelete}>
          <DeleteIcon fontSize="small" sx={{ mr: 1 }} />
          Delete
        </MenuItem>
      </Menu>
    </Paper>
  );
};

export default OptionsTable;
