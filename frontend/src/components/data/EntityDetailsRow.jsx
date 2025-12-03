import React, { useMemo } from "react";
import {
  TableRow,
  TableCell,
  Typography,
  Chip,
  Box,
  Tooltip,
  IconButton,
} from "@mui/material";
import { Info as InfoIcon } from "@mui/icons-material";

const ATTRIBUTE_TYPE_STYLES = {
  base_case: {
    color: "#1b5e20",
    background: "#1b5e2015",
    border: "#1b5e2040",
  },
  tabular_data: {
    color: "#01579b",
    background: "#01579b15",
    border: "#01579b40",
  },
};

const normalizeAttributeType = (value) =>
  (value || "unknown").toString().toLowerCase();

const formatAttributeTypeLabel = (value) => {
  if (!value || value === "unknown") {
    return "Unknown";
  }

  return value
    .split("_")
    .map((segment) => segment.charAt(0).toUpperCase() + segment.slice(1))
    .join(" ");
};

const EntityDetailsRow = ({ entity, index }) => {
  // Note: baseCaseDocuments was removed as documentsSlice doesn't exist
  // The Sources column is commented out, so this is not needed
  const baseCaseDocuments = [];

  // Get entity type color for left border
  const getTypeColor = (type) => {
    const colors = {
      Material: "#1976d2", // Blue
      Equipment: "#9c27b0", // Purple
      Location: "#2e7d32", // Green
      Process: "#ed6c02", // Orange
      Chemical: "#0288d1", // Light Blue
      Commodity: "#d32f2f", // Red
      Project: "#795548", // Brown
      Scenario: "#607d8b", // Blue Grey
      Other: "#757575", // Default grey
    };
    return colors[type] || colors["Other"]; // Default grey
  };

  // Extract main properties
  const entityName = entity.properties?.name || entity.name || "Unnamed Entity";
  const entityDescription = entity.properties?.short_description || "-";
  const entityType = entity.type || "Unknown";
  const confidence = entity.properties?.confidence || entity.confidence;
  const rawAttributeType =
    entity.properties?.attribute_type || entity.attribute_type || "";
  const normalizedAttributeType = normalizeAttributeType(rawAttributeType);
  const attributeTypeLabel = formatAttributeTypeLabel(
    normalizedAttributeType
  );
  const attributeTypeStyles =
    ATTRIBUTE_TYPE_STYLES[normalizedAttributeType] || {
      color: "#424242",
      background: "#eeeeee",
      border: "#bdbdbd",
    };

  // Find the document that this entity belongs to
  const entityDocument = baseCaseDocuments.find(
    (doc) => doc.doc_id === entity.properties.doc_id
  );

  // Extract cost information from properties.cost (new format) or properties.cost (legacy)
  const costInformation = useMemo(() => {
    return entity.properties?.cost || entity.properties?.cost || null;
  }, [entity]);

  // Extract attributes from properties.attributes
  const attributes = useMemo(() => {
    return entity.properties?.attributes || [];
  }, [entity]);

  // Extract other relevant properties (excluding attributes, cost, and metadata)
  const extractOtherProperties = useMemo(() => {
    const excludeFields = new Set([
      "name",
      "type",
      "confidence",
      "short_description",
      "description",
      "project_id",
      "user_id",
      "doc_id",
      "canonical_key",
      "artifact_type",
      "attribute_type",
      "original_id",
      "id",
      "_id",
      "extracted_from",
      "entity_id",
      "sources",
      "attributes",
      "cost",
      "evidence_text",
    ]);

    const allProperties = { ...entity.properties, ...entity };
    const otherProps = Object.entries(allProperties)
      .filter(
        ([key, value]) =>
          !excludeFields.has(key) &&
          value != null &&
          value !== "" &&
          typeof value !== "object"
      )
      .map(([key, value]) => ({ key, value: String(value) }))
      .sort((a, b) => a.key.localeCompare(b.key));

    return otherProps;
  }, [entity]);

  // Format property names for display
  const formatPropertyName = (key) => {
    return key
      .replace(/([A-Z])/g, " $1")
      .replace(/_/g, " ")
      .replace(/\b\w/g, (l) => l.toUpperCase());
  };

  // Format document name for display
  const getDocumentDisplayName = (doc) => {
    if (!doc) return "Unknown Document";
    return (
      doc.originalName ||
      doc.fileName ||
      `Document ${doc.doc_id.substring(0, 8)}...`
    );
  };
  return (
    <TableRow
      hover
      sx={{
        justifyItems: "flex-start",
        borderLeft: `4px solid ${getTypeColor(entityType)}`,
        "&:hover": {
          backgroundColor: "action.hover",
        },
        backgroundColor:
          index % 2 === 0 ? "background.default" : "background.paper",
      }}
    >
      {/* Name Column */}
      <TableCell sx={{ minWidth: 200 }}>
        <Typography variant="body2" fontWeight="medium" sx={{ mb: 0.5 }}>
          {entityName}
        </Typography>
        {entity.properties?.short_description && (
          <Typography variant="caption" color="text.secondary" display="block">
            {entity.properties.short_description.length > 60
              ? `${entity.properties.short_description.substring(0, 80)}...`
              : entity.properties.short_description}
          </Typography>
        )}
      </TableCell>

      {/* Type Column */}
      <TableCell sx={{ minWidth: 100 }}>
        <Chip
          label={entityType}
          size="small"
          sx={{
            backgroundColor: `${getTypeColor(entityType)}20`,
            color: getTypeColor(entityType),
            border: `1px solid ${getTypeColor(entityType)}40`,
            fontWeight: "medium",
          }}
        />
      </TableCell>

      {/* Attribute Type Column */}
      <TableCell sx={{ minWidth: 160 }}>
        {rawAttributeType ? (
          <Chip
            label={attributeTypeLabel}
            size="small"
            sx={{
              backgroundColor: attributeTypeStyles.background,
              color: attributeTypeStyles.color,
              border: `1px solid ${attributeTypeStyles.border}`,
              fontWeight: "medium",
            }}
          />
        ) : (
          <Typography variant="body2" color="text.secondary">
            -
          </Typography>
        )}
      </TableCell>

      {/* Cost Column */}
      <TableCell sx={{ minWidth: 150 }}>
        {costInformation ? (
          <Box>
            {costInformation.cost_value != null ? (
              <Typography variant="body2" fontWeight="medium">
                {costInformation.cost_currency || "USD"} {costInformation.cost_value.toLocaleString()}
                {costInformation.cost_unit && ` / ${costInformation.cost_unit}`}
              </Typography>
            ) : costInformation.cost_min != null || costInformation.cost_max != null ? (
              <Typography variant="body2" fontWeight="medium">
                {costInformation.cost_currency || "USD"}{" "}
                {costInformation.cost_min != null && costInformation.cost_max != null
                  ? `${costInformation.cost_min.toLocaleString()} - ${costInformation.cost_max.toLocaleString()}`
                  : costInformation.cost_min != null
                  ? `≥ ${costInformation.cost_min.toLocaleString()}`
                  : `≤ ${costInformation.cost_max.toLocaleString()}`}
                {costInformation.cost_unit && ` / ${costInformation.cost_unit}`}
              </Typography>
            ) : (
              <Typography variant="body2" color="text.secondary">
                -
              </Typography>
            )}
            {costInformation.cost_type && (
              <Typography variant="caption" color="text.secondary" display="block">
                {costInformation.cost_type}
              </Typography>
            )}
            {costInformation.cost_basis_year && (
              <Typography variant="caption" color="text.secondary" display="block">
                Year: {costInformation.cost_basis_year}
              </Typography>
            )}
            {costInformation.annual_op_cost != null && (
              <Typography variant="caption" color="text.secondary" display="block">
                Annual OPEX: {costInformation.cost_currency || "USD"} {costInformation.annual_op_cost.toLocaleString()}
              </Typography>
            )}
            {costInformation.reclamation_cost != null && (
              <Typography variant="caption" color="text.secondary" display="block">
                Reclamation: {costInformation.cost_currency || "USD"} {costInformation.reclamation_cost.toLocaleString()}
              </Typography>
            )}
          </Box>
        ) : (
          <Typography variant="body2" color="text.secondary">
            -
          </Typography>
        )}
      </TableCell>

      {/* Attributes Column */}
      <TableCell sx={{ minWidth: 250, maxWidth: 300 }}>
        {attributes.length > 0 ? (
          <Box>
            {attributes.map((attr, attrIndex) => (
              <Box
                key={attrIndex}
                sx={{
                  display: "flex",
                  alignItems: "center",
                  flexDirection: "row",
                  justifyContent: "flex-start",
                  gap: 0.5,
                  mb: attrIndex < attributes.length - 1 ? 0.75 : 0,
                  pb: attrIndex < attributes.length - 1 ? 0.75 : 0,
                  borderBottom:
                    attrIndex < attributes.length - 1 ? "1px solid" : "none",
                  borderColor: "divider",
                }}
              >
                <Typography
                  component="span"
                  variant="caption"
                  color="text.secondary"
                  sx={{ fontWeight: 600, display: "block", mb: 0.25, flex: 1 }}
                >
                  {attr.name}:
                </Typography>
                <Typography
                  variant="body2"
                  sx={{
                    fontSize: "0.875rem",
                    fontWeight: 500,
                    display: "block",
                    flex: 1,
                  }}
                >
                  {attr.value != null && attr.value !== "" ? (
                    <>
                      {attr.value}
                      {attr.unit && ` ${attr.unit}`}
                    </>
                  ) : (
                    <Typography
                      component="span"
                      variant="caption"
                      color="text.secondary"
                      sx={{ fontStyle: "italic" }}
                    >
                      No value
                    </Typography>
                  )}
                </Typography>
                {/* {attr.confidence && (
                  <Typography
                    variant="caption"
                    color="text.secondary"
                    sx={{ fontSize: "0.7rem", display: "block", mt: 0.25 }}
                  >
                    Confidence:{" "}
                    {Math.round(parseFloat(attr.confidence) * 100)}%
                  </Typography>
                )} */}
              </Box>
            ))}
          </Box>
        ) : (
          <Typography variant="body2" color="text.secondary">
            -
          </Typography>
        )}
      </TableCell>

      {/* Other Properties Column */}
      <TableCell sx={{ minWidth: 250, maxWidth: 300 }}>
        {extractOtherProperties.length > 0 ? (
          <Box>
            {extractOtherProperties.map(({ key, value }, propIndex) => (
              <Typography
                key={key}
                variant="body2"
                sx={{
                  fontSize: "0.875rem",
                  mb: propIndex < extractOtherProperties.length - 1 ? 0.25 : 0,
                  display: "block",
                }}
              >
                <Typography
                  component="span"
                  variant="caption"
                  color="text.secondary"
                  sx={{ fontWeight: 500 }}
                >
                  {formatPropertyName(key)}:
                </Typography>{" "}
                <Typography component="span" variant="body2">
                  {value.length > 25 ? `${value.substring(0, 25)}...` : value}
                </Typography>
              </Typography>
            ))}
          </Box>
        ) : (
          <Typography variant="body2" color="text.secondary">
            -
          </Typography>
        )}
      </TableCell>

      {/* Evidence Text Column */}
      <TableCell sx={{ minWidth: 50 }} align="center">
        {entity.properties?.evidence_text ? (
          <Tooltip
            title={entity.properties.evidence_text}
            arrow
            placement="left"
          >
            <IconButton size="small" sx={{ color: "primary.main" }}>
              <InfoIcon fontSize="small" />
            </IconButton>
          </Tooltip>
        ) : (
          <Typography variant="body2" color="text.secondary">
            -
          </Typography>
        )}
      </TableCell>

      {/* Sources Column */}
      {/* <TableCell sx={{ minWidth: 180 }}>
        {entityDocument ? (
          <Box sx={{ display: "flex", alignItems: "center", gap: 0.5 }}>
            <Typography
              variant="body2"
              sx={{
                fontSize: "0.8rem",
                wordBreak: "break-word",
              }}
            >
              {getDocumentDisplayName(entityDocument).length > 25
                ? `${getDocumentDisplayName(entityDocument).substring(
                    0,
                    25
                  )}...`
                : getDocumentDisplayName(entityDocument)}
            </Typography>
          </Box>
        ) : (
          <Typography variant="body2" color="text.secondary">
            -
          </Typography>
        )}
      </TableCell> */}

      {/* Confidence Column */}
      <TableCell sx={{ minWidth: 100 }} align="center">
        {confidence ? (
          <Chip
            icon={<InfoIcon sx={{ fontSize: 14 }} />}
            label={`${Math.round(parseFloat(confidence) * 100)}%`}
            size="small"
            variant="outlined"
            color={parseFloat(confidence) > 0.8 ? "success" : "warning"}
            sx={{ fontSize: "0.75rem" }}
          />
        ) : (
          <Typography variant="body2" color="text.secondary">
            -
          </Typography>
        )}
      </TableCell>
    </TableRow>
  );
};

export default EntityDetailsRow;
