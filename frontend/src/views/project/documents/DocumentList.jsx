import React, { useMemo } from "react";
import { Box, Typography, Chip } from "@mui/material";
import {
  PictureAsPdf as PdfIcon,
  TableChart as XlsIcon,
  Description as CsvIcon,
  InsertDriveFile as FileIcon,
} from "@mui/icons-material";
import DataTable from "../../../components/DataTable";

// Create a component that displays a list of documents
const DocumentList = ({ baseCaseDocuments = [], tabularDataDocuments = [] }) => {
  // Format file size
  const formatFileSize = (bytes) => {
    if (!bytes || bytes === 0) return "N/A";
    const k = 1024;
    const sizes = ["Bytes", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
  };

  // Format date for display
  const formatDate = (dateString) => {
    if (!dateString) return "N/A";
    const date = new Date(dateString);
    const options = {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
      timeZoneName: "short",
    };
    return date.toLocaleString("en-US", options);
  };

  // Get file type icon
  const getFileIcon = (fileName, type) => {
    if (!fileName) return <FileIcon />;
    const lowerName = fileName.toLowerCase();
    if (lowerName.endsWith(".pdf")) return <PdfIcon />;
    if (lowerName.endsWith(".xls") || lowerName.endsWith(".xlsx")) return <XlsIcon />;
    if (lowerName.endsWith(".csv")) return <CsvIcon />;
    if (type === "pdf") return <PdfIcon />;
    return <FileIcon />;
  };

  // Get artifact type chip component
  const getArtifactTypeChip = (artifactType) => {
    // Normalize the artifact type (trim whitespace, handle null/undefined)
    const normalizedType = artifactType ? String(artifactType).trim() : null;
    
    switch (normalizedType) {
      case "base_case":
        return (
          <Chip
            label="Base Case"
            size="small"
            variant="filled"
            color="text.secondary"
            sx={{
              fontWeight: 500,
              "& .MuiChip-label": {
                px: 1,
              },
            }}
          />
        );
      case "tabular_data":
        return (
          <Chip
            label="Tabular Data"
            size="small"
            variant="filled"
            color="text.secondary"
            sx={{
              fontWeight: 500,
              "& .MuiChip-label": {
                px: 1,
              },
            }}
          />
        );
      default:
        return (
          <Chip
            label={normalizedType || "Unknown"}
            size="small"
            variant="outlined"
            sx={{
              fontWeight: 500,
              "& .MuiChip-label": {
                px: 1,
              },
            }}
          />
        );
    }
  };

  // Combine and format documents for table
  const tableData = useMemo(() => {
    const allDocuments = [...baseCaseDocuments, ...tabularDataDocuments];
    
    return allDocuments.map((doc) => {
      // Extract artifact_type value before creating new object
      const artifactType = doc.artifact_type;
      
      // Create new object without artifact_type, then add it back as a chip
      const { artifact_type: _, ...docRest } = doc;
      
      return {
        ...docRest, // Spread rest of doc data (without artifact_type)
        name: doc.file_name || doc.title || "Unknown",
        title: doc.title || doc.file_name || "Unknown",
        type_display: (
          <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
            {getFileIcon(doc.file_name, doc.type)}
            <Typography variant="body2">{doc.type || "Document"}</Typography>
          </Box>
        ),
        artifact_type: getArtifactTypeChip(artifactType), // Chip component replaces string value
        size_display: formatFileSize(doc.size),
        tags_display: doc.tags && doc.tags.length > 0 ? doc.tags : [],
        created_at_display: formatDate(doc.created_at),
        updated_at_display: formatDate(doc.updated_at),
      };
    });
  }, [baseCaseDocuments, tabularDataDocuments]);

  // Table headers
  const headers = useMemo(
    () => [
      { key: "name", display_value: "File Name" },
      { key: "artifact_type", display_value: "Type" },
      { key: "type_display", display_value: "File Type" },
      { key: "size_display", display_value: "Size" },
      { key: "tags_display", display_value: "Tags" },
      { key: "created_at_display", display_value: "Created" },
      { key: "updated_at_display", display_value: "Last Updated" },
    ],
    []
  );

  const totalDocuments = baseCaseDocuments.length + tabularDataDocuments.length;

  if (totalDocuments === 0) {
    return (
      <Box sx={{ mt: 3, textAlign: "center", py: 4 }}>
        <Typography variant="body1" color="text.secondary">
          No documents uploaded yet. Use the upload widgets above to add documents.
        </Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ mt: 3 }}>
      <Typography variant="h6" gutterBottom>
        Uploaded Documents ({totalDocuments})
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        Base Case Reports: {baseCaseDocuments.length} | Tabular Data Files: {tabularDataDocuments.length}
      </Typography>
      <DataTable headers={headers} data={tableData} />
    </Box>
  );
};

export default DocumentList;