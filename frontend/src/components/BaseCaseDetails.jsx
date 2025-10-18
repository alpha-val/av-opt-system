import React from "react";
import {
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Typography,
  Box,
} from "@mui/material";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import BaseCaseTable from "./BaseCaseTable";

function hasCost(entity) {
  const props = entity.properties || {};

  // Case-insensitive check for "Total Installed Cost" or "Total Capital Cost"
  if (
    entity.type === "Project" &&
    typeof props.name === "string" &&
    [
      "total installed cost",
      "total capital cost",
      "total project cost",
      "total",
    ].some((sub) =>
      props.name.trim().toLowerCase().includes(sub)
    )
  ) {
    return false;
  }
  return (
    entity.cost != null ||
    props.cost != null ||
    props.capital_cost != null ||
    props.cost_value != null ||
    props.price_value != null
  );
}

const BaseCaseDetails = ({ entities = [], cbEntitySelection }) => {
  const baseCaseEntities = entities.filter(
    (e) => e?.properties?.artifact_type === "base_case"
  );

  return (
    <Box>
      <BaseCaseTable entities={baseCaseEntities} onSelectionChange={cbEntitySelection} />
    </Box>
  );
};

export default BaseCaseDetails;
