import React, { useMemo, useState } from "react";
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Typography,
  Box,
  TextField,
  InputAdornment,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Stack,
  Chip,
} from "@mui/material";
import { Search } from "@mui/icons-material";
import TableEntityDetailsRow from "./TableEntityDetailsRow";

const TableEntityDetailsTable = ({
  entities = [],
  projectId,
  title = "Table Entities",
}) => {
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedEntityType, setSelectedEntityType] = useState("all");
  const [selectedTableId, setSelectedTableId] = useState("all");

  // Get unique entity types
  const entityTypes = useMemo(() => {
    const types = {};
    entities.forEach((entity) => {
      const type = entity.type || "unknown";
      if (type !== "Table" && type !== "TableRow") {
        // Exclude meta types
        types[type] = (types[type] || 0) + 1;
      }
    });
    return types;
  }, [entities]);

  // Get unique source tables
  const sourceTables = useMemo(() => {
    const tables = {};
    entities.forEach((entity) => {
      const tableId =
        entity.properties?.source_table_id || entity.properties?.table_id;
      if (tableId && entity.type !== "Table" && entity.type !== "TableRow") {
        if (!tables[tableId]) {
          tables[tableId] = {
            id: tableId,
            count: 0,
            filename: entity.properties?.filename || "Unknown",
            page: entity.properties?.page || 1,
          };
        }
        tables[tableId].count += 1;
      }
    });
    return Object.values(tables);
  }, [entities]);

  // Filter entities based on search, type, and table
  const filteredEntities = useMemo(() => {
    let filtered = entities;

    // Exclude Table and TableRow meta entities
    filtered = filtered.filter(
      (entity) => entity.type !== "Table" && entity.type !== "TableRow"
    );

    // Filter by entity type
    if (selectedEntityType !== "all") {
      filtered = filtered.filter(
        (entity) => entity.type === selectedEntityType
      );
    }

    // Filter by source table
    if (selectedTableId !== "all") {
      filtered = filtered.filter(
        (entity) =>
          entity.properties?.source_table_id === selectedTableId ||
          entity.properties?.table_id === selectedTableId
      );
    }

    // Filter by search term
    if (searchTerm) {
      const searchLower = searchTerm.toLowerCase();
      filtered = filtered.filter((entity) => {
        const name = (
          entity.properties?.name ||
          entity.name ||
          ""
        ).toLowerCase();
        const type = (entity.type || "").toLowerCase();
        const description = (
          entity.properties?.description || ""
        ).toLowerCase();
        const propertiesString = JSON.stringify(
          entity.properties || {}
        ).toLowerCase();

        return (
          name.includes(searchLower) ||
          type.includes(searchLower) ||
          description.includes(searchLower) ||
          propertiesString.includes(searchLower)
        );
      });
    }

    return filtered;
  }, [entities, selectedEntityType, selectedTableId, searchTerm]);

  // Sort filtered entities by type, then name, then row_index
  const sortedEntities = useMemo(() => {
    return [...filteredEntities].sort((a, b) => {
      // First sort by type
      const typeA = a.type || "Unknown";
      const typeB = b.type || "Unknown";

      if (typeA !== typeB) {
        return typeA.localeCompare(typeB);
      }

      // Then by name
      const nameA = a.properties?.name || a.name || "Unnamed Entity";
      const nameB = b.properties?.name || b.name || "Unnamed Entity";

      if (nameA !== nameB) {
        return nameA.localeCompare(nameB);
      }

      // Finally by row index if available
      const rowA = a.properties?.row_index ?? Infinity;
      const rowB = b.properties?.row_index ?? Infinity;
      return rowA - rowB;
    });
  }, [filteredEntities]);

  return (
    <Paper sx={{ p: 2 }}>
      {/* Header */}
      <Box
        sx={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          mb: 2,
        }}
      >
        <Typography variant="h6">
          {title} (
          {
            entities.filter((e) => e.type !== "Table" && e.type !== "TableRow")
              .length
          }
          )
        </Typography>
      </Box>

      {/* Filters */}
      <Stack direction="row" spacing={2} sx={{ mb: 2 }}>
        {/* Search */}
        <TextField
          size="small"
          placeholder="Search table entities..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <Search fontSize="small" />
              </InputAdornment>
            ),
          }}
          sx={{ flexGrow: 1, maxWidth: 400 }}
        />

        {/* Entity Type Filter */}
        <FormControl size="small" sx={{ minWidth: 200 }}>
          <InputLabel id="entity-type-filter-label">Entity Type</InputLabel>
          <Select
            labelId="entity-type-filter-label"
            value={selectedEntityType}
            onChange={(e) => setSelectedEntityType(e.target.value)}
            label="Entity Type"
          >
            <MenuItem value="all">
              All Types ({Object.values(entityTypes).reduce((a, b) => a + b, 0)}
              )
            </MenuItem>
            {Object.entries(entityTypes)
              .sort(([a], [b]) => a.localeCompare(b))
              .map(([type, count]) => (
                <MenuItem key={type} value={type}>
                  {type} ({count})
                </MenuItem>
              ))}
          </Select>
        </FormControl>

        {/* Source Table Filter */}
        <FormControl size="small" sx={{ minWidth: 250 }}>
          <InputLabel id="source-table-filter-label">Source Table</InputLabel>
          <Select
            labelId="source-table-filter-label"
            value={selectedTableId}
            onChange={(e) => setSelectedTableId(e.target.value)}
            label="Source Table"
          >
            <MenuItem value="all">All Tables ({sourceTables.length})</MenuItem>
            {sourceTables
              .sort((a, b) => a.filename.localeCompare(b.filename))
              .map((table) => (
                <MenuItem key={table.id} value={table.id}>
                  {table.filename} - Page {table.page} ({table.count} entities)
                </MenuItem>
              ))}
          </Select>
        </FormControl>
      </Stack>

      {/* Results count */}
      {sortedEntities.length !==
        entities.filter((e) => e.type !== "Table" && e.type !== "TableRow")
          .length && (
        <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
          Showing {sortedEntities.length} of{" "}
          {
            entities.filter((e) => e.type !== "Table" && e.type !== "TableRow")
              .length
          }{" "}
          entities
        </Typography>
      )}

      {sortedEntities.length > 0 ? (
        <TableContainer sx={{ maxHeight: 600 }}>
          <Table stickyHeader size="small">
            <TableHead>
              <TableRow>
                <TableCell sx={{ fontWeight: "bold", minWidth: 200 }}>
                  Name
                </TableCell>
                <TableCell sx={{ fontWeight: "bold", minWidth: 100 }}>
                  Type
                </TableCell>
                <TableCell sx={{ fontWeight: "bold", minWidth: 120 }}>
                  Cost
                </TableCell>
                <TableCell sx={{ fontWeight: "bold", minWidth: 140 }}>
                  Amount/Quantity
                </TableCell>
                <TableCell
                  sx={{ fontWeight: "bold", minWidth: 300, maxWidth: 300 }}
                >
                  Other Properties
                </TableCell>
                <TableCell sx={{ fontWeight: "bold", minWidth: 200 }}>
                  Source Table
                </TableCell>
                <TableCell sx={{ fontWeight: "bold", minWidth: 180 }}>
                  Source Document
                </TableCell>
                <TableCell
                  sx={{ fontWeight: "bold", minWidth: 100 }}
                  align="center"
                >
                  Confidence
                </TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {sortedEntities.map((entity, index) => (
                <TableEntityDetailsRow
                  key={entity.id || entity._id || `entity-${index}`}
                  entity={entity}
                  index={index}
                  projectId={projectId}
                />
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      ) : (
        <Box sx={{ textAlign: "center", py: 4 }}>
          <Typography variant="body2" color="text.secondary">
            {searchTerm ||
            selectedEntityType !== "all" ||
            selectedTableId !== "all"
              ? "No entities match your filters"
              : "No table entities found"}
          </Typography>
        </Box>
      )}
    </Paper>
  );
};

export default TableEntityDetailsTable;
