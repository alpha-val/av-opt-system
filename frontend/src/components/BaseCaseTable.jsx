import React, { useState, useEffect, useMemo } from "react";
import {
  Box,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
  Paper,
  TableSortLabel,
  Checkbox,
  FormControlLabel,
  TextField,
  MenuItem,
  Button,
} from "@mui/material";

function formatCurrency(value) {
  if (typeof value !== "number" || isNaN(value)) return value || "-";
  return `$${value.toLocaleString()}`;
}

function getCost(entity) {
  const props = entity.properties || {};
  let cost =
    entity.cost ||
    props.cost ||
    props.capital_cost ||
    props.cost_value ||
    props.price_value;
  if (typeof cost === "string") {
    cost = parseFloat(cost.replace(/[^0-9.-]+/g, ""));
  }
  return cost;
}

function getAmount(entity) {
  const props = entity.properties || {};
  return (
    props.capacity_value ||
    props.amount ||
    props.quantity ||
    props.volume ||
    props.capacity ||
    ""
  );
}

function getAmountUnit(entity) {
  const props = entity.properties || {};
  return (
    props.capacity_unit ||
    props.amount_unit ||
    props.unit ||
    props.capacity_unit ||
    props.volume_unit ||
    ""
  );
}

function getName(entity) {
  return entity.name || (entity.properties && entity.properties.name) || "-";
}

function getType(entity) {
  return entity.type || (entity.properties && entity.properties.type) || "-";
}

function getAmountNumber(entity) {
  const amount = getAmount(entity);
  if (typeof amount === "number") return amount;
  if (typeof amount === "string") {
    const num = parseFloat(amount.replace(/[^0-9.-]+/g, ""));
    return isNaN(num) ? null : num;
  }
  return null;
}

const columns = [
  { id: "select", label: "" },
  { id: "name", label: "Name" },
  { id: "type", label: "Type" },
  { id: "capacity_value", label: "Capacity" },
  { id: "capacity_unit", label: "Unit" },
  { id: "cost", label: "Cost", align: "right" },
];

function descendingComparator(a, b, orderBy) {
  switch (orderBy) {
    case "name":
      return getName(b).localeCompare(getName(a));
    case "type":
      return getType(b).localeCompare(getType(a));
    case "amount": {
      const aNum = getAmountNumber(a);
      const bNum = getAmountNumber(b);
      if (aNum !== null && bNum !== null) {
        if (bNum !== aNum) return bNum - aNum;
        return getAmount(b).toString().localeCompare(getAmount(a).toString());
      }
      return getAmount(b).toString().localeCompare(getAmount(a).toString());
    }
    case "cost":
      return (getCost(b) || 0) - (getCost(a) || 0);
    default:
      return 0;
  }
}

function getComparator(order, orderBy) {
  return order === "desc"
    ? (a, b) => descendingComparator(a, b, orderBy)
    : (a, b) => -descendingComparator(a, b, orderBy);
}

const BaseCaseTable = ({ entities, onSelectionChange }) => {
  const [order, setOrder] = useState("asc");
  const [orderBy, setOrderBy] = useState("name");
  const [selected, setSelected] = useState([]);
  const [search, setSearch] = useState("");
  const [filterType, setFilterType] = useState("All");
  
  // Get unique entity types for filtering
  const entityTypes = [
    "All",
    ...Array.from(new Set(entities.map(getType).filter(Boolean))),
  ];

  // Filter entities by search and type
  const filteredEntities = entities.filter((entity) => {
    const name = getName(entity).toLowerCase();
    const type = getType(entity);
    const matchesSearch = name.includes(search.toLowerCase());
    const matchesType = filterType === "All" || type === filterType;
    return matchesSearch && matchesType;
  });

  const sortedEntities = React.useMemo(() => {
    return [...filteredEntities].sort(getComparator(order, orderBy));
  }, [filteredEntities, order, orderBy]);

  // Checkbox logic
  const allSelected =
    sortedEntities.length > 0 &&
    sortedEntities.every((e) => selected.includes(e.id || e._id));
  const handleSelectAll = (event) => {
    const newSelected = event.target.checked
      ? sortedEntities.map((e) => e.id || e._id)
      : [];
    setSelected(newSelected);
    if (typeof onSelectionChange === "function") {
      const selectedEntities = entities.filter((e) =>
        newSelected.includes(e.id || e._id)
      );
      onSelectionChange(selectedEntities);
    }
  };
  const handleSelect = (id) => (event) => {
    let newSelected;
    if (event.target.checked) {
      newSelected = [...selected, id];
    } else {
      newSelected = selected.filter((selectedId) => selectedId !== id);
    }
    setSelected(newSelected);
    if (typeof onSelectionChange === "function") {
      const selectedEntities = entities.filter((e) =>
        newSelected.includes(e.id || e._id)
      );
      onSelectionChange(selectedEntities);
    }
  };

  return (
    <Box sx={{ mt: 2 }}>
      <Box sx={{ display: "flex", gap: 2, mb: 2 }}>
        <TextField
          label="Search"
          variant="outlined"
          size="small"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <TextField
          select
          label="Filter by Type"
          variant="outlined"
          size="small"
          value={filterType}
          onChange={(e) => setFilterType(e.target.value)}
        >
          {entityTypes.map((type) => (
            <MenuItem key={type} value={type}>
              {type}
            </MenuItem>
          ))}
        </TextField>
        <Button
          variant="outlined"
          size="small"
          onClick={() => setSelected(sortedEntities.map((e) => e.id || e._id))}
          disabled={allSelected}
        >
          Select All
        </Button>
        <Button
          variant="outlined"
          size="small"
          onClick={() => setSelected([])}
          disabled={selected.length === 0}
        >
          Deselect All
        </Button>
      </Box>
      <TableContainer component={Paper} variant="outlined">
        <Table size="small">
          <TableHead>
            <TableRow sx={{ borderBottom: "1px solid gray" }}>
              <TableCell padding="checkbox">
                <Checkbox
                  checked={allSelected}
                  indeterminate={
                    selected.length > 0 &&
                    selected.length < sortedEntities.length
                  }
                  onChange={handleSelectAll}
                  inputProps={{ "aria-label": "select all entities" }}
                />
              </TableCell>
              {columns.slice(1).map((col) => (
                <TableCell
                  key={col.id}
                  align={col.align || "left"}
                  sortDirection={orderBy === col.id ? order : false}
                >
                  <TableSortLabel
                    active={orderBy === col.id}
                    direction={orderBy === col.id ? order : "asc"}
                    onClick={() => {
                      if (orderBy === col.id) {
                        setOrder(order === "asc" ? "desc" : "asc");
                      } else {
                        setOrderBy(col.id);
                        setOrder("asc");
                      }
                    }}
                  >
                    {col.label}
                  </TableSortLabel>
                </TableCell>
              ))}
            </TableRow>
          </TableHead>
          <TableBody>
            {sortedEntities.map((entity, idx) => {
              const id = entity.id || entity._id;
              return (
                <TableRow key={id}>
                  <TableCell padding="checkbox">
                    <Checkbox
                      checked={selected.includes(id)}
                      onChange={handleSelect(id)}
                      inputProps={{
                        "aria-label": `select entity ${getName(entity)}`,
                      }}
                    />
                  </TableCell>
                  <TableCell>{getName(entity)}</TableCell>
                  <TableCell>{getType(entity)}</TableCell>
                  <TableCell align="left">{getAmount(entity)}</TableCell>
                  <TableCell align="left">{getAmountUnit(entity)}</TableCell>
                  <TableCell align="right">
                    {formatCurrency(getCost(entity))}
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
};

export default BaseCaseTable;
