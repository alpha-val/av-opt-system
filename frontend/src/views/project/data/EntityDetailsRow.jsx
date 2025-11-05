import React, { useMemo } from "react";
import { useSelector } from "react-redux";
import { TableRow, TableCell, Typography, Chip, Box } from "@mui/material";
import {
  Info as InfoIcon,
  Description as DocumentIcon,
} from "@mui/icons-material";

import { selectBaseCaseDocuments } from "../../../redux/dataSlice";

const EntityDetailsRow = ({ entity, index }) => {
  const baseCaseDocuments = useSelector(selectBaseCaseDocuments);
  console.log("[EntityDetailsRow] entity", entity);
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

  // Find the document that this entity belongs to
  const entityDocument = baseCaseDocuments.find(
    (doc) => doc.doc_id === entity.properties.doc_id
  );

  // Extract cost-related properties
  const extractCostData = useMemo(() => {
    const allProperties = { ...entity.properties, ...entity };
    const costKeywords = [
      "cost",
      "price",
      "capex",
      "opex",
      "expense",
      "budget",
      "investment",
      "expenditure",
      "dollar",
      "usd",
      "$",
    ];

    const costs = Object.entries(allProperties)
      .filter(([key, value]) => {
        const keyLower = key.toLowerCase();
        return (
          costKeywords.some((keyword) => keyLower.includes(keyword)) &&
          value != null &&
          value !== "" &&
          typeof value !== "object"
        );
      })
      .map(([key, value]) => ({ key, value: String(value) }));
    return costs.length > 0 ? costs[0] : null;
  }, [entity]);

  // Extract attributes from properties.attributes
  const attributes = useMemo(() => {
    return entity.properties?.attributes || [];
  }, [entity]);

  // Extract other relevant properties (excluding cost, amount, and metadata)
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
      "original_id",
      "id",
      "_id",
      "extracted_from",
      "entity_id",
      "sources",
      "attributes",
    ]);

    // Also exclude cost field we already extracted
    if (extractCostData) excludeFields.add(extractCostData.key);
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
  }, [entity, extractCostData]);

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

      {/* Cost Column */}
      <TableCell sx={{ minWidth: 120 }}>
        {extractCostData ? (
          <Box>
            <Typography variant="body2" fontWeight="medium">
              {extractCostData.value}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              {formatPropertyName(extractCostData.key)}
            </Typography>
          </Box>
        ) : (
          <Typography variant="body2" color="text.secondary">
            -
          </Typography>
        )}
      </TableCell>

      {/* Other Properties Column */}
      <TableCell sx={{ minWidth: 300, maxWidth: 350 }}>
        <Box>
          {/* Display Attributes */}
          {attributes.length > 0 && (
            <Box sx={{ mb: extractOtherProperties.length > 0 ? 1 : 0 }}>
              {attributes.map((attr, attrIndex) => (
                <Box
                  key={attrIndex}
                  sx={{
                    mb:
                      attrIndex < attributes.length - 1 ||
                      extractOtherProperties.length > 0
                        ? 0.75
                        : 0,
                    pb:
                      attrIndex < attributes.length - 1 ||
                      extractOtherProperties.length > 0
                        ? 0.75
                        : 0,
                    borderBottom:
                      attrIndex < attributes.length - 1 ||
                      (attrIndex === attributes.length - 1 &&
                        extractOtherProperties.length > 0)
                        ? "1px solid"
                        : "none",
                    borderColor: "divider",
                  }}
                >
                  <Typography
                    component="span"
                    variant="caption"
                    color="text.secondary"
                    sx={{ fontWeight: 600, display: "block", mb: 0.25 }}
                  >
                    {attr.name}:
                  </Typography>
                  <Typography
                    variant="body2"
                    sx={{
                      fontSize: "0.875rem",
                      fontWeight: 500,
                      display: "block",
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
                  {attr.confidence && (
                    <Typography
                      variant="caption"
                      color="text.secondary"
                      sx={{ fontSize: "0.7rem", display: "block", mt: 0.25 }}
                    >
                      Confidence:{" "}
                      {Math.round(parseFloat(attr.confidence) * 100)}%
                    </Typography>
                  )}
                </Box>
              ))}
            </Box>
          )}

          {/* Display Other Properties */}
          {extractOtherProperties.length > 0 ? (
            <Box>
              {extractOtherProperties.map(({ key, value }, propIndex) => (
                <Typography
                  key={key}
                  variant="body2"
                  sx={{
                    fontSize: "0.875rem",
                    mb:
                      propIndex < extractOtherProperties.length - 1 ? 0.25 : 0,
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
          ) : attributes.length === 0 ? (
            <Typography variant="body2" color="text.secondary">
              -
            </Typography>
          ) : null}
        </Box>
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
