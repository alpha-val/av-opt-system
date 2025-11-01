import React from "react";
import PropTypes from "prop-types";
import { Box, Typography } from "@mui/material";
import ReactJson from "react-json-view";
import { marked } from "marked";

const MarkdownRenderer = ({ markdown }) => {
  const htmlContent = marked(markdown);

  return <div dangerouslySetInnerHTML={{ __html: htmlContent }} />;
};
const DocumentMetaDataDetails = ({ document }) => {
  console.log("Document:", document);
  if (!document || !document.scenarios) {
    return (
      <Box sx={{ textAlign: "center", py: 4 }}>
        <Typography variant="h6" color="text.secondary">
          No metadata available for this document.
        </Typography>
      </Box>
    );
  }
  return (
    <Box
      sx={{
        p: 1,
        height: 600,
        overflow: "auto",
        border: 0.5,
        borderRadius: 1,
        borderColor: "grey.300",
      }}
    >
      <Typography variant="h5" fontWeight="bold" sx={{ mb: 1 }}>
        Document Summary
      </Typography>
      {document.summaries &&
        document.summaries.map((summary, index) => (
          <Box key={index} sx={{ mb: 2 }}>
            <Typography variant="h6" fontWeight="bold" sx={{ mb: 1 }}>
              Summary {index + 1}
            </Typography>
            {/* <MarkdownRenderer markdown={summary} /> */}
            <ReactJson
              src={summary || { message: "No metadata available" }}
              name={false} // Disable the root name
              theme="monokai" // JSON viewer theme
              collapsed={false} // Expand all nodes by default
              enableClipboard={false} // Allow copying JSON values
              displayDataTypes={false} // Hide data types
              displayObjectSize={false} // Hide object size
              style={{ fontSize: "14px", borderRadius: "4px", padding: "10px" }}
            />
          </Box>
        ))}
    </Box>
  );
};
{
  /* <ReactJson
  src={document.summaries || { message: "No metadata available" }}
  name={false} // Disable the root name
  theme="monokai" // JSON viewer theme
  collapsed={false} // Expand all nodes by default
  enableClipboard={false} // Allow copying JSON values
  displayDataTypes={false} // Hide data types
  displayObjectSize={false} // Hide object size
  style={{ fontSize: "14px", borderRadius: "4px", padding: "10px" }}
/> */
}

DocumentMetaDataDetails.propTypes = {
  document: PropTypes.shape({
    meta: PropTypes.oneOfType([PropTypes.object, PropTypes.array]).isRequired,
  }),
};

export default DocumentMetaDataDetails;
