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
  Select,
  MenuItem,
  FormControl,
  Divider,
  TextField,
} from "@mui/material";
import { scenarioApi } from "../../services/api";
import { RecommendationsResponse } from "../../types/api";

interface LocalObjectiveInputsProps {
  scenarioId: string;
  globalObjectiveType?: string;
  globalObjectiveTarget?: string;
  globalObjectiveUnit?: string;
  costEstimateId?: string;
}

interface AttributeRow {
  entityId: string;
  entityName: string;
  entityType: string;
  attributeName: string;
  attributeLabel: string;
  attributeValue: number | null;
  unit: string | null;
  type: "Fixed" | "Floating";
  redesignValue: number | null;
  isPlaceholder: boolean;
}

interface AttributeRowComponentProps {
  row: AttributeRow;
  rowKey: string;
  currentType: "Fixed" | "Floating";
  currentRedesignValue: number | null;
  currentPlaceholderText: string;
  onTypeChange: (rowKey: string, newType: "Fixed" | "Floating") => void;
  onRedesignValueChange: (rowKey: string, value: number | null) => void;
  onPlaceholderTextChange: (rowKey: string, value: string) => void;
  formatValue: (value: number | null, unit: string | null) => string;
  calculateRedesignValue: (baseValue: number | null) => number | null;
  showDivider: boolean;
  showEntityName: boolean;
  showEntityType: boolean;
  rowSpan: number;
}

/**
 * Memoized row component to prevent unnecessary re-renders
 * Only re-renders when its own props change
 */
const AttributeRowComponent = memo<AttributeRowComponentProps>(({
  row,
  rowKey,
  currentType,
  currentRedesignValue,
  currentPlaceholderText,
  onTypeChange,
  onRedesignValueChange,
  onPlaceholderTextChange,
  formatValue,
  calculateRedesignValue,
  showDivider,
  showEntityName,
  showEntityType,
  rowSpan,
}) => {
  return (
    <React.Fragment>
      {showDivider && (
        <TableRow>
          <TableCell colSpan={7} sx={{ p: 0, border: 0 }}>
            <Divider sx={{ my: 0.5 }} />
          </TableCell>
        </TableRow>
      )}
      <TableRow>
        {showEntityName ? (
          <TableCell 
            rowSpan={rowSpan} 
            sx={{ fontWeight: 600, py: 0.5, px: 1 }}
          >
            {row.entityName}
          </TableCell>
        ) : null}
        {showEntityType ? (
          <TableCell rowSpan={rowSpan} sx={{ py: 0.5, px: 1 }}>
            <Chip label={row.entityType} size="small" />
          </TableCell>
        ) : null}
        <TableCell sx={{ py: 0.5, px: 1 }}>{row.attributeLabel}</TableCell>
        <TableCell sx={{ py: 0.5, px: 1 }}>
          <FormControl size="small" sx={{ minWidth: 80 }}>
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
        <TableCell align="right" sx={{ py: 0.5, px: 1 }}>
          {row.isPlaceholder
            ? "N/A"
            : formatValue(row.attributeValue, row.unit)}
        </TableCell>
        <TableCell align="right" sx={{ py: 0.5, px: 1 }}>
          {row.isPlaceholder ? (
            <TextField
              type="text"
              size="small"
              value={currentPlaceholderText}
              onChange={(e) => {
                onPlaceholderTextChange(rowKey, e.target.value);
              }}
              disabled={currentType === "Fixed"}
              placeholder="Enter value"
              sx={{ width: 200 }}
            />
          ) : row.attributeValue !== null ? (
            <TextField
              type="number"
              size="small"
              value={currentRedesignValue ?? ""}
              onChange={(e) => {
                const val =
                  e.target.value === "" ? null : parseFloat(e.target.value);
                onRedesignValueChange(
                  rowKey,
                  isNaN(val as number) ? null : val
                );
              }}
              disabled={currentType === "Fixed"}
              inputProps={{
                min:
                  row.attributeValue !== null
                    ? row.attributeValue * -10
                    : undefined,
                max:
                  row.attributeValue !== null
                    ? row.attributeValue * 10
                    : undefined,
                step: "any",
              }}
              sx={{ width: 120 }}
              error={
                currentRedesignValue !== null &&
                row.attributeValue !== null &&
                (currentRedesignValue < row.attributeValue * -10 ||
                  currentRedesignValue > row.attributeValue * 10)
              }
              helperText={
                currentRedesignValue !== null &&
                row.attributeValue !== null &&
                (currentRedesignValue < row.attributeValue * -10 ||
                  currentRedesignValue > row.attributeValue * 10)
                  ? `Must be between ${row.attributeValue * -10} and ${
                      row.attributeValue * 10
                    }`
                  : row.unit
                  ? row.unit
                  : ""
              }
            />
          ) : (
            formatValue(currentRedesignValue, row.unit)
          )}
        </TableCell>
      </TableRow>
    </React.Fragment>
  );
}, (prevProps, nextProps) => {
  // Custom comparison function - return true if props are equal (skip re-render)
  // Return false if props changed (should re-render)
  const propsEqual =
    prevProps.rowKey === nextProps.rowKey &&
    prevProps.currentType === nextProps.currentType &&
    prevProps.currentRedesignValue === nextProps.currentRedesignValue &&
    prevProps.currentPlaceholderText === nextProps.currentPlaceholderText &&
    prevProps.showDivider === nextProps.showDivider &&
    prevProps.showEntityName === nextProps.showEntityName &&
    prevProps.showEntityType === nextProps.showEntityType &&
    prevProps.rowSpan === nextProps.rowSpan &&
    prevProps.row.entityId === nextProps.row.entityId &&
    prevProps.row.attributeName === nextProps.row.attributeName &&
    prevProps.row.attributeValue === nextProps.row.attributeValue &&
    prevProps.row.unit === nextProps.row.unit;
  
  return propsEqual; // true = skip re-render, false = re-render
});

AttributeRowComponent.displayName = "AttributeRowComponent";

/**
 * LocalObjectiveInputs Component
 *
 * Displays entity attributes from relevant_entities in the latest recommendations document.
 * Allows users to configure attribute types (Fixed/Floating) and shows
 * redesign values based on global objective target.
 */
const LocalObjectiveInputs: React.FC<LocalObjectiveInputsProps> = ({
  scenarioId,
  globalObjectiveType,
  globalObjectiveTarget,
  globalObjectiveUnit,
}) => {
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [relevantEntities, setRelevantEntities] = useState<
    Array<{
      id: string;
      type: string;
      properties: {
        name?: string;
        attributes?: Array<{
          name: string;
          value: number | null;
          unit: string | null;
          evidence_text?: string | null;
          confidence?: number;
        }>;
        [key: string]: any;
      };
    }>
  >([]);
  const [attributeTypes, setAttributeTypes] = useState<
    Record<string, "Fixed" | "Floating">
  >({});
  const [redesignValues, setRedesignValues] = useState<
    Record<string, number | null>
  >({});
  const [placeholderTextValues, setPlaceholderTextValues] = useState<
    Record<string, string>
  >({});

  // Fetch recommendations and extract relevant_entities
  useEffect(() => {
    const fetchRelevantEntities = async () => {
      if (!scenarioId) {
        setError("Scenario ID is required");
        setLoading(false);
        return;
      }

      try {
        setLoading(true);
        setError(null);

        // Fetch recommendations
        const recommendationsData = await scenarioApi.getRecommendations(
          scenarioId
        );

        // Get the latest recommendation document
        let latestDoc: any = null;
        if (
          Array.isArray(recommendationsData.recommendations_documents) &&
          recommendationsData.recommendations_documents.length > 0
        ) {
          // Pick the last element from the array
          latestDoc =
            recommendationsData.recommendations_documents[
              recommendationsData.recommendations_documents.length - 1
            ];
        } else if (
          recommendationsData.recommendations_documents &&
          !Array.isArray(recommendationsData.recommendations_documents)
        ) {
          // Handle case where it's a single object
          latestDoc = recommendationsData.recommendations_documents;
        }

        // Extract relevant_entities from latest document or fallback to top-level
        const entities =
          latestDoc?.relevant_entities ||
          recommendationsData.relevant_entities ||
          [];

        setRelevantEntities(entities);
      } catch (err) {
        const errorMessage =
          err instanceof Error
            ? err.message
            : "Failed to fetch relevant entities";
        setError(errorMessage);
        setRelevantEntities([]);
      } finally {
        setLoading(false);
      }
    };

    fetchRelevantEntities();
  }, [scenarioId]);

  /**
   * Calculate redesign value based on global objective target
   */
  const calculateRedesignValue = useMemo(() => {
    return (baseValue: number | null): number | null => {
      if (baseValue === null || baseValue === undefined) {
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
        // Percentage change
        const multiplier = isIncrease
          ? 1 + targetValue / 100
          : 1 - targetValue / 100;
        return baseValue * multiplier;
      } else {
        // Absolute change
        const change = isIncrease ? targetValue : -targetValue;
        return baseValue + change;
      }
    };
  }, [globalObjectiveTarget, globalObjectiveUnit, globalObjectiveType]);

  /**
   * Flatten attributes from relevant_entities
   */
  const attributeRows = useMemo(() => {
    if (!relevantEntities.length) {
      return [];
    }

    const rows: AttributeRow[] = [];

    // Process all relevant entities
    relevantEntities.forEach((entity) => {
      const entityName = entity.properties?.name || "Unknown Entity";
      const entityType = entity.type || "Unknown";
      const isPlaceholder = entity.properties?.is_placeholder === true;
      let attributes: Array<{
        name: string;
        label: string;
        value: number | null;
        unit: string | null;
      }> = [];

      // Handle placeholder entities
      if (isPlaceholder) {
        // For placeholder entities, use expected_attributes
        const expectedAttributes = entity.properties?.expected_attributes || [];
        if (Array.isArray(expectedAttributes) && expectedAttributes.length > 0) {
          expectedAttributes.forEach((attrName: string) => {
            attributes.push({
              name: attrName,
              label: attrName
                .replace(/_/g, " ")
                .replace(/\b\w/g, (l) => l.toUpperCase()),
              value: null, // Placeholder entities have no base values
              unit: null,
            });
          });
        }
      } else {
        // First, try to get attributes from properties.attributes array
        if (
          entity.properties?.attributes &&
          Array.isArray(entity.properties.attributes) &&
          entity.properties.attributes.length > 0
        ) {
          attributes = entity.properties.attributes.map((attr: any) => ({
            name: attr.name,
            label: attr.name, // Use name as label
            value: attr.value,
            unit: attr.unit || null,
          }));
        } else {
          // If no attributes array, check for expected_attributes and try to find matching values
          const expectedAttributes = entity.properties?.expected_attributes || [];

          if (
            Array.isArray(expectedAttributes) &&
            expectedAttributes.length > 0
          ) {
            // For each expected attribute, try to find a matching property value
            expectedAttributes.forEach((attrName: string) => {
              // Try to find a property with this name or similar
              const propValue = entity.properties[attrName];
              if (
                typeof propValue === "number" ||
                (typeof propValue === "string" && !isNaN(parseFloat(propValue)))
              ) {
                const numValue =
                  typeof propValue === "number"
                    ? propValue
                    : parseFloat(propValue);
                if (!isNaN(numValue)) {
                  attributes.push({
                    name: attrName,
                    label: attrName
                      .replace(/_/g, " ")
                      .replace(/\b\w/g, (l) => l.toUpperCase()),
                    value: numValue,
                    unit: null, // Unit not available from property
                  });
                }
              }
            });
          }

          // If still no attributes, try to extract numeric properties (fallback)
          if (attributes.length === 0) {
            const excludedFields = new Set([
              "name",
              "discipline",
              "category",
              "subcategory",
              "entity",
              "confidence",
              "evidence_text",
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
              "is_placeholder",
              "attributes",
            ]);

            Object.entries(entity.properties || {}).forEach(([key, value]) => {
              if (
                !excludedFields.has(key) &&
                (typeof value === "number" ||
                  (typeof value === "string" && !isNaN(parseFloat(value))))
              ) {
                const numValue =
                  typeof value === "number" ? value : parseFloat(value);
                if (!isNaN(numValue)) {
                  attributes.push({
                    name: key,
                    label: key
                      .replace(/_/g, " ")
                      .replace(/\b\w/g, (l) => l.toUpperCase()),
                    value: numValue,
                    unit: null,
                  });
                }
              }
            });
          }
        }
      }

      // Add rows for each attribute (structure only, values read in render)
      if (attributes.length > 0) {
        attributes.forEach((attr) => {
          rows.push({
            entityId: entity.id,
            entityName,
            entityType,
            attributeName: attr.name,
            attributeLabel: attr.label || null,
            attributeValue: attr.value || null,
            unit: attr.unit || null,
            type: "Floating", // Default, will be read from state in render
            redesignValue: null, // Will be read from state in render
            isPlaceholder,
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
  }, [relevantEntities]);

  // Initialize redesign values when relevantEntities change
  useEffect(() => {
    if (relevantEntities.length > 0) {
      setRedesignValues((prev) => {
        const initialValues: Record<string, number | null> = {};

        relevantEntities.forEach((entity) => {
          // Skip placeholder entities - they don't get redesign values
          if (entity.properties?.is_placeholder === true) {
            return;
          }

          let attributes: Array<{ name: string; value: number | null }> = [];

          if (
            entity.properties?.attributes &&
            Array.isArray(entity.properties.attributes)
          ) {
            attributes = entity.properties.attributes.map((attr: any) => ({
              name: attr.name,
              value: attr.value,
            }));
          } else {
            const expectedAttributes =
              entity.properties?.expected_attributes || [];
            if (
              Array.isArray(expectedAttributes) &&
              expectedAttributes.length > 0
            ) {
              expectedAttributes.forEach((attrName: string) => {
                const propValue = entity.properties[attrName];
                if (
                  typeof propValue === "number" ||
                  (typeof propValue === "string" &&
                    !isNaN(parseFloat(propValue)))
                ) {
                  const numValue =
                    typeof propValue === "number"
                      ? propValue
                      : parseFloat(propValue);
                  if (!isNaN(numValue)) {
                    attributes.push({ name: attrName, value: numValue });
                  }
                }
              });
            }
          }

          attributes.forEach((attr) => {
            const rowKey = `${entity.id}-${attr.name}`;
            // Only initialize if not already set
            if (prev[rowKey] === undefined) {
              initialValues[rowKey] = calculateRedesignValue(attr.value);
            }
          });
        });

        if (Object.keys(initialValues).length > 0) {
          return { ...prev, ...initialValues };
        }
        return prev;
      });
    }
  }, [relevantEntities, calculateRedesignValue]);

  /**
   * Handle attribute type change
   */
  const handleTypeChange = useCallback((rowKey: string, newType: "Fixed" | "Floating") => {
    setAttributeTypes((prev) => ({
      ...prev,
      [rowKey]: newType,
    }));
  }, []);

  /**
   * Handle redesign value change
   */
  const handleRedesignValueChange = useCallback((rowKey: string, value: number | null) => {
    setRedesignValues((prev) => ({
      ...prev,
      [rowKey]: value,
    }));
  }, []);

  /**
   * Handle placeholder text value change
   */
  const handlePlaceholderTextChange = useCallback((rowKey: string, value: string) => {
    setPlaceholderTextValues((prev) => ({
      ...prev,
      [rowKey]: value,
    }));
  }, []);
  
  /**
   * Format value for display
   */
  const formatValue = useCallback((value: number | null, unit: string | null): string => {
    if (value === null || value === undefined) {
      return "N/A";
    }
    const formatted =
      typeof value === "number" ? value.toLocaleString() : String(value);
    return unit ? `${formatted} ${unit}` : formatted;
  }, []);

  // Group rows by entity for display (must be before early returns to follow Rules of Hooks)
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
        {relevantEntities.length > 0 ? (
          <Typography variant="body2">
            Found {relevantEntities.length} relevant entities, but none have
            extractable attributes. This may indicate the entities need to be
            processed or attributes need to be extracted.
          </Typography>
        ) : (
          <Typography variant="body2">
            No relevant entities found for this scenario. Please run analysis
            first to generate recommendations and identify relevant entities.
          </Typography>
        )}
      </Alert>
    );
  }
  return (
    <Box>
      <TableContainer component={Paper} variant="outlined">
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell sx={{ fontWeight: 600, py: 1, px: 1 }}>
                Entity Name
              </TableCell>
              <TableCell sx={{ fontWeight: 600, py: 1, px: 1 }}>
                Entity Type
              </TableCell>
              <TableCell sx={{ fontWeight: 600, py: 1, px: 1 }}>
                Attribute Name
              </TableCell>
              <TableCell sx={{ fontWeight: 600, py: 1, px: 1 }}>
                Fixed/Floating
              </TableCell>
              <TableCell sx={{ fontWeight: 600, py: 1, px: 1 }} align="right">
                Base Case Value
              </TableCell>
              <TableCell sx={{ fontWeight: 600, py: 1, px: 1 }} align="right">
                Updated Value (Based on objective target)
              </TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {Object.entries(groupedRows).map(
              ([entityName, rows], entityIndex) => (
                <React.Fragment key={entityName}>
                  {rows.map((row, index) => {
                    const rowKey = `${row.entityId}-${row.attributeName}`;
                    // Read current values from state
                    const currentType = attributeTypes[rowKey] || "Floating";
                    const currentRedesignValue = row.isPlaceholder
                      ? null
                      : redesignValues[rowKey] !== undefined
                      ? redesignValues[rowKey]
                      : calculateRedesignValue(row.attributeValue);
                    const currentPlaceholderText = placeholderTextValues[rowKey] || "";
                    
                    return (
                      <AttributeRowComponent
                        key={rowKey}
                        row={row}
                        rowKey={rowKey}
                        currentType={currentType}
                        currentRedesignValue={currentRedesignValue}
                        currentPlaceholderText={currentPlaceholderText}
                        onTypeChange={handleTypeChange}
                        onRedesignValueChange={handleRedesignValueChange}
                        onPlaceholderTextChange={handlePlaceholderTextChange}
                        formatValue={formatValue}
                        calculateRedesignValue={calculateRedesignValue}
                        showDivider={index === 0 && entityIndex > 0}
                        showEntityName={index === 0}
                        showEntityType={index === 0}
                        rowSpan={rows.length}
                      />
                    );
                  })}
                </React.Fragment>
              )
            )}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
};

export default LocalObjectiveInputs;
