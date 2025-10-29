import React from "react";
import PropTypes from "prop-types";
import { Box, Card, CardContent, Typography, Grid } from "@mui/material";
import DocumentMetaDataDetails from "./DocumentMetaDataDetails";

const DocumentMetaDataView = ({ documents }) => {
  if (!documents || documents.length === 0) {
    return (
      <Box sx={{ textAlign: "center", py: 4 }}>
        <Typography variant="h6" color="text.secondary">
          No documents available.
        </Typography>
      </Box>
    );
  }

  // Helper function to truncate file names
  const truncateFileName = (fileName) => {
    if (!fileName || fileName.length <= 25) return fileName; // No truncation needed
    const parts = fileName.split(".");
    const extension = parts.length > 1 ? `.${parts.pop()}` : ""; // Extract extension
    const baseName = parts.join("."); // Remaining file name without extension
    return `${baseName.slice(0, 16)}...${baseName.slice(-8)}${extension}`;
  };
  console.log("Documents:", documents);
  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" fontWeight="bold" sx={{ mb: 3 }}>
        Documents Metadata
      </Typography>
      <Grid container spacing={3}>
        {documents.map((document, index) => (
          <Grid item xs={12} sm={6} md={4} key={document.id || index}>
            <Card
              sx={{
                height: "100%",
                display: "flex",
                flexDirection: "column",
                boxShadow: 3,
                "&:hover": { boxShadow: 6 },
                transition: "box-shadow 0.3s",
              }}
            >
              <CardContent>
                <Typography variant="h6" fontWeight="bold" sx={{ mb: 2 }}>
                  {truncateFileName(document.file_name) || `Document ${index + 1}`}
                </Typography>
                <Typography
                  variant="body2"
                  color="text.secondary"
                  sx={{ mb: 2 }}
                >
                  File Size:{" "}
                  {document.file_size
                    ? `${document.file_size} bytes`
                    : "Unknown"}
                </Typography>
                <DocumentMetaDataDetails document={document} />
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>
    </Box>
  );
};

DocumentMetaDataView.propTypes = {
  documents: PropTypes.arrayOf(
    PropTypes.shape({
      id: PropTypes.string,
      filename: PropTypes.string,
      file_size: PropTypes.number,
      meta: PropTypes.oneOfType([PropTypes.object, PropTypes.array]),
    })
  ).isRequired,
};

export default DocumentMetaDataView;
