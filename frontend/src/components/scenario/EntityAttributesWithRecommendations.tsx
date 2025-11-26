import React, { useEffect, useState, useMemo, useCallback, memo } from "react";
import {
  Box,
  Chip,
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
  Divider,
  TextField,
  Card,
  CardContent,
  Select,
  MenuItem,
  FormControl,
  IconButton,
  Tooltip,
  Checkbox,
} from "@mui/material";
import { Info as InfoIcon } from "@mui/icons-material";
import { scenarioApi } from "../../services/api";

interface EntityAttributesWithRecommendationsProps {
  scenarioId: string;
  globalObjectiveType?: string;
  globalObjectiveTarget?: string;
  globalObjectiveUnit?: string;
  onEntitySelectionChange?: (selections: Record<string, boolean>) => void;
}

interface Recommendation {
  id: string;
  type: string;
  name: string;
  rationale: string;
  relevance: "primary" | "secondary" | "other";
  change_direction?: "increase" | "decrease" | "no change";
  change_unit?: string;
  change_magnitude?: string;
  change_magnitude_unit?: string;
  change_magnitude_direction?: string;
  evidence_text?: string;
  confidence?: number;
}

interface EntityAttribute {
  name: string;
  value: number | string | null;
  unit: string | null;
  evidence_text?: string | null;
  confidence?: number;
}

interface Entity {
  id: string;
  type: string;
  properties: {
    name?: string;
    recommendations?: Recommendation[];
    attributes?: EntityAttribute[];
    [key: string]: any;
  };
}

interface AttributeRow {
  entityId: string;
  entityName: string;
  entityType: string;
  attributeName: string;
  attributeLabel: string;
  attributeValue: number | string | null;
  unit: string | null;
  isNumeric: boolean;
  baseValue: number | string | null;
  updatedValue: number | string | null;
  evidenceText: string | null;
  confidence: number | null;
  recommendations: Recommendation[];
  attributeIndex: number; // Index to ensure unique keys
  costValue: number | null;
  costCurrency: string | null;
}

interface AttributeRowComponentProps {
  row: AttributeRow;
  rowKey: string;
  currentType: "Fixed" | "Floating";
  currentBaseValue: number | string | null;
  currentUpdatedValue: number | string | null;
  onTypeChange: (rowKey: string, newType: "Fixed" | "Floating") => void;
  onBaseValueChange: (rowKey: string, value: number | string | null) => void;
  onUpdatedValueChange: (rowKey: string, value: number | string | null) => void;
  formatValue: (value: number | string | null, unit: string | null) => string;
  calculateUpdatedValue: (baseValue: number | null) => number | null;
  showDivider: boolean;
  showEntityName: boolean;
  showEntityType: boolean;
  showCost: boolean;
  showRecommendations: boolean;
  showIncludeCheckbox: boolean;
  isEntityIncluded: boolean;
  onEntityInclusionToggle: (entityId: string) => void;
  rowSpan: number;
}

/**
 * Component to display recommendations for an entity
 */
const RecommendationsCell: React.FC<{ recommendations: Recommendation[] }> = ({
  recommendations,
}) => {
  if (!recommendations || recommendations.length === 0) {
    return (
      <Typography variant="caption" color="text.secondary">
        No recommendations
      </Typography>
    );
  }

  const getRelevanceColor = (
    relevance: string
  ): "error" | "warning" | "success" | "default" => {
    switch (relevance) {
      case "primary":
        return "error";
      case "secondary":
        return "warning";
      case "other":
        return "success";
      default:
        return "default";
    }
  };

  return (
    <Box sx={{ display: "flex", flexDirection: "column", gap: 0.5 }}>
      {recommendations.map((rec, idx) => (
        <Card key={rec.id || idx} variant="outlined" sx={{ p: 0.5 }}>
          <CardContent sx={{ p: 0.5, "&:last-child": { pb: 0.5 } }}>
            <Box
              sx={{ display: "flex", alignItems: "center", gap: 0.5, mb: 0.25 }}
            >
              <Chip
                label={rec.type}
                size="small"
                variant="outlined"
                sx={{ height: 20, fontSize: "0.65rem" }}
              />
              <Chip
                label={rec.relevance}
                size="small"
                variant="outlined"
                color={getRelevanceColor(rec.relevance)}
                sx={{ height: 20, fontSize: "0.65rem" }}
              />
            </Box>
            <Typography
              variant="caption"
              fontWeight={600}
              sx={{ display: "block", mb: 0.25 }}
            >
              {rec.name}
            </Typography>
            {rec.rationale && (
              <Typography
                variant="caption"
                color="text.secondary"
                sx={{ display: "block" }}
              >
                {rec.rationale}
              </Typography>
            )}
          </CardContent>
        </Card>
      ))}
    </Box>
  );
};

/**
 * Memoized attribute row component
 */
const AttributeRowComponent = memo<AttributeRowComponentProps>(
  ({
    row,
    rowKey,
    currentType,
    currentBaseValue,
    currentUpdatedValue,
    onTypeChange,
    onBaseValueChange,
    onUpdatedValueChange,
    formatValue,
    calculateUpdatedValue,
    showDivider,
    showEntityName,
    showEntityType,
    showCost,
    showRecommendations,
    showIncludeCheckbox,
    isEntityIncluded,
    onEntityInclusionToggle,
    rowSpan,
  }) => {
    const isValueNumeric =
      row.isNumeric && typeof row.attributeValue === "number";
    const isValueNA =
      row.attributeValue === null ||
      row.attributeValue === undefined ||
      row.attributeValue === "N/A";

    return (
      <React.Fragment>
        {showDivider && (
          <TableRow>
            <TableCell colSpan={12} sx={{ p: 0, border: 0 }}>
              <Divider sx={{ my: 0.5 }} />
            </TableCell>
          </TableRow>
        )}
        <TableRow
          sx={
            {
              // backgroundColor: !isEntityIncluded ? "rgba(0, 0, 0, 0.04)" : "inherit",
              // opacity: !isEntityIncluded ? 0.6 : 1,
            }
          }
        >
          {showIncludeCheckbox ? (
            <TableCell rowSpan={rowSpan} sx={{ px: 1, verticalAlign: "top" }}>
              <Checkbox
                checked={isEntityIncluded}
                onChange={() => onEntityInclusionToggle(row.entityId)}
                size="small"
              />
            </TableCell>
          ) : null}
          {showEntityName ? (
            <TableCell
              rowSpan={rowSpan}
              sx={{ fontWeight: 600, py: 0.5, px: 1, verticalAlign: "top" }}
            >
              {row.entityName}
            </TableCell>
          ) : null}
          {showEntityType ? (
            <TableCell
              rowSpan={rowSpan}
              sx={{ py: 0.5, px: 1, verticalAlign: "top" }}
            >
              <Chip label={row.entityType} size="small" />
            </TableCell>
          ) : null}
          {showCost ? (
            <TableCell
              rowSpan={rowSpan}
              sx={{ py: 0.5, px: 1, verticalAlign: "top" }}
            >
              {row.costValue !== null && row.costValue !== undefined ? (
                <Typography variant="body2">
                  {row.costValue.toLocaleString(undefined, {
                    minimumFractionDigits: 2,
                    maximumFractionDigits: 2,
                  })}{" "}
                  {row.costCurrency || "USD"}
                </Typography>
              ) : (
                <Typography variant="body2" color="text.secondary">
                  —
                </Typography>
              )}
            </TableCell>
          ) : null}
          {showRecommendations ? (
            <TableCell
              rowSpan={rowSpan}
              sx={{ py: 0.5, px: 1, verticalAlign: "top", width: "200px" }}
            >
              <RecommendationsCell recommendations={row.recommendations} />
            </TableCell>
          ) : null}
          <TableCell sx={{ py: 0.5, px: 1 }}>
            <FormControl size="small" sx={{ minWidth: 100 }}>
              <Select
                value={currentType}
                onChange={(e) =>
                  onTypeChange(rowKey, e.target.value as "Fixed" | "Floating")
                }
                displayEmpty
              >
                <MenuItem value="Fixed">Fixed</MenuItem>
                <MenuItem value="Floating">Floating</MenuItem>
              </Select>
            </FormControl>
          </TableCell>
          <TableCell sx={{ py: 0.5, px: 1 }}>{row.attributeLabel}</TableCell>
          <TableCell align="right" sx={{ py: 0.5, px: 1 }}>
            {isValueNumeric ? (
              <TextField
                type="number"
                size="small"
                value={
                  currentBaseValue !== null &&
                  typeof currentBaseValue === "number"
                    ? parseFloat(currentBaseValue.toFixed(2))
                    : currentBaseValue ?? ""
                }
                onChange={(e) => {
                  const val =
                    e.target.value === "" ? null : parseFloat(e.target.value);
                  if (val !== null && !isNaN(val)) {
                    // Round to 2 decimal places
                    const roundedVal = Math.round(val * 100) / 100;
                    onBaseValueChange(rowKey, roundedVal);
                  } else {
                    onBaseValueChange(rowKey, null);
                  }
                }}
                inputProps={{
                  step: 0.01,
                }}
                sx={{ width: 120 }}
                disabled={currentType === "Fixed"}
              />
            ) : !isValueNA ? (
              <TextField
                type="text"
                size="small"
                value={currentBaseValue ?? ""}
                onChange={(e) => {
                  onBaseValueChange(rowKey, e.target.value || null);
                }}
                sx={{ width: 120 }}
                disabled={currentType === "Fixed"}
              />
            ) : (
              <Typography variant="body2" color="text.secondary">
                N/A
              </Typography>
            )}
          </TableCell>
          <TableCell sx={{ py: 0.5, px: 1 }}>
            {row.unit ? (
              <Typography variant="body2">{row.unit}</Typography>
            ) : (
              <Typography variant="body2" color="text.secondary">
                —
              </Typography>
            )}
          </TableCell>
          <TableCell sx={{ py: 0.5, px: 1 }}>
            {row.evidenceText || row.confidence !== null ? (
              <Tooltip
                title={
                  <Box>
                    {row.evidenceText && (
                      <Typography
                        variant="caption"
                        display="block"
                        sx={{ mb: 0.5 }}
                      >
                        <strong>Evidence:</strong> {row.evidenceText}
                      </Typography>
                    )}
                    {row.confidence !== null && (
                      <Typography variant="caption" display="block">
                        <strong>Confidence:</strong>{" "}
                        {(row.confidence * 100).toFixed(0)}%
                      </Typography>
                    )}
                  </Box>
                }
                arrow
              >
                <IconButton size="small" sx={{ p: 0.5 }}>
                  <InfoIcon fontSize="small" />
                </IconButton>
              </Tooltip>
            ) : (
              <Typography variant="body2" color="text.secondary">
                —
              </Typography>
            )}
          </TableCell>
          <TableCell align="right" sx={{ py: 0.5, px: 1 }}>
            {isValueNumeric ? (
              <TextField
                type="number"
                size="small"
                value={
                  currentUpdatedValue !== null &&
                  typeof currentUpdatedValue === "number"
                    ? parseFloat(currentUpdatedValue.toFixed(2))
                    : currentUpdatedValue ?? ""
                }
                onChange={(e) => {
                  const val =
                    e.target.value === "" ? null : parseFloat(e.target.value);
                  if (val !== null && !isNaN(val)) {
                    // Round to 2 decimal places
                    const roundedVal = Math.round(val * 100) / 100;
                    onUpdatedValueChange(rowKey, roundedVal);
                  } else {
                    onUpdatedValueChange(rowKey, null);
                  }
                }}
                inputProps={{
                  step: 0.01,
                }}
                sx={{ width: 120 }}
                disabled={currentType === "Fixed"}
                error={
                  currentUpdatedValue !== null &&
                  typeof currentUpdatedValue === "number" &&
                  row.attributeValue !== null &&
                  typeof row.attributeValue === "number" &&
                  (currentUpdatedValue < row.attributeValue * -10 ||
                    currentUpdatedValue > row.attributeValue * 10)
                }
                helperText={
                  currentUpdatedValue !== null &&
                  typeof currentUpdatedValue === "number" &&
                  row.attributeValue !== null &&
                  typeof row.attributeValue === "number" &&
                  (currentUpdatedValue < row.attributeValue * -10 ||
                    currentUpdatedValue > row.attributeValue * 10)
                    ? `Must be between ${(row.attributeValue * -10).toFixed(
                        2
                      )} and ${(row.attributeValue * 10).toFixed(2)}`
                    : ""
                }
              />
            ) : !isValueNA ? (
              <TextField
                type="text"
                size="small"
                value={currentUpdatedValue ?? ""}
                onChange={(e) => {
                  onUpdatedValueChange(rowKey, e.target.value || null);
                }}
                sx={{ width: 120 }}
                disabled={currentType === "Fixed"}
              />
            ) : (
              <Typography variant="body2" color="text.secondary">
                N/A
              </Typography>
            )}
          </TableCell>
        </TableRow>
      </React.Fragment>
    );
  },
  (prevProps, nextProps) => {
    // Custom comparison function
    const propsEqual =
      prevProps.rowKey === nextProps.rowKey &&
      prevProps.currentType === nextProps.currentType &&
      prevProps.currentBaseValue === nextProps.currentBaseValue &&
      prevProps.currentUpdatedValue === nextProps.currentUpdatedValue &&
      prevProps.showDivider === nextProps.showDivider &&
      prevProps.showEntityName === nextProps.showEntityName &&
      prevProps.showEntityType === nextProps.showEntityType &&
      prevProps.showCost === nextProps.showCost &&
      prevProps.showRecommendations === nextProps.showRecommendations &&
      prevProps.showIncludeCheckbox === nextProps.showIncludeCheckbox &&
      prevProps.isEntityIncluded === nextProps.isEntityIncluded &&
      prevProps.rowSpan === nextProps.rowSpan &&
      prevProps.row.entityId === nextProps.row.entityId &&
      prevProps.row.attributeName === nextProps.row.attributeName &&
      prevProps.row.attributeValue === nextProps.row.attributeValue &&
      prevProps.row.unit === nextProps.row.unit;

    return propsEqual;
  }
);

AttributeRowComponent.displayName = "AttributeRowComponent";

/**
 * EntityAttributesWithRecommendations Component
 *
 * Displays entities with their attributes and recommendations in a table format.
 * Each entity's attributes are shown as rows, with recommendations displayed
 * in a single column (same recommendations for all attribute rows of the same entity).
 */
const EntityAttributesWithRecommendations: React.FC<
  EntityAttributesWithRecommendationsProps
> = ({
  scenarioId,
  globalObjectiveType,
  globalObjectiveTarget,
  globalObjectiveUnit,
  onEntitySelectionChange,
}) => {
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [entities, setEntities] = useState<Entity[]>([]);
  const [baseValues, setBaseValues] = useState<
    Record<string, number | string | null>
  >({});
  const [updatedValues, setUpdatedValues] = useState<
    Record<string, number | string | null>
  >({});
  const [attributeTypes, setAttributeTypes] = useState<
    Record<string, "Fixed" | "Floating">
  >({});
  const [includedEntities, setIncludedEntities] = useState<
    Record<string, boolean>
  >({});

  // Fetch entities
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

        const data = await scenarioApi.getEntities(scenarioId, "base_case");
        setEntities(data.entities || []);
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

  // Notify parent of entity selection changes
  useEffect(() => {
    if (onEntitySelectionChange) {
      onEntitySelectionChange(includedEntities);
    }
  }, [includedEntities, onEntitySelectionChange]);

  /**
   * Calculate updated value based on global objective target magnitude
   * Multiplies base capacity value by the +/- of objective change target (magnitude)
   */
  const calculateUpdatedValue = useMemo(() => {
    return (baseValue: number | null): number | null => {
      if (
        baseValue === null ||
        baseValue === undefined ||
        typeof baseValue !== "number"
      ) {
        return null;
      }

      if (!globalObjectiveTarget) {
        return baseValue;
      }

      // Use separate target and unit fields
      if (!globalObjectiveTarget) {
        return baseValue;
      }

      const targetValue = parseFloat(globalObjectiveTarget);
      const targetUnit = globalObjectiveUnit || "%";

      if (isNaN(targetValue)) {
        return baseValue;
      }

      // Determine direction based on objective type
      const isIncrease = globalObjectiveType
        ? globalObjectiveType.toLowerCase().includes("increase") ||
          globalObjectiveType.toLowerCase().includes("improve") ||
          globalObjectiveType.toLowerCase().includes("optimize")
        : true; // Default to increase if unclear

      if (targetUnit === "%") {
        // Percentage change: multiply base value by (1 +/- targetValue/100)
        const multiplier = isIncrease
          ? 1 + targetValue / 100
          : 1 - targetValue / 100;
        const result = baseValue * multiplier;
        // Round to 2 decimal places
        return Math.round(result * 100) / 100;
      } else {
        // Absolute change: add/subtract target value
        const change = isIncrease ? targetValue : -targetValue;
        const result = baseValue + change;
        // Round to 2 decimal places
        return Math.round(result * 100) / 100;
      }
    };
  }, [globalObjectiveTarget, globalObjectiveUnit, globalObjectiveType]);

  /**
   * Extract and flatten attributes from entities
   */
  const attributeRows = useMemo(() => {
    if (!entities.length) {
      return [];
    }

    /**
     * Get the highest priority recommendation relevance for an entity
     * Returns: "primary" | "secondary" | "other" | "none"
     */
    const getHighestRecommendationPriority = (entity: Entity): string => {
      const recommendations = entity.properties?.recommendations || [];
      if (recommendations.length === 0) {
        return "none";
      }

      // Check for primary first
      if (recommendations.some((rec) => rec.relevance === "primary")) {
        return "primary";
      }
      // Check for secondary
      if (recommendations.some((rec) => rec.relevance === "secondary")) {
        return "secondary";
      }
      // Otherwise it's "other"
      return "other";
    };

    // Sort entities: first by recommendation priority, then by entity name
    const sortedEntities = [...entities].sort((a, b) => {
      const priorityA = getHighestRecommendationPriority(a);
      const priorityB = getHighestRecommendationPriority(b);

      // Priority order: primary > secondary > other > none
      const priorityOrder: Record<string, number> = {
        primary: 0,
        secondary: 1,
        other: 2,
        none: 3,
      };

      const priorityDiff = priorityOrder[priorityA] - priorityOrder[priorityB];
      if (priorityDiff !== 0) {
        return priorityDiff;
      }

      // If same priority, sort by entity name
      const nameA = (a.properties?.name || "Unknown Entity").toLowerCase();
      const nameB = (b.properties?.name || "Unknown Entity").toLowerCase();
      return nameA.localeCompare(nameB);
    });

    const rows: AttributeRow[] = [];

    sortedEntities.forEach((entity) => {
      const entityName = entity.properties?.name || "Unknown Entity";
      const entityType = entity.type || "Unknown";
      const recommendations = entity.properties?.recommendations || [];

      // Get attributes from properties.attributes array
      const attributes = entity.properties?.attributes || [];

      // Extract cost information from properties.cost object
      let costValue: number | null = null;
      let costCurrency: string | null = null;

      const costInformation = entity.properties?.cost;
      if (costInformation) {
        // Extract cost_value
        if (
          costInformation.cost_value !== null &&
          costInformation.cost_value !== undefined
        ) {
          if (typeof costInformation.cost_value === "number") {
            costValue = costInformation.cost_value;
          } else if (typeof costInformation.cost_value === "string") {
            const parsed = parseFloat(
              costInformation.cost_value.replace(/[,$]/g, "")
            );
            if (!isNaN(parsed)) {
              costValue = parsed;
            }
          }
        }

        // Extract cost_currency
        if (
          costInformation.cost_currency !== null &&
          costInformation.cost_currency !== undefined
        ) {
          costCurrency = String(costInformation.cost_currency);
        }
      }

      // Add rows for each attribute
      if (attributes.length > 0) {
        attributes.forEach((attr: EntityAttribute, attrIndex: number) => {
          const attrName = attr.name || "";
          const attrValue = attr.value;
          const isNumeric =
            typeof attrValue === "number" && !isNaN(attrValue as number);
          const baseValue = attrValue;
          // Only calculate updated value for numeric attributes
          const updatedValue =
            isNumeric && typeof attrValue === "number"
              ? calculateUpdatedValue(attrValue)
              : null;

          rows.push({
            entityId: entity.id,
            entityName,
            entityType,
            attributeName: attrName,
            attributeLabel: attrName
              .replace(/_/g, " ")
              .replace(/\b\w/g, (l) => l.toUpperCase()),
            attributeValue: attrValue,
            unit: attr.unit || null,
            isNumeric,
            baseValue,
            updatedValue,
            evidenceText: attr.evidence_text || null,
            confidence: attr.confidence !== undefined ? attr.confidence : null,
            recommendations,
            attributeIndex: attrIndex, // Add index to make keys unique
            costValue,
            costCurrency,
          });
        });
      } else {
        // If no attributes found, still create a row to show the entity and recommendations
        rows.push({
          entityId: entity.id,
          entityName,
          entityType,
          attributeName: "N/A",
          attributeLabel: "No attributes",
          attributeValue: null,
          unit: null,
          isNumeric: false,
          baseValue: null,
          updatedValue: null,
          evidenceText: null,
          confidence: null,
          recommendations,
          attributeIndex: 0,
          costValue,
          costCurrency,
        });
      }
    });

    // Rows are already sorted by entity (recommendation priority, then name)
    // and attributes are processed in order, so no additional sorting needed
    return rows;
  }, [entities, calculateUpdatedValue]);

  // Initialize base and updated values when attributeRows change
  useEffect(() => {
    if (attributeRows.length > 0) {
      setBaseValues((prev) => {
        const initialValues: Record<string, number | string | null> = {};
        attributeRows.forEach((row) => {
          const rowKey = `${row.entityId}-${row.attributeName}-${row.attributeIndex}`;
          if (prev[rowKey] === undefined) {
            initialValues[rowKey] = row.baseValue;
          }
        });
        if (Object.keys(initialValues).length > 0) {
          return { ...prev, ...initialValues };
        }
        return prev;
      });

      setUpdatedValues((prev) => {
        const initialValues: Record<string, number | string | null> = {};
        attributeRows.forEach((row) => {
          const rowKey = `${row.entityId}-${row.attributeName}-${row.attributeIndex}`;
          if (prev[rowKey] === undefined) {
            initialValues[rowKey] = row.updatedValue;
          }
        });
        if (Object.keys(initialValues).length > 0) {
          return { ...prev, ...initialValues };
        }
        return prev;
      });

      // Initialize attribute types to "Floating" by default
      setAttributeTypes((prev) => {
        const initialTypes: Record<string, "Fixed" | "Floating"> = {};
        attributeRows.forEach((row) => {
          const rowKey = `${row.entityId}-${row.attributeName}-${row.attributeIndex}`;
          if (prev[rowKey] === undefined) {
            initialTypes[rowKey] = "Floating";
          }
        });
        if (Object.keys(initialTypes).length > 0) {
          return { ...prev, ...initialTypes };
        }
        return prev;
      });

      // Initialize included entities - all unchecked by default
      setIncludedEntities((prev) => {
        const initialIncluded: Record<string, boolean> = {};
        const uniqueEntityIds = new Set(
          attributeRows.map((row) => row.entityId)
        );

        uniqueEntityIds.forEach((entityId) => {
          if (prev[entityId] === undefined) {
            // All entities are unchecked by default
            initialIncluded[entityId] = false;
          }
        });
        if (Object.keys(initialIncluded).length > 0) {
          return { ...prev, ...initialIncluded };
        }
        return prev;
      });
    }
  }, [attributeRows, entities]);

  /**
   * Handle attribute type change
   */
  const handleTypeChange = useCallback(
    (rowKey: string, newType: "Fixed" | "Floating") => {
      setAttributeTypes((prev) => ({
        ...prev,
        [rowKey]: newType,
      }));
    },
    []
  );

  /**
   * Handle base value change
   */
  const handleBaseValueChange = useCallback(
    (rowKey: string, value: number | string | null) => {
      setBaseValues((prev) => ({
        ...prev,
        [rowKey]: value,
      }));
    },
    []
  );

  /**
   * Handle updated value change
   */
  const handleUpdatedValueChange = useCallback(
    (rowKey: string, value: number | string | null) => {
      setUpdatedValues((prev) => ({
        ...prev,
        [rowKey]: value,
      }));
    },
    []
  );

  /**
   * Handle entity inclusion toggle
   */
  const handleEntityInclusionToggle = useCallback((entityId: string) => {
    setIncludedEntities((prev) => ({
      ...prev,
      [entityId]: !prev[entityId],
    }));
  }, []);

  /**
   * Format value for display
   */
  const formatValue = useCallback(
    (value: number | string | null, unit: string | null): string => {
      if (value === null || value === undefined) {
        return "N/A";
      }
      if (typeof value === "number") {
        // Format to 2 decimal places
        const formatted = value.toFixed(2);
        return unit ? `${formatted} ${unit}` : formatted;
      }
      return String(value);
    },
    []
  );

  // Group rows by entity for display
  const groupedRows = useMemo(() => {
    return attributeRows.reduce((acc, row) => {
      if (!acc[row.entityName]) {
        acc[row.entityName] = [];
      }
      acc[row.entityName].push(row);
      return acc;
    }, {} as Record<string, AttributeRow[]>);
  }, [attributeRows]);

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
        <Typography variant="body2" gutterBottom>
          Failed to fetch entities with recommendations.
        </Typography>
        <Typography variant="body2">{error}</Typography>
        <Typography variant="body2" sx={{ mt: 1 }}>
          Please ensure the scenario has been analyzed and entities have been
          extracted.
        </Typography>
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
            Found {entities.length} entities, but none have extractable
            attributes. This may indicate that entities need to be processed or
            attributes need to be extracted from the base case documents.
          </Typography>
        ) : (
          <Typography variant="body2">
            No entities found for this scenario. Please run analysis first to
            generate entities with recommendations.
          </Typography>
        )}
      </Alert>
    );
  }

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        Total entities: {entities.length}
      </Typography>
      <TableContainer component={Paper} variant="outlined">
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell
                sx={{
                  fontWeight: 600,
                  py: 1,
                  px: 1,
                  verticalAlign: "top",
                  width: "50px",
                }}
              >
                Include
              </TableCell>
              <TableCell
                sx={{ fontWeight: 600, py: 1, px: 1, verticalAlign: "top" }}
              >
                Entity Name
              </TableCell>
              <TableCell
                sx={{ fontWeight: 600, py: 1, px: 1, verticalAlign: "top" }}
              >
                Entity Type
              </TableCell>
              <TableCell
                sx={{ fontWeight: 600, py: 1, px: 1, verticalAlign: "top" }}
                align="right"
              >
                Cost
              </TableCell>
              <TableCell
                sx={{ fontWeight: 600, py: 1, px: 1, verticalAlign: "top" }}
              >
                Recommendations
              </TableCell>
              <TableCell
                sx={{ fontWeight: 600, py: 1, px: 1, verticalAlign: "top" }}
              >
                Fixed/Floating
              </TableCell>
              <TableCell
                sx={{ fontWeight: 600, py: 1, px: 1, verticalAlign: "top" }}
              >
                Attribute Name
              </TableCell>
              <TableCell
                sx={{ fontWeight: 600, py: 1, px: 1, verticalAlign: "top" }}
                align="right"
              >
                Attribute Value
              </TableCell>
              <TableCell
                sx={{ fontWeight: 600, py: 1, px: 1, verticalAlign: "top" }}
              >
                Unit
              </TableCell>
              <TableCell
                sx={{ fontWeight: 600, py: 1, px: 1, verticalAlign: "top" }}
              >
                Info
              </TableCell>
              <TableCell
                sx={{ fontWeight: 600, py: 1, px: 1, verticalAlign: "top" }}
                align="right"
              >
                <Box>Revised Values</Box>
                <Box>
                  <Chip
                    label={`Objective: ${globalObjectiveType} ${globalObjectiveTarget}${
                      globalObjectiveUnit || ""
                    }`}
                    size="small"
                    color="primary"
                    variant="outlined"
                    sx={{ fontSize: "0.7rem" }}
                  />
                </Box>
              </TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {Object.entries(groupedRows).map(
              ([entityName, rows], entityIndex) => {
                const firstRow = rows[0];
                const rowSpan = rows.length;

                return (
                  <React.Fragment key={entityName}>
                    {rows.map((row, index) => {
                      // Use attributeIndex to ensure unique keys even if attribute names are duplicated
                      const rowKey = `${row.entityId}-${row.attributeName}-${row.attributeIndex}`;
                      const currentType = attributeTypes[rowKey] || "Floating";
                      const currentBaseValue =
                        baseValues[rowKey] !== undefined
                          ? baseValues[rowKey]
                          : row.baseValue;
                      const currentUpdatedValue =
                        updatedValues[rowKey] !== undefined
                          ? updatedValues[rowKey]
                          : row.updatedValue;
                      // Check if entity is included (defaults to false if not explicitly set)
                      const isEntityIncluded =
                        includedEntities[row.entityId] === true;

                      return (
                        <AttributeRowComponent
                          key={rowKey}
                          row={row}
                          rowKey={rowKey}
                          currentType={currentType}
                          currentBaseValue={currentBaseValue}
                          currentUpdatedValue={currentUpdatedValue}
                          onTypeChange={handleTypeChange}
                          onBaseValueChange={handleBaseValueChange}
                          onUpdatedValueChange={handleUpdatedValueChange}
                          formatValue={formatValue}
                          calculateUpdatedValue={calculateUpdatedValue}
                          showDivider={index === 0 && entityIndex > 0}
                          showEntityName={index === 0}
                          showEntityType={index === 0}
                          showCost={index === 0}
                          showRecommendations={index === 0}
                          showIncludeCheckbox={index === 0}
                          isEntityIncluded={isEntityIncluded}
                          onEntityInclusionToggle={handleEntityInclusionToggle}
                          rowSpan={rowSpan}
                        />
                      );
                    })}
                  </React.Fragment>
                );
              }
            )}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
};

export default EntityAttributesWithRecommendations;
