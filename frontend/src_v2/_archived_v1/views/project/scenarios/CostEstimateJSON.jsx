import React from "react";
import { Box, Typography } from "@mui/material";
import ReactJson from "react-json-view";

const CostEstimateJSON = ({ data }) => {
  if (!data) return null;

  return (
    <Box sx={{ p: 2 }}>
      <Typography variant="h6" gutterBottom>
        Cost Estimate JSON
      </Typography>
      <ReactJson
        src={data}
        name={false}
        collapsed={2}
        enableClipboard={true}
        displayDataTypes={false}
        displayObjectSize={false}
        theme="rjv-default"
        style={{ fontSize: 14 }}
      />
    </Box>
  );
};

export default CostEstimateJSON;
