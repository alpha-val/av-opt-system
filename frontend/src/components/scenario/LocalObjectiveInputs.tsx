import React, { useEffect, useState, useMemo } from "react";
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
}

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
  console.log("relevantEntities", relevantEntities);
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
  }, [globalObjectiveTarget, globalObjectiveType]);

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
      let attributes: Array<{
        name: string;
        label: string;
        value: number | null;
        unit: string | null;
      }> = [];

      // First, try to get attributes from properties.attributes array
      if (
        entity.properties?.attributes &&
        Array.isArray(entity.properties.attributes)
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

      // Only add rows if entity has attributes
      if (attributes.length > 0) {
        attributes.forEach((attr) => {
          const rowKey = `${entity.id}-${attr.name}`;
          // Use stored redesign value or calculate initial value
          const redesignValue =
            redesignValues[rowKey] !== undefined
              ? redesignValues[rowKey]
              : calculateRedesignValue(attr.value);

          rows.push({
            entityId: entity.id,
            entityName,
            entityType,
            attributeName: attr.name,
            attributeLabel: attr.label,
            attributeValue: attr.value,
            unit: attr.unit || null,
            type: attributeTypes[rowKey] || "Floating", // Default to Floating
            redesignValue,
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
  }, [
    relevantEntities,
    calculateRedesignValue,
    attributeTypes,
    redesignValues,
  ]);

  // Initialize redesign values when relevantEntities change
  useEffect(() => {
    if (relevantEntities.length > 0) {
      setRedesignValues((prev) => {
        const initialValues: Record<string, number | null> = {};

        relevantEntities.forEach((entity) => {
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
  const handleTypeChange = (rowKey: string, newType: "Fixed" | "Floating") => {
    setAttributeTypes((prev) => ({
      ...prev,
      [rowKey]: newType,
    }));
  };

  /**
   * Handle redesign value change
   */
  const handleRedesignValueChange = (rowKey: string, value: number | null) => {
    setRedesignValues((prev) => ({
      ...prev,
      [rowKey]: value,
    }));
  };

  /**
   * Format value for display
   */
  const formatValue = (value: number | null, unit: string | null): string => {
    if (value === null || value === undefined) {
      return "N/A";
    }
    const formatted =
      typeof value === "number" ? value.toLocaleString() : String(value);
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
        Local Objective Inputs
      </Typography>
      <Box sx={{ mb: 3 }}>
        <Typography variant="body2" color="text.secondary" component="div">
          Configure attribute types and review redesign values based on global
          objective target.
        </Typography>
        {globalObjectiveTarget && (
          <Box
            sx={{
              display: "flex",
              flexDirection: "row",
              gap: 1,
              alignItems: "center",
              border: "1px solid",
              borderColor: "divider",
              padding: 1,
              borderRadius: 1,
              marginTop: 1,
            }}
          >
            <Typography variant="body2" color="text.secondary">
              Goal: <strong>{globalObjectiveType}</strong>
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Change by: <strong>{globalObjectiveTarget}</strong>
            </Typography>
          </Box>
        )}
      </Box>

      <TableContainer component={Paper} variant="outlined">
        <Table>
          <TableHead>
            <TableRow>
              <TableCell sx={{ fontWeight: 600 }}>Entity Name</TableCell>
              <TableCell sx={{ fontWeight: 600 }}>Entity Type</TableCell>
              <TableCell sx={{ fontWeight: 600 }}>Attribute Name</TableCell>
              <TableCell sx={{ fontWeight: 600 }}>Fixed/Floating</TableCell>
              <TableCell sx={{ fontWeight: 600 }} align="right">
                Base Case Value
              </TableCell>
              <TableCell sx={{ fontWeight: 600 }} align="right">
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
                    return (
                      <React.Fragment key={rowKey}>
                        {index === 0 && entityIndex > 0 && (
                          <TableRow>
                            <TableCell colSpan={7} sx={{ p: 0, border: 0 }}>
                              <Divider sx={{ my: 1 }} />
                            </TableCell>
                          </TableRow>
                        )}
                        <TableRow>
                          {index === 0 ? (
                            <TableCell
                              rowSpan={rows.length}
                              sx={{ fontWeight: 600 }}
                            >
                              {row.entityName}
                            </TableCell>
                          ) : null}
                          {index === 0 ? (
                            <TableCell rowSpan={rows.length}>
                              <Chip label={row.entityType} size="small" />
                            </TableCell>
                          ) : null}
                          <TableCell>{row.attributeLabel}</TableCell>
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
                            {row.attributeValue !== null ? (
                              <TextField
                                type="number"
                                size="small"
                                value={row.redesignValue ?? ""}
                                onChange={(e) => {
                                  const val =
                                    e.target.value === ""
                                      ? null
                                      : parseFloat(e.target.value);
                                  handleRedesignValueChange(
                                    rowKey,
                                    isNaN(val as number) ? null : val
                                  );
                                }}
                                disabled={row.type === "Fixed"}
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
                                  row.redesignValue !== null &&
                                  row.attributeValue !== null &&
                                  (row.redesignValue <
                                    row.attributeValue * -10 ||
                                    row.redesignValue > row.attributeValue * 10)
                                }
                                helperText={
                                  row.attributeValue !== null &&
                                  row.redesignValue !== null &&
                                  (row.redesignValue <
                                    row.attributeValue * -10 ||
                                    row.redesignValue > row.attributeValue * 10)
                                    ? `Must be between ${
                                        row.attributeValue * -10
                                      } and ${row.attributeValue * 10}`
                                    : row.unit
                                    ? row.unit
                                    : ""
                                }
                              />
                            ) : (
                              formatValue(row.redesignValue, row.unit)
                            )}
                          </TableCell>
                        </TableRow>
                      </React.Fragment>
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
