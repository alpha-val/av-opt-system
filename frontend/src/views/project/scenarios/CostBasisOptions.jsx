import React from "react";
import {
  Box,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Typography,
  Divider,
  Tooltip,
} from "@mui/material";

function parseCostValue(entity) {
  const props = entity.properties || {};
  const v =
    props.cost_value ??
    props.cost ??
    props.unit_cost ??
    entity.cost_value ??
    entity.cost ??
    null;
  if (v === null || v === undefined || v === "") return null;
  const num =
    typeof v === "number" ? v : parseFloat(String(v).replace(/[^0-9.-]+/g, ""));
  return Number.isFinite(num) ? num : null;
}

function getName(entity) {
  if (!entity) return "Unnamed";
  return (
    entity.properties?.name ||
    entity.name ||
    entity.properties?.short_description ||
    "Unnamed"
  );
}

function getType(entity) {
  return entity.type || entity.properties?.type || "Unknown";
}

function renderEntityTooltip(entity) {
  if (!entity) return null;
  const props = entity.properties || {};
  // filter out id/date/time/table/row/col fields and keep only primitive props,
  // then sort keys alphabetically (ascending)
  const visibleProps = Object.entries(props)
    .filter(([k, v]) => {
      const key = String(k).toLowerCase();
      if (
        key.includes("id") ||
        key.includes("created") ||
        key.includes("updated") ||
        key.includes("date") ||
        key.includes("time") ||
        key.includes("table_id") ||
        key.includes("row_index") ||
        key.includes("col_index") ||
        key.includes("original_id")
      ) {
        return false;
      }
      return (
        typeof v === "string" || typeof v === "number" || typeof v === "boolean"
      );
    })
    .sort(([ka], [kb]) => String(ka).localeCompare(String(kb)));

  return (
    <Box sx={{ p: 1, maxWidth: 360 }}>
      <Typography variant="subtitle2" sx={{ fontWeight: 700 }}>
        {getName(entity)}
      </Typography>
      <hr />
      <Typography variant="caption" sx={{ fontWeight: "bold" }} gutterBottom>
        Type: {getType(entity)}
      </Typography>
      {visibleProps.length === 0 ? (
        <Typography variant="body2">No additional properties</Typography>
      ) : (
        visibleProps.map(([k, v]) => (
          <Box key={k} sx={{ display: "flex", gap: 1, mb: 0.5 }}>
            <Typography
              variant="caption"
              sx={{ fontWeight: 600, minWidth: 100 }}
            >
              {k}:
            </Typography>
            <Typography variant="body2" sx={{ wordBreak: "break-word" }}>
              {String(v)}
            </Typography>
          </Box>
        ))
      )}
    </Box>
  );
}

const CostBasisOptions = ({ data }) => {
  if (!data || !data.metadata) return null;

  const costDetails = data.metadata.cost_details || {};
  const matched =
    costDetails.matched_entities || costDetails.matched_data || [];
  console.log("[CostBasisOptions] matched data:", data); // Debug log
  if (!Array.isArray(matched) || matched.length === 0) return null;

  return (
    <Box sx={{ mt: 2 }}>
      <TableContainer component={Paper} variant="outlined">
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell sx={{ py: 0.5, fontWeight: 600 }}>
                <b>Base Case Entities</b>
              </TableCell>
              <TableCell sx={{ py: 0.5, fontWeight: 600 }} align="right">
                <b>Cost</b>
              </TableCell>
              <TableCell sx={{ py: 0.5, fontWeight: 600 }} align="right">
                <b>Capacity</b>
              </TableCell>
              {/* <TableCell sx={{ py: 0.5, fontWeight: 600 }} align="right">
                <b>Capacity Unit</b>
              </TableCell> */}

              <TableCell sx={{ py: 0.5, fontWeight: 600 }}>
                <b>
                  Matching Options (source: tabular data; top 5 matches shown)
                </b>
              </TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {matched.map((row, idx) => {
              const base = row.base_entity || {};
              const tabular = row.tabular_entities || [];
              const baseCost = parseCostValue(base);
              const baseCapacityValue = (() => {
                const props = base.properties || {};
                const v =
                  props.capacity_value ??
                  props.amount_value ??
                  base.capacity_value ??
                  base.amount_value ??
                  null;
                if (v === null || v === undefined || v === "") return null;
                const num =
                  typeof v === "number"
                    ? v
                    : parseFloat(String(v).replace(/[^0-9.-]+/g, ""));
                return Number.isFinite(num) ? num : null;
              })();
              const baseCapacityUnit = (() => {
                const props = base.properties || {};
                return (
                  props.capacity_unit ||
                  props.amount_unit ||
                  base.capacity_unit ||
                  base.amount_unit ||
                  "—"
                );
              })();
              return (
                <TableRow key={base.id || idx}>
                  <TableCell sx={{ backgroundColor: "primary.veryLight" }}>
                    <Tooltip
                      title={renderEntityTooltip(base)}
                      placement="top-start"
                      arrow
                      enterDelay={300}
                      slotProps={{
                        tooltip: {
                          sx: {
                            // semi-transparent black background and overall opacity
                            bgcolor: "rgba(0,0,0,0.85)",
                            opacity: 0.925,
                            // optional: adjust padding / font size
                            p: 1,
                            fontSize: 13,
                          },
                        },
                        arrow: {
                          sx: {
                            // arrow color must match tooltip background
                            color: "rgba(0,0,0,0.85)",
                          },
                        },
                      }}
                    >
                      <span>
                        <Typography
                          variant="body2"
                          sx={{
                            cursor: "help",
                            color: "primary.main",
                            verticalAlign: "top",
                          }}
                        >
                          {getName(base)}
                        </Typography>
                      </span>
                    </Tooltip>
                  </TableCell>
                  <TableCell
                    align="right"
                    sx={{ backgroundColor: "primary.veryLight" }}
                  >
                    <Typography variant="body2">
                      {baseCost !== null
                        ? `$${baseCost.toLocaleString()}`
                        : "—"}
                    </Typography>
                  </TableCell>
                  <TableCell
                    align="right"
                    sx={{ backgroundColor: "primary.veryLight" }}
                  >
                    <Typography variant="body2">
                      {baseCapacityValue !== null
                        ? baseCapacityValue.toLocaleString()
                        : "—"}{" "}
                      {baseCapacityUnit}
                    </Typography>
                  </TableCell>
                  {/* <TableCell
                    align="right"
                    sx={{ backgroundColor: "primary.veryLight" }}
                  >
                    <Typography variant="body2">{baseCapacityUnit}</Typography>
                  </TableCell> */}
                  <TableCell>
                    {tabular.length === 0 ? (
                      <Typography variant="body2" color="textSecondary">
                        No matches
                      </Typography>
                    ) : (
                      <Table size="small" aria-label="matches-mini-table">
                        <TableHead>
                          <TableRow>
                            <TableCell
                              sx={{
                                py: 0.5,
                                fontWeight: 600,
                                borderBottom: "none",
                              }}
                            >
                              Name
                            </TableCell>
                            <TableCell
                              sx={{
                                py: 0.5,
                                fontWeight: 600,
                                borderBottom: "none",
                              }}
                              align="right"
                            >
                              Cost
                            </TableCell>
                            <TableCell
                              sx={{
                                py: 0.5,
                                fontWeight: 600,
                                borderBottom: "none",
                              }}
                              align="right"
                            >
                              Capacity
                            </TableCell>
                            <TableCell
                              sx={{
                                py: 0.5,
                                fontWeight: 600,
                                borderBottom: "none",
                              }}
                              align="right"
                            >
                              Relevance
                            </TableCell>
                          </TableRow>
                        </TableHead>
                        <TableBody>
                          {tabular.map((t) => {
                            const tCost = parseCostValue(t);
                            const relevance =
                              t.relevance_score ??
                              t.properties?.relevance_score ??
                              null;
                            const capacityValue = (() => {
                              const props = t.properties || {};
                              const v =
                                props.capacity_value ??
                                props.amount_value ??
                                t.capacity_value ??
                                t.amount_value ??
                                null;
                              if (v === null || v === undefined || v === "")
                                return null;
                              const num =
                                typeof v === "number"
                                  ? v
                                  : parseFloat(
                                      String(v).replace(/[^0-9.-]+/g, "")
                                    );
                              return Number.isFinite(num) ? num : null;
                            })();
                            const capacityUnit = (() => {
                              const props = t.properties || {};
                              return (
                                props.capacity_unit ||
                                props.amount_unit ||
                                t.capacity_unit ||
                                t.amount_unit ||
                                "—"
                              );
                            })();
                            return (
                              <TableRow key={t.id}>
                                <TableCell
                                  sx={{
                                    py: 0.5,
                                    borderBottom: "none",
                                    verticalAlign: "top",
                                  }}
                                >
                                  <Tooltip
                                    title={renderEntityTooltip(t)}
                                    placement="top-start"
                                    arrow
                                    enterDelay={300}
                                    slotProps={{
                                      tooltip: {
                                        sx: {
                                          bgcolor: "rgba(0,0,0,0.85)",
                                          opacity: 0.925,
                                          p: 1,
                                          fontSize: 13,
                                        },
                                      },
                                      arrow: {
                                        sx: { color: "rgba(0,0,0,0.85)" },
                                      },
                                    }}
                                  >
                                    <span>
                                      <Typography
                                        variant="body2"
                                        sx={{
                                          cursor: "help",
                                          color: "primary.main",
                                        }}
                                      >
                                        {getName(t)}
                                      </Typography>
                                    </span>
                                  </Tooltip>
                                </TableCell>
                                <TableCell
                                  sx={{ py: 0.5, borderBottom: "none" }}
                                  align="right"
                                >
                                  <Typography variant="body2">
                                    {tCost !== null
                                      ? `$${tCost.toLocaleString()}`
                                      : "—"}
                                  </Typography>
                                </TableCell>
                                <TableCell
                                  sx={{ py: 0.5, borderBottom: "none" }}
                                  align="right"
                                >
                                  <Typography variant="body2">
                                    {tCost !== null
                                      ? `${capacityValue.toLocaleString()} ${capacityUnit}`
                                      : "—"}
                                  </Typography>
                                </TableCell>
                                <TableCell
                                  sx={{ py: 0.5, borderBottom: "none" }}
                                  align="right"
                                >
                                  <Typography variant="body2">
                                    {typeof relevance === "number"
                                      ? relevance.toFixed(3)
                                      : "—"}
                                  </Typography>
                                </TableCell>
                              </TableRow>
                            );
                          })}
                        </TableBody>
                      </Table>
                    )}
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
};

export default CostBasisOptions;
