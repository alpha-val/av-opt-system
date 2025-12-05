import React, { useState, useCallback, useMemo, useEffect } from "react";
import {
  Box,
  Typography,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Checkbox,
  Chip,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Tooltip,
  Button,
  Grid,
  Divider,
} from "@mui/material";
import {
  ExpandMore as ExpandMoreIcon,
  Info as InfoIcon,
  InfoOutlined as InfoOutlinedIcon,
  Calculate as CalculateIcon,
} from "@mui/icons-material";

// TypeScript interfaces
export interface DecisionLever {
  lever_id: string;
  attribute_name: string;
  category: string;
  baseline_value: string | number | null;
  baseline_unit: string | null;
  baseline_text: string | null;
  description: string | null;
  change_relevance_to_objective: string | null;
  is_discrete: boolean | null;
  options: Array<{ label: string; description: string | null }>;
  plausible_range: {
    min: number | null;
    max: number | null;
    unit: string | null;
    source_text: string | null;
  } | null;
  dependencies: Array<{ type: string | null; description: string | null }>;
}

export interface Component {
  component_id: string;
  role: string;
  msio_discipline: string;
  msio_category: string;
  msio_subcategory: string;
  quantity: number | null;
  relevance_to_objective: string;
  relevance_score: number;
  decision_levers: DecisionLever[];
}

export interface SystemDesignConfig {
  selectedComponents: Record<string, boolean>;
  leverValues: Record<string, string | number | null>;
  leverTypes: Record<string, "Fixed" | "Floating">;
}

interface SystemDesignProps {
  components: Component[];
  onComponentSelectionChange?: (selections: Record<string, boolean>) => void;
  onLeverValueChange?: (
    componentId: string,
    leverId: string,
    value: any,
    type: "Fixed" | "Floating"
  ) => void;
  onEstimateCost?: (config: SystemDesignConfig) => void;
}

/**
 * SystemDesign Component
 *
 * Displays scenario analysis components in accordions with checkboxes,
 * decision lever inputs, and Fixed/Floating controls for cost estimation.
 */
const SystemDesign: React.FC<SystemDesignProps> = ({
  components,
  onComponentSelectionChange,
  onLeverValueChange,
  onEstimateCost,
}) => {
  // State for component selection
  const [componentSelections, setComponentSelections] = useState<
    Record<string, boolean>
  >({});

  // State for lever values (initialized from baseline_value)
  const [leverValues, setLeverValues] = useState<
    Record<string, string | number | null>
  >({});

  // State for lever types (Fixed/Floating) - default to "Floating"
  const [leverTypes, setLeverTypes] = useState<
    Record<string, "Fixed" | "Floating">
  >({});

  // Initialize lever values from baseline_value
  useEffect(() => {
    const initialValues: Record<string, string | number | null> = {};
    const initialTypes: Record<string, "Fixed" | "Floating"> = {};

    components.forEach((component) => {
      component.decision_levers.forEach((lever) => {
        initialValues[lever.lever_id] = lever.baseline_value;
        initialTypes[lever.lever_id] = "Floating";
      });
    });

    setLeverValues(initialValues);
    setLeverTypes(initialTypes);
  }, [components]);

  // Handle component selection change
  const handleComponentSelectionChange = useCallback(
    (componentId: string, checked: boolean) => {
      setComponentSelections((prev) => {
        const updated = { ...prev, [componentId]: checked };
        onComponentSelectionChange?.(updated);
        return updated;
      });
    },
    [onComponentSelectionChange]
  );

  // Handle lever value change
  const handleLeverValueChange = useCallback(
    (componentId: string, leverId: string, value: string | number | null) => {
      setLeverValues((prev) => {
        const updated = { ...prev, [leverId]: value };
        const leverType = leverTypes[leverId] || "Floating";
        onLeverValueChange?.(componentId, leverId, value, leverType);
        return updated;
      });
    },
    [leverTypes, onLeverValueChange]
  );

  // Handle lever type change (Fixed/Floating)
  const handleLeverTypeChange = useCallback(
    (componentId: string, leverId: string, type: "Fixed" | "Floating") => {
      setLeverTypes((prev) => {
        const updated = { ...prev, [leverId]: type };
        const leverValue = leverValues[leverId] ?? null;
        onLeverValueChange?.(componentId, leverId, leverValue, type);
        return updated;
      });
    },
    [leverValues, onLeverValueChange]
  );

  // Handle estimate cost button click
  const handleEstimateCost = useCallback(() => {
    const config: SystemDesignConfig = {
      selectedComponents: componentSelections,
      leverValues,
      leverTypes,
    };
    onEstimateCost?.(config);
  }, [componentSelections, leverValues, leverTypes, onEstimateCost]);

  // Format relevance score with color indicator
  const getRelevanceScoreColor = (score: number): string => {
    if (score >= 0.8) return "#f44336"; // Red for high relevance
    if (score >= 0.5) return "#ff9800"; // Orange for medium relevance
    return "#4caf50"; // Green for low relevance
  };

  // Format value with unit
  const formatValueWithUnit = (
    value: string | number | null,
    unit: string | null
  ): string => {
    if (value === null || value === undefined) return "N/A";
    const valueStr = typeof value === "number" ? value.toString() : value;
    return unit ? `${valueStr} ${unit}` : valueStr;
  };

  // Check if at least one component is selected
  const hasSelectedComponents = useMemo(() => {
    return Object.values(componentSelections).some(
      (selected) => selected === true
    );
  }, [componentSelections]);

  return (
    <Box sx={{ width: "100%" }}>
      <Box
        sx={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          mb: 3,
        }}
      >
        <Typography variant="h5">System Design Configuration</Typography>
        <Tooltip
          title={
            !hasSelectedComponents
              ? "Please select at least one component to estimate cost"
              : ""
          }
          arrow
        >
          <span>
            <Button
              variant="contained"
              color="primary"
              size="small"
              startIcon={<CalculateIcon />}
              onClick={handleEstimateCost}
              disabled={!hasSelectedComponents}
            >
              Estimate Cost
            </Button>
          </span>
        </Tooltip>
      </Box>

      {components.length === 0 ? (
        <Typography variant="body1" color="text.secondary">
          No components available. Please run scenario analysis first.
        </Typography>
      ) : (
        <>
          {components.map((component) => {
            const isSelected =
              componentSelections[component.component_id] || false;

            return (
              <Accordion
                key={component.component_id}
                defaultExpanded={false}
                sx={{ mb: 2 }}
              >
                <AccordionSummary
                  expandIcon={<ExpandMoreIcon />}
                  sx={{
                    "& .MuiAccordionSummary-content": {
                      alignItems: "center",
                      gap: 2,
                    },
                  }}
                >
                  <Checkbox
                    checked={isSelected}
                    onChange={(e) =>
                      handleComponentSelectionChange(
                        component.component_id,
                        e.target.checked
                      )
                    }
                    onClick={(e) => e.stopPropagation()}
                    sx={{ mr: 1 }}
                  />
                  <Typography variant="h6" sx={{ flexGrow: 1 }}>
                    {component.role}
                  </Typography>
                  <Box sx={{ display: "flex", gap: 1, alignItems: "center" }}>
                    <Chip
                      label={component.msio_discipline}
                      size="small"
                      color="primary"
                      variant="outlined"
                    />
                    <Chip
                      label={component.msio_category}
                      size="small"
                      color="secondary"
                      variant="outlined"
                    />
                    <Chip
                      label={component.msio_subcategory}
                      size="small"
                      variant="outlined"
                    />
                    <Box
                      sx={{
                        display: "flex",
                        alignItems: "center",
                        gap: 0.5,
                        px: 1,
                        py: 0.5,
                        borderRadius: 1,
                        bgcolor: "action.hover",
                      }}
                    >
                      <Typography variant="caption" sx={{ fontWeight: 600 }}>
                        Relevance:
                      </Typography>
                      <Typography
                        variant="caption"
                        sx={{
                          fontWeight: 700,
                          color: getRelevanceScoreColor(
                            component.relevance_score
                          ),
                        }}
                      >
                        {component.relevance_score.toFixed(2)}
                      </Typography>
                    </Box>
                    <Tooltip title={component.relevance_to_objective} arrow>
                      <Box
                        component="span"
                        sx={{
                          display: "inline-flex",
                          alignItems: "center",
                          ml: 1,
                          cursor: "help",
                        }}
                        onClick={(e) => e.stopPropagation()}
                      >
                        <InfoIcon fontSize="small" />
                      </Box>
                    </Tooltip>
                  </Box>
                </AccordionSummary>
                <AccordionDetails>
                  <Box sx={{ mt: 2 }}>
                    {component.decision_levers.length === 0 ? (
                      <Typography variant="body2" color="text.secondary">
                        No decision levers available for this component.
                      </Typography>
                    ) : (
                      <Grid container spacing={3}>
                        {component.decision_levers.map((lever) => {
                          const leverValue =
                            leverValues[lever.lever_id] ?? lever.baseline_value;
                          const leverType =
                            leverTypes[lever.lever_id] || "Floating";
                          const isFixed = leverType === "Fixed";
                          const isDiscrete = lever.is_discrete === true;

                          return (
                            <Grid item xs={12} md={6} key={lever.lever_id}>
                              <Box
                                sx={{
                                  p: 2,
                                  border: 1,
                                  borderColor: "divider",
                                  borderRadius: 1,
                                  bgcolor: "background.paper",
                                }}
                              >
                                <Box
                                  sx={{
                                    display: "flex",
                                    alignItems: "center",
                                    gap: 1,
                                    mb: 1.5,
                                  }}
                                >
                                  <Typography
                                    variant="subtitle1"
                                    sx={{ fontWeight: 600 }}
                                  >
                                    {lever.attribute_name}
                                  </Typography>
                                  <Chip
                                    label={lever.category}
                                    size="small"
                                    color="default"
                                    variant="outlined"
                                  />
                                  {lever.change_relevance_to_objective && (
                                    <Tooltip
                                      title={
                                        lever.change_relevance_to_objective
                                      }
                                      arrow
                                    >
                                      <Box
                                        component="span"
                                        sx={{
                                          display: "inline-flex",
                                          alignItems: "center",
                                          cursor: "help",
                                        }}
                                      >
                                        <InfoIcon fontSize="small" />
                                      </Box>
                                    </Tooltip>
                                  )}
                                </Box>

                                {lever.description && (
                                  <Typography
                                    variant="body2"
                                    color="text.secondary"
                                    sx={{ mb: 1.5 }}
                                  >
                                    {lever.description}
                                  </Typography>
                                )}

                                <Box
                                  sx={{
                                    mb: 1,
                                    display: "flex",
                                    alignItems: "center",
                                    gap: 0.5,
                                  }}
                                >
                                  <Typography
                                    variant="caption"
                                    color="text.secondary"
                                  >
                                    Baseline:{" "}
                                    {formatValueWithUnit(
                                      lever.baseline_value,
                                      lever.baseline_unit
                                    )}
                                  </Typography>
                                  {lever.baseline_text && (
                                    <Tooltip title={lever.baseline_text} arrow>
                                      <Box
                                        component="span"
                                        sx={{
                                          display: "inline-flex",
                                          alignItems: "center",
                                          ml: 0.5,
                                          cursor: "help",
                                        }}
                                      >
                                        <InfoOutlinedIcon fontSize="small" />
                                      </Box>
                                    </Tooltip>
                                  )}
                                </Box>

                                <Grid container spacing={2} sx={{ mt: 1 }}>
                                  <Grid item xs={12} sm={isDiscrete ? 6 : 4}>
                                    <FormControl fullWidth size="small">
                                      <InputLabel>Type</InputLabel>
                                      <Select
                                        value={leverType}
                                        onChange={(e) =>
                                          handleLeverTypeChange(
                                            component.component_id,
                                            lever.lever_id,
                                            e.target.value as
                                              | "Fixed"
                                              | "Floating"
                                          )
                                        }
                                        label="Type"
                                      >
                                        <MenuItem value="Floating">
                                          Floating
                                        </MenuItem>
                                        <MenuItem value="Fixed">Fixed</MenuItem>
                                      </Select>
                                    </FormControl>
                                  </Grid>
                                  <Grid item xs={12} sm={isDiscrete ? 6 : 8}>
                                    {isDiscrete ? (
                                      <FormControl
                                        fullWidth
                                        size="small"
                                        disabled={isFixed}
                                      >
                                        <InputLabel>Value</InputLabel>
                                        <Select
                                          value={
                                            leverValue !== null
                                              ? leverValue.toString()
                                              : ""
                                          }
                                          onChange={(e) =>
                                            handleLeverValueChange(
                                              component.component_id,
                                              lever.lever_id,
                                              e.target.value
                                            )
                                          }
                                          label="Value"
                                        >
                                          {lever.options.map((option, idx) => (
                                            <MenuItem
                                              key={idx}
                                              value={option.label}
                                            >
                                              {option.label}
                                              {option.description && (
                                                <Typography
                                                  variant="caption"
                                                  color="text.secondary"
                                                  sx={{ ml: 1 }}
                                                >
                                                  ({option.description})
                                                </Typography>
                                              )}
                                            </MenuItem>
                                          ))}
                                        </Select>
                                      </FormControl>
                                    ) : (
                                      <TextField
                                        fullWidth
                                        size="small"
                                        type="number"
                                        label="Value"
                                        value={
                                          leverValue !== null ? leverValue : ""
                                        }
                                        onChange={(e) => {
                                          const val = e.target.value;
                                          const numVal =
                                            val === "" ? null : parseFloat(val);
                                          handleLeverValueChange(
                                            component.component_id,
                                            lever.lever_id,
                                            numVal
                                          );
                                        }}
                                        disabled={isFixed}
                                        inputProps={{
                                          min:
                                            lever.plausible_range?.min ??
                                            undefined,
                                          max:
                                            lever.plausible_range?.max ??
                                            undefined,
                                          step: "any",
                                        }}
                                        helperText={
                                          lever.plausible_range
                                            ? `Range: ${
                                                lever.plausible_range.min ?? "∞"
                                              } - ${
                                                lever.plausible_range.max ?? "∞"
                                              } ${
                                                lever.plausible_range.unit || ""
                                              }`
                                            : undefined
                                        }
                                      />
                                    )}
                                  </Grid>
                                </Grid>
                              </Box>
                            </Grid>
                          );
                        })}
                      </Grid>
                    )}
                  </Box>
                </AccordionDetails>
              </Accordion>
            );
          })}
        </>
      )}
    </Box>
  );
};

export default SystemDesign;
