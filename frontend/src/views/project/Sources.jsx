import React, { useState, useEffect, useMemo, useCallback } from "react";
import { useDispatch, useSelector } from "react-redux";
import { useParams } from "react-router-dom";
import {
  Box,
  Typography,
  Grid,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Button,
  IconButton,
  Chip,
  LinearProgress,
  Alert,
  Snackbar,
} from "@mui/material";
import {
  PictureAsPdf as PdfIcon,
  TableChart as XlsIcon,
  Description as CsvIcon,
  Delete as DeleteIcon,
  CloudUpload as UploadIcon,
  DeleteSweep as ClearAllIcon, // Add this icon
} from "@mui/icons-material";

import FileUpload from "../../components/FileUpload";
import { useDialogs } from "../../hooks/useDialogs/useDialogs";
import {
  fetchProjectDocuments,
  uploadProjectDescription,
  uploadStructuredData,
  deleteProjectDocument,
  clearAllProjectData,
  setCurrentProject,
  clearError,
  selectAllDocuments,
  selectBaseCaseDocuments,
  selectTabularDataDocuments,
  selectBaseCaseCount,
  selectTabularDataCount,
  selectTotalDocumentCount,
  selectDataLoading,
  selectDataError,
  selectDataProgress,
  invalidateEntitiesRelationsCache,
} from "../../redux/dataSlice";

const Sources = () => {
  const { projectId } = useParams();
  const dispatch = useDispatch();

  // Use the useDialogs hook
  const { clearData } = useDialogs();

  // Add state for clearing data
  const [clearingData, setClearingData] = useState(false);

  // Use memoized selectors
  const allDocuments = useSelector(selectAllDocuments);
  const baseCaseDocuments = useSelector(selectBaseCaseDocuments);
  const scenarioDocuments = useSelector(selectTabularDataDocuments);
  const baseCaseCount = useSelector(selectBaseCaseCount);
  const scenarioCount = useSelector(selectTabularDataCount);
  const totalCount = useSelector(selectTotalDocumentCount);
  const loading = useSelector(selectDataLoading);
  const error = useSelector(selectDataError);
  const progress = useSelector(selectDataProgress);

  // Local state
  const [toast, setToast] = useState({
    open: false,
    message: "",
    severity: "success",
  });

  // Load project documents on mount
  useEffect(() => {
    if (projectId && !loading.fetchDocuments) {
      dispatch(setCurrentProject(projectId));
      dispatch(fetchProjectDocuments({ projectId }));
    }
  }, [dispatch, projectId]);

  // Handle base case upload
  const handleBaseCaseUpload = async (files) => {
    for (const fileObj of files) {
      try {
        await dispatch(
          uploadProjectDescription({
            projectId,
            file: fileObj.file,
            metadata: {
              description: `Base case document: ${fileObj.name}`,
            },
          })
        ).unwrap();

        handleUploadSuccess();
      } catch (error) {
        setToast({
          open: true,
          message: `Upload failed: ${error}`,
          severity: "error",
        });
      }
    }
  };

  // Handle scenario data upload
  const handleTabularDataUpload = async (files) => {
    for (const fileObj of files) {
      try {
        await dispatch(
          uploadStructuredData({
            projectId,
            file: fileObj.file,
            metadata: {
              description: `Tabular data: ${fileObj.name}`,
            },
          })
        ).unwrap();

        handleUploadSuccess();
      } catch (error) {
        setToast({
          open: true,
          message: `Upload failed: ${error}`,
          severity: "error",
        });
      }
    }
  };

  // Handle delete - CORRECTED
  const handleDeleteFile = async (docId, fileName) => {
    try {
      // ✅ Use the confirm method correctly
      const confirmed = await clearData(
        `Are you sure you want to delete "${fileName}"?\nAll data items associated with this file will be deleted. This action cannot be undone.`,
        {
          title: "Delete Document",
          okText: "Delete",
          cancelText: "Cancel",
          severity: "warning",
          warningMsg: `You are about to delete a document and all associated data.`,
        }
      );

      if (confirmed) {
        await dispatch(
          deleteProjectDocument({ projectId, docId, hard_delete: true })
        ).unwrap();
        setToast({
          open: true,
          message: `${fileName} deleted successfully`,
          severity: "success",
        });
      }
    } catch (error) {
      setToast({
        open: true,
        message: `Delete failed: ${error}`,
        severity: "error",
      });
    }
  };

  // Handle upload success
  const handleUploadSuccess = useCallback(() => {
    // Invalidate entities/relations cache to force refresh
    dispatch(
      invalidateEntitiesRelationsCache({
        projectId,
        // artifactType: 'base_case'
      })
    );

    // Also refresh documents
    dispatch(
      fetchProjectDocuments({
        projectId,
        // artifact_type: 'base_case'
      })
    );

    setToast({
      open: true,
      message: `Documents uploaded successfully`,
      severity: "success",
    });
  }, [dispatch, projectId]);

  // Handle clear all data
  const handleClearAllData = async () => {
    try {
      const confirmed = await clearData(
        `This will permanently delete all data for this project including:\n\n• All uploaded documents\n• All extracted tables and data\n• All entities and relationships\n• All scenarios\n\nThe project itself will remain, but all its data will be gone.\n\nThis action cannot be undone. Are you absolutely sure?`,
        {
          title: "Clear All Project Data",
          okText: "Yes, Clear All Data",
          cancelText: "Cancel",
          severity: "error",
        }
      );

      if (confirmed) {
        setClearingData(true);

        // Clear all project data
        const result = await dispatch(
          clearAllProjectData({ projectId })
        ).unwrap();

        // Invalidate all caches
        dispatch(invalidateEntitiesRelationsCache({ projectId }));

        // Refresh documents list
        await dispatch(fetchProjectDocuments({ projectId }));

        setClearingData(false);

        setToast({
          open: true,
          message: `Successfully cleared ${result.deleted_counts.total_items} items from project`,
          severity: "success",
        });
      }
    } catch (error) {
      setClearingData(false);
      setToast({
        open: true,
        message: `Failed to clear data: ${error}`,
        severity: "error",
      });
    }
  };

  // Get file icon based on type
  const getFileIcon = (fileType, fileName) => {
    const name = fileName?.toLowerCase() || "";
    const type = fileType?.toLowerCase() || "";

    if (type.includes("pdf") || name.endsWith(".pdf")) {
      return <PdfIcon sx={{ color: "#d32f2f" }} />;
    } else if (
      type.includes("excel") ||
      type.includes("spreadsheet") ||
      name.endsWith(".xlsx") ||
      name.endsWith(".xls")
    ) {
      return <XlsIcon sx={{ color: "#2e7d32" }} />;
    } else if (type.includes("csv") || name.endsWith(".csv")) {
      return <CsvIcon sx={{ color: "#1976d2" }} />;
    }
    return <CsvIcon sx={{ color: "#666" }} />;
  };

  // Format file size
  const formatFileSize = (bytes) => {
    if (!bytes) return "N/A";
    if (bytes === 0) return "0 Bytes";
    const k = 1024;
    const sizes = ["Bytes", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
  };

  // Get file type label
  const getFileTypeLabel = (fileName) => {
    const name = fileName?.toLowerCase() || "";
    if (name.endsWith(".pdf")) return "PDF";
    if (name.endsWith(".xlsx") || name.endsWith(".xls")) return "XLS";
    if (name.endsWith(".csv")) return "CSV";
    return "Unknown";
  };

  // Memoize derived data
  const memoizedBaseCaseDocuments = useMemo(
    () => allDocuments.filter((doc) => doc.artifact_type === "base_case"),
    [allDocuments]
  );

  const memoizedTabularDataDocuments = useMemo(
    () => allDocuments.filter((doc) => doc.artifact_type === "scenario"),
    [allDocuments]
  );

  const memoizedBaseCaseCount = useMemo(
    () => memoizedBaseCaseDocuments.length,
    [memoizedBaseCaseDocuments]
  );

  const memoizedTabularDataCount = useMemo(
    () => memoizedTabularDataDocuments.length,
    [memoizedTabularDataDocuments]
  );

  return (
    <Box>
      <Typography variant="h5" gutterBottom fontWeight="bold">
        Sources
      </Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 0 }}>
        Upload your mining reports, estimation documents, and data tables.
      </Typography>

      {/* Error Alert */}
      {error && (
        <Alert
          severity="error"
          sx={{ mb: 3 }}
          onClose={() => dispatch(clearError())}
        >
          {error}
        </Alert>
      )}

      <Grid
        container
        spacing={3}
        sx={{ justifyContent: "flex-start", flexDirection: "column" }}
      >
        {/* Second Row - Full width table */}
        <Grid xs={12} sx={{ mt: 2, width: "100%" }}>
          <Paper sx={{ p: 3 }}>
            <Box
              sx={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                mb: 2,
              }}
            >
              <Typography variant="h6">All Documents ({totalCount})</Typography>

              {/* Add Clear All Data Button */}
              {allDocuments.length > 0 && (
                <Button
                  variant="outlined"
                  color="error"
                  startIcon={<ClearAllIcon />}
                  onClick={handleClearAllData}
                  disabled={clearingData || loading.deleteDocument}
                  size="small"
                >
                  Clear All Data
                </Button>
              )}
            </Box>

            {allDocuments.length === 0 ? (
              <Box sx={{ textAlign: "center", py: 4 }}>
                <UploadIcon
                  sx={{ fontSize: 48, color: "text.secondary", mb: 2 }}
                />
                <Typography variant="body2" color="text.secondary">
                  No documents uploaded yet. Use the upload sections to add your
                  project files.
                </Typography>
              </Box>
            ) : (
              <TableContainer sx={{ overflow: "auto", width: "100%" }}>
                <Table sx={{ minWidth: 650, width: "100%" }} stickyHeader>
                  <TableHead>
                    <TableRow>
                      <TableCell>File Name</TableCell>
                      <TableCell>Type</TableCell>
                      <TableCell>Size</TableCell>
                      <TableCell>Category</TableCell>
                      <TableCell align="right">Actions</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {allDocuments.map((doc, index) => (
                      <TableRow key={doc.id || `doc-${index}`} hover>
                        <TableCell>
                          <Box
                            sx={{
                              display: "flex",
                              alignItems: "center",
                              gap: 1,
                            }}
                          >
                            {getFileIcon(doc.fileType, doc.fileName)}
                            <Box>
                              <Typography variant="body2" fontWeight="medium">
                                {doc.file_name ||
                                  "Unknown File"}
                              </Typography>
                            </Box>
                          </Box>
                        </TableCell>
                        <TableCell>
                          <Chip
                            label={getFileTypeLabel(doc.file_name)}
                            size="small"
                            variant="outlined"
                          />
                        </TableCell>
                        <TableCell>{formatFileSize(doc.file_size)}</TableCell>
                        <TableCell>
                          <Chip
                            label={
                              doc.artifact_type === "base_case"
                                ? "Base Case"
                                : "Tabular Data"
                            }
                            size="small"
                            color={
                              doc.artifact_type === "base_case"
                                ? "primary"
                                : "secondary"
                            }
                          />
                        </TableCell>
                        <TableCell align="right">
                          <IconButton
                            size="small"
                            onClick={() =>
                              handleDeleteFile(doc.doc_id, doc.fileName)
                            }
                            disabled={loading.deleteDocument}
                            sx={{ color: "error.main" }}
                          >
                            <DeleteIcon />
                          </IconButton>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            )}

            {/* Global upload progress */}
            {(loading.uploadBase ||
              loading.uploadTabularData ||
              clearingData) && (
              <Box sx={{ mt: 2 }}>
                <LinearProgress />
                <Typography
                  variant="caption"
                  color="text.secondary"
                  sx={{ mt: 1, display: "block" }}
                >
                  {clearingData
                    ? "Clearing all data..."
                    : "Uploading files and extracting data..."}
                </Typography>
              </Box>
            )}
          </Paper>
        </Grid>

        {/* First Row - Two columns for uploads */}
        <Box
          sx={{
            maxWidth: 1200,
            mx: "auto",
            mb: 1,
            justifyContent: "flex-start",
          }}
        >
          <Grid container spacing={3} sx={{ justifyContent: "flex-start" }}>
            <Grid xs={12} md={6}>
              <Paper sx={{ p: 2, height: "fit-content" }}>
                <FileUpload
                  title="Upload Base Case Documents"
                  description="Upload PDF Project descriptions, feasibility studies, and reports."
                  supportedTypes={["PDF"]}
                  multiple={true}
                  maxFiles={10}
                  maxSizeInMB={100}
                  onFilesSelected={handleBaseCaseUpload}
                  icon={<PdfIcon />}
                  iconColor="#d32f2f"
                  numberOfFiles={memoizedBaseCaseCount}
                  disabled={loading.uploadBase}
                  showProgress={loading.uploadBase}
                  progress={loading.uploadBase ? progress.upload : 0}
                />
              </Paper>
            </Grid>
            <Grid xs={12} md={6}>
              <Paper sx={{ p: 2, height: "fit-content" }}>
                <FileUpload
                  title="Upload Tabular Data Files"
                  description="Upload PDF, Excel, or CSV files with structured data."
                  supportedTypes={["PDF", "XLS", "CSV"]}
                  multiple={true}
                  maxFiles={20}
                  maxSizeInMB={200}
                  onFilesSelected={handleTabularDataUpload}
                  icon={<XlsIcon />}
                  iconColor="#2e7d32"
                  numberOfFiles={memoizedTabularDataCount}
                  disabled={loading.uploadTabularData}
                  showProgress={loading.uploadTabularData}
                  progress={loading.uploadTabularData ? progress.upload : 0}
                />
              </Paper>
            </Grid>
          </Grid>
        </Box>
      </Grid>

      {/* Toast Notifications */}
      <Snackbar
        open={toast.open}
        autoHideDuration={4000}
        onClose={() => setToast((prev) => ({ ...prev, open: false }))}
        anchorOrigin={{ vertical: "top", horizontal: "right" }}
      >
        <Alert
          onClose={() => setToast((prev) => ({ ...prev, open: false }))}
          severity={toast.severity}
          sx={{ width: "100%" }}
        >
          {toast.message}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default Sources;
