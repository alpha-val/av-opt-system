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
import { Search, FilterList } from "@mui/icons-material";
import EntityDetailsRow from "./EntityDetailsRow";

const EntityDetailsTable = ({ entities = [], title = "Entities" }) => {
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedEntityType, setSelectedEntityType] = useState("all");

  // Get unique entity types
  const entityTypes = useMemo(() => {
    const types = {};
    entities.forEach((entity) => {
      const type = entity.type || entity.entity_type || "unknown";
      types[type] = (types[type] || 0) + 1;
    });
    return types;
  }, [entities]);

  // Filter entities based on search and type
  const filteredEntities = useMemo(() => {
    let filtered = entities;

    // Filter by entity type
    if (selectedEntityType !== "all") {
      filtered = filtered.filter(
        (entity) =>
          (entity.type || entity.entity_type || "unknown") ===
          selectedEntityType
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
        const type = (entity.type || entity.entity_type || "").toLowerCase();
        const description = (
          entity.properties?.description || ""
        ).toLowerCase();

        // Search in properties
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
  }, [entities, selectedEntityType, searchTerm]);

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
          {title} ({entities.length})
        </Typography>
      </Box>

      {/* Filters */}
      <Stack direction="row" spacing={2} sx={{ mb: 2 }}>
        {/* Search */}
        <TextField
          size="small"
          placeholder="Search entities..."
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
          <InputLabel id="entity-type-filter-label">
            <Box sx={{ display: "flex", alignItems: "center", gap: 0.5 }}>
              {/* <FilterList fontSize="small" /> */}
              Entity Type
            </Box>
          </InputLabel>
          <Select
            labelId="entity-type-filter-label"
            value={selectedEntityType}
            onChange={(e) => setSelectedEntityType(e.target.value)}
            label="Entity Type"
          >
            <MenuItem value="all">All Types ({entities.length})</MenuItem>
            {Object.entries(entityTypes)
              .sort(([a], [b]) => a.localeCompare(b))
              .map(([type, count]) => (
                <MenuItem key={type} value={type}>
                  {type} ({count})
                </MenuItem>
              ))}
          </Select>
        </FormControl>
      </Stack>

      {/* Entity Type Summary Chips */}
      {/* <Box sx={{ mb: 2 }}>
                <Typography
                    variant="caption"
                    color="text.secondary"
                    sx={{ mb: 1, display: 'block' }}
                >
                    Entity Types:
                </Typography>
                {Object.entries(entityTypes)
                    .sort(([a], [b]) => a.localeCompare(b))
                    .map(([type, count]) => (
                        <Chip
                            key={`entity-type-${type}`}
                            label={`${type}: ${count}`}
                            size="small"
                            color={selectedEntityType === type ? 'primary' : 'default'}
                            onClick={() =>
                                setSelectedEntityType(
                                    type === selectedEntityType ? 'all' : type
                                )
                            }
                            sx={{ mr: 1, mb: 1, cursor: 'pointer' }}
                        />
                    ))}
            </Box> */}

      {/* Results count */}
      {filteredEntities.length !== entities.length && (
        <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
          Showing {filteredEntities.length} of {entities.length} entities
        </Typography>
      )}

      {filteredEntities.length > 0 ? (
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
                <TableCell sx={{ fontWeight: "bold", minWidth: 150 }}>
                  Cost
                </TableCell>
                <TableCell
                  sx={{ fontWeight: "bold", minWidth: 250, maxWidth: 300 }}
                >
                  Attributes
                </TableCell>
                <TableCell
                  sx={{ fontWeight: "bold", minWidth: 250, maxWidth: 300 }}
                >
                  Other Properties
                </TableCell>
                <TableCell
                  sx={{ fontWeight: "bold", minWidth: 50 }}
                  align="center"
                >
                  Evidence
                </TableCell>
                {/* <TableCell sx={{ fontWeight: "bold", minWidth: 180 }}>
                  Sources
                </TableCell> */}
                <TableCell
                  sx={{ fontWeight: "bold", minWidth: 100 }}
                  align="center"
                >
                  Confidence
                </TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {filteredEntities.map((entity, index) => (
                <EntityDetailsRow
                  key={entity.entity_id || `entity-${index}`}
                  entity={entity}
                  index={index}
                />
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      ) : (
        <Box sx={{ textAlign: "center", py: 4 }}>
          <Typography variant="body2" color="text.secondary">
            {searchTerm || selectedEntityType !== "all"
              ? "No entities match your filters"
              : "No entities found"}
          </Typography>
        </Box>
      )}
    </Paper>
  );
};

export default EntityDetailsTable;
