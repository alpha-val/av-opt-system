import React, { useMemo, useState, useCallback } from "react";
import { useDispatch, useSelector } from "react-redux";
import {
  Box,
  Typography,
  Chip,
  Menu,
  MenuItem,
  ListItemIcon,
  ListItemText,
  IconButton,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Alert,
} from "@mui/material";
import {
  PictureAsPdf as PdfIcon,
  TableChart as XlsIcon,
  Description as CsvIcon,
  InsertDriveFile as FileIcon,
  Download as DownloadIcon,
  Delete as DeleteIcon,
  MoreVert as MoreVertIcon,
} from "@mui/icons-material";
import { selectProjectsError, clearError } from "../../redux/projectsSlice";

export interface DocumentMetadata {
  file_id: string;
  filename: string;
  length: number;
  upload_date: Date | string;
  content_type: string;
  artifact_type: string;
  sha256?: string;
}

interface DocumentListProps {
  baseCaseDocuments?: DocumentMetadata[];
  tabularDataDocuments?: DocumentMetadata[];
  onDownload?: (fileId: string, filename: string) => void;
  onDelete?: (fileId: string) => void;
}

/**
 * Document list component that displays uploaded documents in a table.
 * 
 * Shows base case and tabular data documents with options to download or delete.
 */
const DocumentList: React.FC<DocumentListProps> = ({
  baseCaseDocuments = [],
  tabularDataDocuments = [],
  onDownload,
  onDelete,
}) => {
  const [contextMenu, setContextMenu] = useState<{
    mouseX: number;
    mouseY: number;
  } | null>(null);
  const [selectedDocument, setSelectedDocument] = useState<DocumentMetadata | null>(null);
  const dispatch = useDispatch();
  const error = useSelector(selectProjectsError);

  const handleOptionsClick = useCallback(
    (event: React.MouseEvent, document: DocumentMetadata) => {
      event.preventDefault();
      setSelectedDocument(document);
      setContextMenu({
        mouseX: event.clientX + 2,
        mouseY: event.clientY - 6,
      });
    },
    []
  );

  const handleContextMenuClose = useCallback(() => {
    setContextMenu(null);
    setSelectedDocument(null);
  }, []);

  const handleDownload = useCallback(() => {
    if (selectedDocument && onDownload) {
      onDownload(selectedDocument.file_id, selectedDocument.filename);
      handleContextMenuClose();
    }
  }, [selectedDocument, onDownload, handleContextMenuClose]);

  const handleDelete = useCallback(() => {
    if (selectedDocument && onDelete) {
      onDelete(selectedDocument.file_id);
      handleContextMenuClose();
    }
  }, [selectedDocument, onDelete, handleContextMenuClose]);

  // Format file size
  const formatFileSize = (bytes: number): string => {
    if (!bytes || bytes === 0) return "N/A";
    const k = 1024;
    const sizes = ["Bytes", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
  };

  // Format date for display
  const formatDate = (dateString: Date | string): string => {
    if (!dateString) return "N/A";
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString("en-US", {
        year: "numeric",
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      });
    } catch {
      return String(dateString);
    }
  };

  // Get file type icon
  const getFileIcon = (filename: string, contentType: string) => {
    if (!filename) return <FileIcon />;
    const lowerName = filename.toLowerCase();
    if (lowerName.endsWith(".pdf") || contentType === "application/pdf")
      return <PdfIcon />;
    if (
      lowerName.endsWith(".xls") ||
      lowerName.endsWith(".xlsx") ||
      contentType.includes("spreadsheet")
    )
      return <XlsIcon />;
    if (lowerName.endsWith(".csv") || contentType === "text/csv")
      return <CsvIcon />;
    return <FileIcon />;
  };

  // Get artifact type chip component
  const getArtifactTypeChip = (artifactType: string) => {
    const normalizedType = artifactType ? String(artifactType).trim() : null;

    switch (normalizedType) {
      case "base_case":
        return (
          <Chip
            label="Base Case"
            size="small"
            variant="filled"
            color="default"
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
            color="default"
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

    return allDocuments.map((doc) => ({
      ...doc,
      name: doc.filename || "Unknown",
      size_display: formatFileSize(doc.length),
      upload_date_display: formatDate(doc.upload_date),
      artifact_type_display: getArtifactTypeChip(doc.artifact_type),
      file_icon: getFileIcon(doc.filename, doc.content_type),
    }));
  }, [baseCaseDocuments, tabularDataDocuments]);

  const totalDocuments = baseCaseDocuments.length + tabularDataDocuments.length;

  if (totalDocuments === 0) {
    return (
      <Box sx={{ mt: 3, textAlign: "center", py: 4 }}>
        <Typography variant="body1" color="text.secondary">
          No documents uploaded yet. Use the upload widgets above to add
          documents.
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
        Base Case Reports: {baseCaseDocuments.length} | Tabular Data Files:{" "}
        {tabularDataDocuments.length}
      </Typography>

      {error && (
        <Alert
          severity="error"
          sx={{ mb: 2 }}
          onClose={() => dispatch(clearError())}
        >
          {error}
        </Alert>
      )}

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>File Name</TableCell>
              <TableCell>Type</TableCell>
              <TableCell>Size</TableCell>
              <TableCell>Uploaded</TableCell>
              <TableCell align="right">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {tableData.map((doc) => (
              <TableRow key={doc.file_id} hover>
                <TableCell>
                  <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                    <Box sx={{ color: "text.secondary" }}>{doc.file_icon}</Box>
                    <Typography variant="body2">{doc.name}</Typography>
                  </Box>
                </TableCell>
                <TableCell>{doc.artifact_type_display}</TableCell>
                <TableCell>{doc.size_display}</TableCell>
                <TableCell>{doc.upload_date_display}</TableCell>
                <TableCell align="right">
                  <IconButton
                    size="small"
                    onClick={(e) => handleOptionsClick(e, doc)}
                  >
                    <MoreVertIcon />
                  </IconButton>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Context Menu */}
      <Menu
        open={contextMenu !== null}
        onClose={handleContextMenuClose}
        anchorReference="anchorPosition"
        anchorPosition={
          contextMenu !== null
            ? { top: contextMenu.mouseY, left: contextMenu.mouseX }
            : undefined
        }
        slotProps={{
          paper: {
            sx: {
              minWidth: 120,
            },
          },
        }}
      >
        <MenuItem onClick={handleDownload} disabled={!selectedDocument}>
          <ListItemIcon>
            <DownloadIcon fontSize="small" />
          </ListItemIcon>
          <ListItemText>Download</ListItemText>
        </MenuItem>

        <MenuItem
          onClick={handleDelete}
          disabled={!selectedDocument}
          sx={{
            color: "error.main",
            "&:hover": {
              backgroundColor: "error.veryLight",
            },
          }}
        >
          <ListItemIcon>
            <DeleteIcon fontSize="small" sx={{ color: "inherit" }} />
          </ListItemIcon>
          <ListItemText>Delete</ListItemText>
        </MenuItem>
      </Menu>
    </Box>
  );
};

export default DocumentList;

