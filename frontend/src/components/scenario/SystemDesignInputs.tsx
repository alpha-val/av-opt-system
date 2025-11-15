import React, { useEffect, useState, useMemo } from "react";
import {
  Box,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  CircularProgress,
  Alert,
  Select,
  MenuItem,
  FormControl,
  Chip,
} from "@mui/material";
import { scenarioApi } from "../../services/api";

interface SystemDesignInputsProps {
  scenarioId: string;
  globalObjectiveType?: string;
  globalObjectiveTarget?: string;
  costEstimateId?: string;
}

interface AttributeRow {
  entityId: string;
  entityName: string;
  attributeName: string;
  attributeValue: number | null;
  unit: string | null;
  type: "Fixed" | "Floating";
  markedUpDown: number | null;
}

/**
 * SystemDesignInputs Component
 * 
 * Displays entity attributes from base case entities in a table format.
 * Allows users to configure attribute types (Fixed/Floating) and shows
 * marked up/down values based on global objective target.
 */
const SystemDesignInputs: React.FC<SystemDesignInputsProps> = ({
  scenarioId,
  globalObjectiveType,
  globalObjectiveTarget,
  costEstimateId,
}) => {
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [entities, setEntities] = useState<Array<{
    id: string;
    type: string;
    properties: {
      name?: string;
      attributes?: Array<{
        name: string;
        value: number | null;
        unit: string | null;
        evidence_text: string | null;
        confidence: number;
      }>;
      [key: string]: any;
    };
  }>>([]);
  const [attributeTypes, setAttributeTypes] = useState<Record<string, "Fixed" | "Floating">>({});

  // Fetch base case entities for the scenario
  useEffect(() => {
    const fetchEntities = async () => {
      if (!scenarioId) {
        setError("Scenario ID is required");
        setLoading(false);
        return;
      }

      try {
        setLoading(true);
        setError(null);

        const entitiesData = await scenarioApi.getEntities(scenarioId, "base_case");
        setEntities(entitiesData.entities || []);
      } catch (err) {
        const errorMessage =
          err instanceof Error ? err.message : "Failed to fetch entities";
        setError(errorMessage);
        setEntities([]);
      } finally {
        setLoading(false);
      }
    };

    fetchEntities();
  }, [scenarioId]);

  /**
   * Parse global objective target and calculate marked up/down value
   */
  const calculateMarkedUpDown = useMemo(() => {
    return (baseValue: number | null): number | null => {
      if (baseValue === null || baseValue === undefined) {
        return null;
      }

      if (!globalObjectiveTarget) {
        return baseValue;
      }

      // Parse target (format: "5%", "$1000000", "10%", etc.)
      const targetMatch = globalObjectiveTarget.match(/^([\d.]+)([%$])?$/);
      if (!targetMatch) {
        return baseValue;
      }

      const targetValue = parseFloat(targetMatch[1]);
      const targetUnit = targetMatch[2] || "%";

      // Determine direction based on objective type
      const isIncrease = globalObjectiveType
        ? globalObjectiveType.toLowerCase().includes("increase") ||
          globalObjectiveType.toLowerCase().includes("improve") ||
          globalObjectiveType.toLowerCase().includes("optimize")
        : true; // Default to increase if unclear

      if (targetUnit === "%") {
        // Percentage change
        const multiplier = isIncrease ? 1 + targetValue / 100 : 1 - targetValue / 100;
        return baseValue * multiplier;
      } else {
        // Absolute change
        const change = isIncrease ? targetValue : -targetValue;
        return baseValue + change;
      }
    };
  }, [globalObjectiveTarget, globalObjectiveType]);

  /**
   * Flatten attributes from entities and group by entity
   */
  const attributeRows = useMemo(() => {
    if (!entities.length) {
      return [];
    }

    const rows: AttributeRow[] = [];

    // Process all base case entities
    entities.forEach((entity) => {
      const entityName = entity.properties.name || "Unknown Entity";
      let attributes: Array<{
        name: string;
        value: number | null;
        unit: string | null;
      }> = [];

      // First, try to get attributes from properties.attributes array
      if (entity.properties.attributes && Array.isArray(entity.properties.attributes)) {
        attributes = entity.properties.attributes.map((attr: any) => ({
          name: attr.name,
          value: attr.value,
          unit: attr.unit || null,
        }));
      } else {
        // If no attributes array, flatten numeric properties from properties object
        // Exclude metadata fields and MSIO classification fields
        const excludedFields = new Set([
          "name",
          "discipline",
          "category",
          "subcategory",
          "entity",
          "confidence",
          "evidence_text",
          "row_index",
          "source_table_id",
          "extraction_method",
          "scenario_id",
          "project_id",
          "doc_id",
          "user_id",
          "artifact_type",
          "created_at",
          "updated_at",
          "extraction_priority",
          "extraction_rationale",
          "expected_attributes",
          "evidence_locations",
          "model",
          "supplier",
        ]);

        // Extract numeric properties as attributes
        Object.entries(entity.properties).forEach(([key, value]) => {
          // Skip excluded fields and non-numeric values
          if (
            !excludedFields.has(key) &&
            (typeof value === "number" || (typeof value === "string" && !isNaN(parseFloat(value))))
          ) {
            const numValue = typeof value === "number" ? value : parseFloat(value);
            if (!isNaN(numValue)) {
              // Try to extract unit from key name (e.g., "capacity_stph" -> "stph")
              const unitMatch = key.match(/_([a-z]+)$/i);
              const unit = unitMatch ? unitMatch[1] : null;
              
              // Clean up attribute name (remove unit suffix if present)
              const attrName = unitMatch ? key.replace(/_([a-z]+)$/i, "") : key;
              
              attributes.push({
                name: attrName.replace(/_/g, " ").replace(/\b\w/g, (l) => l.toUpperCase()),
                value: numValue,
                unit: unit,
              });
            }
          }
        });
      }

      // Only add rows if entity has attributes
      if (attributes.length > 0) {
        attributes.forEach((attr) => {
          const rowKey = `${entity.id}-${attr.name}`;
          const markedUpDown = calculateMarkedUpDown(attr.value);

          rows.push({
            entityId: entity.id,
            entityName,
            attributeName: attr.name,
            attributeValue: attr.value,
            unit: attr.unit || null,
            type: attributeTypes[rowKey] || "Floating", // Default to Floating
            markedUpDown,
          });
        });
      }
    });

    // Group by entity name for display
    return rows.sort((a, b) => {
      if (a.entityName !== b.entityName) {
        return a.entityName.localeCompare(b.entityName);
      }
      return a.attributeName.localeCompare(b.attributeName);
    });
  }, [entities, calculateMarkedUpDown, attributeTypes]);

  /**
   * Handle attribute type change
   */
  const handleTypeChange = (rowKey: string, newType: "Fixed" | "Floating") => {
    setAttributeTypes((prev) => ({
      ...prev,
      [rowKey]: newType,
    }));
  };

  /**
   * Format value for display
   */
  const formatValue = (value: number | null, unit: string | null): string => {
    if (value === null || value === undefined) {
      return "N/A";
    }
    const formatted = typeof value === "number" ? value.toLocaleString() : String(value);
    return unit ? `${formatted} ${unit}` : formatted;
  };

  if (loading) {
    return (
      <Box sx={{ display: "flex", justifyContent: "center", p: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ mb: 2 }}>
        {error}
      </Alert>
    );
  }

  if (attributeRows.length === 0) {
    return (
      <Alert severity="info">
        <Typography variant="body2" gutterBottom>
          No attributes found to display.
        </Typography>
        {entities.length > 0 ? (
          <Typography variant="body2">
            Found {entities.length} entities, but none have extractable attributes.
            This may indicate the analysis needs to be re-run with a different extraction scope.
          </Typography>
        ) : (
          <Typography variant="body2">
            No base case entities found for this scenario. Please run analysis first to extract entities.
          </Typography>
        )}
      </Alert>
    );
  }

  // Group rows by entity for display
  const groupedRows = attributeRows.reduce((acc, row) => {
    if (!acc[row.entityName]) {
      acc[row.entityName] = [];
    }
    acc[row.entityName].push(row);
    return acc;
  }, {} as Record<string, AttributeRow[]>);

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        System Design Inputs
      </Typography>
      <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 3 }}>
        <Typography variant="body2" color="text.secondary">
          Configure attribute types and review marked up/down values based on global objective target.
        </Typography>
        {globalObjectiveTarget && (
          <Chip
            label={`Target: ${globalObjectiveTarget}`}
            size="small"
            color="primary"
            variant="outlined"
          />
        )}
      </Box>

      <TableContainer component={Paper} variant="outlined">
        <Table>
          <TableHead>
            <TableRow>
              <TableCell sx={{ fontWeight: 600 }}>Entity</TableCell>
              <TableCell sx={{ fontWeight: 600 }}>Attribute Name</TableCell>
              <TableCell sx={{ fontWeight: 600 }}>Type</TableCell>
              <TableCell sx={{ fontWeight: 600 }} align="right">
                Base Case Value
              </TableCell>
              <TableCell sx={{ fontWeight: 600 }} align="right">
                Marked Up/Down
              </TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {Object.entries(groupedRows).map(([entityName, rows]) => (
              <React.Fragment key={entityName}>
                {rows.map((row, index) => {
                  const rowKey = `${row.entityId}-${row.attributeName}`;
                  return (
                    <TableRow key={rowKey} hover>
                      {index === 0 && (
                        <TableCell
                          rowSpan={rows.length}
                          sx={{
                            fontWeight: 600,
                            verticalAlign: "top",
                            borderRight: "1px solid",
                            borderColor: "divider",
                          }}
                        >
                          {entityName}
                        </TableCell>
                      )}
                      <TableCell>{row.attributeName}</TableCell>
                      <TableCell>
                        <FormControl size="small" sx={{ minWidth: 120 }}>
                          <Select
                            value={row.type}
                            onChange={(e) =>
                              handleTypeChange(
                                rowKey,
                                e.target.value as "Fixed" | "Floating"
                              )
                            }
                            displayEmpty
                          >
                            <MenuItem value="Fixed">Fixed</MenuItem>
                            <MenuItem value="Floating">Floating</MenuItem>
                          </Select>
                        </FormControl>
                      </TableCell>
                      <TableCell align="right">
                        {formatValue(row.attributeValue, row.unit)}
                      </TableCell>
                      <TableCell align="right">
                        {formatValue(row.markedUpDown, row.unit)}
                      </TableCell>
                    </TableRow>
                  );
                })}
              </React.Fragment>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
};

export default SystemDesignInputs;
