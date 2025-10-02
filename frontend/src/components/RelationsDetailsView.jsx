import React, { useMemo, useState } from "react";
import {
  Paper,
  Typography,
  Box,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Collapse,
  IconButton,
  Tooltip,
  TextField,
  InputAdornment,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Stack,
} from "@mui/material";
import {
  KeyboardArrowDown,
  KeyboardArrowUp,
  Search,
  FilterList,
} from "@mui/icons-material";

const RelationRow = ({ relation, index, entityMap }) => {
  const [open, setOpen] = useState(false);

  // Extract properties safely
  const properties = relation.properties || {};
  const hasProperties = Object.keys(properties).length > 0;

  // Get entity names from IDs
  const sourceEntityId = relation.source_entity || relation.source;
  const targetEntityId = relation.target_entity || relation.target;

  const sourceEntity = entityMap[sourceEntityId];
  const targetEntity = entityMap[targetEntityId];

  const sourceName =
    sourceEntity?.properties.name || sourceEntity?.entity_name || sourceEntityId;
  const targetName =
    targetEntity?.properties.name || targetEntity?.entity_name || targetEntityId;

  return (
    <>
      <TableRow sx={{ "& > *": { borderBottom: "unset" } }} hover>
        <TableCell width={50}>
          {hasProperties && (
            <IconButton
              aria-label="expand row"
              size="small"
              onClick={() => setOpen(!open)}
            >
              {open ? <KeyboardArrowUp /> : <KeyboardArrowDown />}
            </IconButton>
          )}
        </TableCell>
        <TableCell>
          <Box>
            <Typography variant="body2" fontWeight="medium">
              {sourceName}
            </Typography>
            {sourceEntity?.entity_type && (
              <Chip
                label={sourceEntity.entity_type}
                size="small"
                variant="outlined"
                sx={{ mt: 0.5, fontSize: "0.7rem", height: 20 }}
              />
            )}
          </Box>
        </TableCell>
        <TableCell align="center">
          <Chip
            label={relation.relation_type || relation.type || "Unknown"}
            size="small"
            color="primary"
            variant="outlined"
          />
        </TableCell>
        <TableCell>
          <Box>
            <Typography variant="body2" fontWeight="medium">
              {targetName}
            </Typography>
            {targetEntity?.entity_type && (
              <Chip
                label={targetEntity.entity_type}
                size="small"
                variant="outlined"
                sx={{ mt: 0.5, fontSize: "0.7rem", height: 20 }}
              />
            )}
          </Box>
        </TableCell>
        <TableCell>
          {relation.confidence && (
            <Chip
              label={`${(relation.confidence * 100).toFixed(0)}%`}
              size="small"
              color={relation.confidence > 0.7 ? "success" : "warning"}
              variant="outlined"
            />
          )}
        </TableCell>
      </TableRow>
      {hasProperties && (
        <TableRow>
          <TableCell style={{ paddingBottom: 0, paddingTop: 0 }} colSpan={5}>
            <Collapse in={open} timeout="auto" unmountOnExit>
              <Box
                sx={{ margin: 1, p: 2, bgcolor: "grey.50", borderRadius: 1 }}
              >
                <Typography variant="subtitle2" gutterBottom fontWeight="bold">
                  Relation Properties
                </Typography>
                <Box sx={{ display: "flex", flexWrap: "wrap", gap: 1, mt: 1 }}>
                  {Object.entries(properties).map(([key, value]) => {
                    const displayValue =
                      typeof value === "object"
                        ? JSON.stringify(value, null, 2)
                        : String(value);

                    return (
                      <Tooltip
                        key={key}
                        title={`${key}: ${displayValue}`}
                        arrow
                      >
                        <Chip
                          label={`${key}: ${
                            displayValue.length > 50
                              ? displayValue.substring(0, 50) + "..."
                              : displayValue
                          }`}
                          size="small"
                          variant="outlined"
                        />
                      </Tooltip>
                    );
                  })}
                </Box>
              </Box>
            </Collapse>
          </TableCell>
        </TableRow>
      )}
    </>
  );
};

const RelationsDetailsView = ({
  relations = [],
  entities = [],
  title = "Relations",
}) => {
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedRelationType, setSelectedRelationType] = useState("all");

  // Create a map of entity_id to entity object for quick lookup
  const entityMap = useMemo(() => {
    const map = {};
    entities.forEach((entity) => {
      const entityId = entity._id;
      if (entityId) {
        map[entityId] = entity;
      }
    });
    return map;
  }, [entities]);

  // Get unique relation types
  const relationTypes = useMemo(() => {
    const types = {};
    relations.forEach((relation) => {
      const type = relation.relation_type || relation.type || "unknown";
      types[type] = (types[type] || 0) + 1;
    });
    return types;
  }, [relations]);

  // Filter relations based on search and type
  const filteredRelations = useMemo(() => {
    let filtered = relations;

    // Filter by relation type
    if (selectedRelationType !== "all") {
      filtered = filtered.filter(
        (relation) =>
          (relation.relation_type || relation.type || "unknown") ===
          selectedRelationType
      );
    }

    // Filter by search term
    if (searchTerm) {
      const searchLower = searchTerm.toLowerCase();
      filtered = filtered.filter((relation) => {
        const sourceEntityId = relation.source_entity || relation.source;
        const targetEntityId = relation.target_entity || relation.target;

        const sourceEntity = entityMap[sourceEntityId];
        const targetEntity = entityMap[targetEntityId];

        const sourceName = (
          sourceEntity?.name ||
          sourceEntity?.entity_name ||
          sourceEntityId
        ).toLowerCase();
        const targetName = (
          targetEntity?.name ||
          targetEntity?.entity_name ||
          targetEntityId
        ).toLowerCase();
        const relationType = (
          relation.relation_type ||
          relation.type ||
          ""
        ).toLowerCase();

        return (
          sourceName.includes(searchLower) ||
          targetName.includes(searchLower) ||
          relationType.includes(searchLower)
        );
      });
    }

    return filtered;
  }, [relations, selectedRelationType, searchTerm, entityMap]);

  if (relations.length === 0) {
    return (
      <Paper sx={{ p: 3 }}>
        <Typography variant="h6" gutterBottom>
          {title}
        </Typography>
        <Typography variant="body2" color="text.secondary">
          No relations found.
        </Typography>
      </Paper>
    );
  }

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
          {title} ({relations.length})
        </Typography>
      </Box>

      {/* Filters */}
      <Stack direction="row" spacing={2} sx={{ mb: 2 }}>
        {/* Search */}
        <TextField
          size="small"
          placeholder="Search relations..."
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

        {/* Relation Type Filter */}
        <FormControl size="small" sx={{ minWidth: 200 }}>
          <InputLabel id="relation-type-filter-label">
            <Box sx={{ display: "flex", alignItems: "center", gap: 0.5 }}>
              {/* <FilterList fontSize="small" /> */}
              Relation Type
            </Box>
          </InputLabel>
          <Select
            labelId="relation-type-filter-label"
            value={selectedRelationType}
            onChange={(e) => setSelectedRelationType(e.target.value)}
            label="Relation Type"
          >
            <MenuItem value="all">All Types ({relations.length})</MenuItem>
            {Object.entries(relationTypes)
              .sort(([a], [b]) => a.localeCompare(b))
              .map(([type, count]) => (
                <MenuItem key={type} value={type}>
                  {type} ({count})
                </MenuItem>
              ))}
          </Select>
        </FormControl>
      </Stack>

      {/* Relation Type Summary Chips */}
      {/* <Box sx={{ mb: 2 }}>
        <Typography
          variant="caption"
          color="text.secondary"
          sx={{ mb: 1, display: "block" }}
        >
          Relation Types:
        </Typography>
        {Object.entries(relationTypes)
          .sort(([a], [b]) => a.localeCompare(b))
          .map(([type, count]) => (
            <Chip
              key={`relation-type-${type}`}
              label={`${type}: ${count}`}
              size="small"
              color={selectedRelationType === type ? "primary" : "default"}
              onClick={() =>
                setSelectedRelationType(
                  type === selectedRelationType ? "all" : type
                )
              }
              sx={{ mr: 1, mb: 1, cursor: "pointer" }}
            />
          ))}
      </Box> */}

      {/* Results count */}
      {filteredRelations.length !== relations.length && (
        <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
          Showing {filteredRelations.length} of {relations.length} relations
        </Typography>
      )}

      {/* Relations Table */}
      <TableContainer sx={{ maxHeight: 600 }}>
        <Table stickyHeader size="small">
          <TableHead>
            <TableRow>
              <TableCell width={50} />
              <TableCell width="30%">
                <Typography variant="subtitle2" fontWeight="bold">
                  Source Entity
                </Typography>
              </TableCell>
              <TableCell align="center" width="20%">
                <Typography variant="subtitle2" fontWeight="bold">
                  Relationship
                </Typography>
              </TableCell>
              <TableCell width="30%">
                <Typography variant="subtitle2" fontWeight="bold">
                  Target Entity
                </Typography>
              </TableCell>
              <TableCell width="15%">
                <Typography variant="subtitle2" fontWeight="bold">
                  Confidence
                </Typography>
              </TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {filteredRelations.length === 0 ? (
              <TableRow>
                <TableCell colSpan={5} align="center" sx={{ py: 4 }}>
                  <Typography variant="body2" color="text.secondary">
                    No relations match your filters
                  </Typography>
                </TableCell>
              </TableRow>
            ) : (
              filteredRelations.map((relation, index) => (
                <RelationRow
                  key={relation.relation_id || `relation-${index}`}
                  relation={relation}
                  index={index}
                  entityMap={entityMap}
                />
              ))
            )}
          </TableBody>
        </Table>
      </TableContainer>
    </Paper>
  );
};

export default RelationsDetailsView;
