import React, { useMemo } from "react";
import { useSelector } from "react-redux";
import { TableRow, TableCell, Typography, Chip, Box } from "@mui/material";
import {
  Info as InfoIcon,
  Description as DocumentIcon,
  TableChart as TableIcon,
} from "@mui/icons-material";

import { selectBaseCaseDocuments } from "../redux/dataSlice";
import { selectTablesByProject } from "../redux/tableDataSlice";

const TableEntityDetailsRow = ({ entity, index, projectId }) => {
  const baseCaseDocuments = useSelector(selectBaseCaseDocuments);
  const tables = useSelector((state) =>
    selectTablesByProject(state, projectId)
  );

  // Get entity type color for left border
  const getTypeColor = (type) => {
    const colors = {
      Material: "#1976d2",
      Equipment: "#9c27b0",
      Location: "#2e7d32",
      Process: "#ed6c02",
      Chemical: "#0288d1",
      Commodity: "#d32f2f",
      Project: "#795548",
      Scenario: "#607d8b",
      Table: "#546e7a",
      TableRow: "#78909c",
    };
    return colors[type] || "#757575";
  };

  // Extract main properties
  const entityName = entity.properties?.name || entity.name || "Unnamed Entity";
  const entityType = entity.type || "Unknown";
  const confidence = entity.properties?.confidence || entity.confidence;
  const rowIndex = entity.properties?.row_index;

  // Find the document and table that this entity belongs to
  const entityDocument = baseCaseDocuments.find(
    (doc) => doc.doc_id === entity.properties?.doc_id
  );
  const sourceTable = tables.find(
    (table) =>
      table.table_id === entity.properties?.source_table_id ||
      table.table_id === entity.properties?.table_id
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
      "capital_cost",
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

  // Extract amount/quantity properties
  const extractAmountData = useMemo(() => {
    const allProperties = { ...entity.properties, ...entity };
    const amountKeywords = [
      "flow_rate",
      "throughput",
      "capacity",
      "volume",
      "quantity",
      "amount",
      "size",
      "weight",
      "mass",
      "count",
      "number",
      "rate",
      "horsepower",
      "hp",
      "dimensions",
    ];

    const amounts = Object.entries(allProperties)
      .filter(([key, value]) => {
        const keyLower = key.toLowerCase();
        return (
          amountKeywords.some((keyword) => keyLower.includes(keyword)) &&
          value != null &&
          value !== "" &&
          typeof value !== "object"
        );
      })
      .map(([key, value]) => ({ key, value: String(value) }));

    return amounts.length > 0 ? amounts[0] : null;
  }, [entity]);

  // Extract other relevant properties
  const extractOtherProperties = useMemo(() => {
    const excludeFields = new Set([
      "id",
      "_id",
      "artifact_type",
      "canonical_key",
      "column_count",
      "confidence",
      "created_at",
      "description",
      "doc_id",
      "entity_id",
      "extracted_from",
      "filename",
      "index",
      "name",
      "page",
      "project_id",
      "row_count",
      "row_index",
      "short_description",
      "source_table_id",
      "sources",
      "table_id",
      "type",
      "updated_at",
      "user_id",
    ]);

    // Also exclude cost and amount fields we already extracted
    if (extractCostData) excludeFields.add(extractCostData.key);
    if (extractAmountData) excludeFields.add(extractAmountData.key);

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
  }, [entity, extractCostData, extractAmountData]);

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

  // Format table name for display
  const getTableDisplayName = (table) => {
    if (!table) return "Unknown Table";
    const fileName = table.filename || "document";
    const page = table.page || 1;
    const index = table.index || 0;
    return `${fileName} - Page ${page}, Table ${index + 1}`;
  };

  return (
    <TableRow
      hover
      sx={{
        borderLeft: `4px solid ${getTypeColor(entityType)}`,
        "&:hover": {
          backgroundColor: "action.hover",
        },
        backgroundColor:
          index % 2 === 0 ? "background.default" : "background.paper",
      }}
    >
      {/* Name Column */}
      <TableCell sx={{ minWidth: 200, verticalAlign: "top" }}>
        <Typography variant="body2" fontWeight="medium" sx={{ mb: 0.5 }}>
          {entityName}
        </Typography>
        {entity.properties?.short_description && (
          <Typography variant="caption" color="text.secondary" display="block">
            {entity.properties.short_description.length > 80
              ? `${entity.properties.short_description.substring(0, 80)}...`
              : entity.properties.short_description}
          </Typography>
        )}
        {rowIndex !== undefined && rowIndex !== null && (
          <Chip
            label={`Row ${rowIndex}`}
            size="small"
            variant="outlined"
            sx={{ mt: 0.5, fontSize: "0.7rem", height: 20 }}
          />
        )}
      </TableCell>

      {/* Type Column */}
      <TableCell sx={{ minWidth: 100, verticalAlign: "top" }}>
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
      <TableCell sx={{ minWidth: 120, verticalAlign: "top" }}>
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

      {/* Amount/Quantity Column */}
      <TableCell sx={{ minWidth: 140, verticalAlign: "top" }}>
        {extractAmountData ? (
          <Box>
            <Typography variant="body2" fontWeight="medium">
              {extractAmountData.value}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              {formatPropertyName(extractAmountData.key)}
            </Typography>
          </Box>
        ) : (
          <Typography variant="body2" color="text.secondary">
            -
          </Typography>
        )}
      </TableCell>

      {/* Other Properties Column */}
      <TableCell sx={{ minWidth: 300, maxWidth: 350, verticalAlign: "top" }}>
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
                  {value}
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

      {/* Source Table Column */}
      <TableCell sx={{ minWidth: 200, verticalAlign: "top" }}>
        {sourceTable ? (
          <Box>
            <Box
              sx={{ display: "flex", alignItems: "center", gap: 0.5, mb: 0.5 }}
            >
              <TableIcon
                fontSize="small"
                sx={{ color: getTypeColor(entityType), flexShrink: 0 }}
              />
              <Typography
                variant="body2"
                sx={{
                  fontSize: "0.8rem",
                  fontWeight: "medium",
                  wordBreak: "break-word",
                }}
              >
                {sourceTable.filename || "Unknown Table"}
              </Typography>
            </Box>
            <Typography
              variant="caption"
              color="text.secondary"
              display="block"
            >
              Page {sourceTable.page}, Table {(sourceTable.index || 0) + 1}
            </Typography>
            <Typography
              variant="caption"
              color="text.secondary"
              display="block"
            >
              {sourceTable.row_count} rows × {sourceTable.column_count} cols
            </Typography>
          </Box>
        ) : (
          <Typography variant="body2" color="text.secondary">
            -
          </Typography>
        )}
      </TableCell>

      {/* Source Document Column */}
      <TableCell sx={{ minWidth: 180, verticalAlign: "top" }}>
        {entityDocument ? (
          <Box sx={{ display: "flex", alignItems: "center", gap: 0.5 }}>
            <DocumentIcon
              fontSize="small"
              sx={{ color: getTypeColor(entityType), flexShrink: 0 }}
            />
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
      </TableCell>

      {/* Confidence Column */}
      <TableCell sx={{ minWidth: 100, verticalAlign: "top" }} align="center">
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

export default TableEntityDetailsRow;
