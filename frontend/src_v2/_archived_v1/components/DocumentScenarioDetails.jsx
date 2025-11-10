import React from "react";
import PropTypes from "prop-types";
import { Box, Typography } from "@mui/material";
import ReactJson from "react-json-view";

const DocumentScenarioDetails = ({ scenario }) => {
  if (!scenario) {
    return (
      <Box sx={{ textAlign: "center", py: 4 }}>
        <Typography variant="h6" color="text.secondary">
          No scenario available for this document.
        </Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 1 }}>
      <Typography variant="h5" fontWeight="bold" sx={{ mb: 1 }}>
        Document Metadata
      </Typography>
      <ReactJson
        src={scenario}
        name={false} // Disable the root name
        theme="monokai" // JSON viewer theme
        collapsed={true} // Expand all nodes by default
        enableClipboard={false} // Allow copying JSON values
        displayDataTypes={false} // Hide data types
        displayObjectSize={false} // Hide object size
        style={{ fontSize: "14px", borderRadius: "4px", padding: "10px" }}
      />
    </Box>
  );
};

DocumentScenarioDetails.propTypes = {
  document: PropTypes.shape({
    scenario: PropTypes.oneOfType([PropTypes.object, PropTypes.array]).isRequired,
  }),
};

export default DocumentScenarioDetails;
