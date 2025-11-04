import React, { useState, useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import { Box, Typography, Paper, Grid, Alert, Button } from "@mui/material";
import {
  PictureAsPdf as PdfIcon,
  TableChart as XlsIcon,
  DeleteSweep,
} from "@mui/icons-material";
import FileUpload from "../../../components/widgets/FileUpload";
import {
  ingestBaseCaseDocument,
  fetchDocumentsByProject,
  selectDocumentsByProjectAndType,
  selectDocumentsLoading,
  selectDocumentsError,
  selectUploadProgress,
} from "../../../redux/documentSlice";
import { clearAllProjectData } from "../../../redux/dataSlice";
import { useDialogs } from "../../../hooks/useDialogs/useDialogs";
import DocumentList from "../documents/DocumentList.jsx";

const DocumentsTab = ({ projectId }) => {
  const dispatch = useDispatch();
  const dialogs = useDialogs();
  const [uploadError, setUploadError] = useState(null);
  const [uploadSuccess, setUploadSuccess] = useState(null);
  const [uploadingType, setUploadingType] = useState(null); // "base_case" or "tabular_data"
  const [clearingData, setClearingData] = useState(false);

  // Get documents from Redux
  const baseCaseDocuments = useSelector((state) =>
    selectDocumentsByProjectAndType(state, projectId, "base_case")
  );
  const tabularDataDocuments = useSelector((state) =>
    selectDocumentsByProjectAndType(state, projectId, "tabular_data")
  );
  const loading = useSelector(selectDocumentsLoading);
  const error = useSelector(selectDocumentsError);
  const uploadProgress = useSelector(selectUploadProgress);

  const baseCaseUploading = loading.upload && uploadingType === "base_case";
  const tabularDataUploading =
    loading.upload && uploadingType === "tabular_data";

  // Fetch documents on mount
  useEffect(() => {
    if (projectId) {
      dispatch(fetchDocumentsByProject(projectId));
    }
  }, [dispatch, projectId]);

  // Clear error from Redux when component unmounts or error changes
  useEffect(() => {
    if (error) {
      setUploadError(error);
      setTimeout(() => setUploadError(null), 5000);
    }
  }, [error]);

  // Handle base case report upload (PDF only)
  const handleBaseCaseUpload = async (files) => {
    if (!projectId) {
      setUploadError("Project ID is required");
      return;
    }

    setUploadError(null);
    setUploadSuccess(null);
    setUploadingType("base_case");

    try {
      // Upload each file
      for (const fileObj of files) {
        const result = await dispatch(
          ingestBaseCaseDocument({
            file: fileObj.file,
            projectId: projectId,
            artifactType: "base_case",
            metadata: {
              title: fileObj.name,
              tags: ["base-case", "report"],
            },
          })
        ).unwrap();

        console.log("Base case report uploaded:", result);
      }

      setUploadSuccess(
        `Successfully uploaded ${files.length} base case report(s)`
      );

      // Refresh documents list
      dispatch(fetchDocumentsByProject(projectId));

      // Clear success message after 5 seconds
      setTimeout(() => setUploadSuccess(null), 5000);
    } catch (error) {
      console.error("Base case upload error:", error);
      setUploadError(
        `Failed to upload base case reports: ${error.message || error}`
      );
      setTimeout(() => setUploadError(null), 5000);
    } finally {
      setUploadingType(null);
    }
  };

  // Handle tabular data files upload (PDF, XLS, CSV)
  const handleTabularDataUpload = async (files) => {
    if (!projectId) {
      setUploadError("Project ID is required");
      return;
    }

    setUploadError(null);
    setUploadSuccess(null);
    setUploadingType("tabular_data");

    try {
      // Upload each file
      for (const fileObj of files) {
        const result = await dispatch(
          uploadDocument({
            file: fileObj.file,
            projectId: projectId,
            artifactType: "tabular_data",
            metadata: {
              title: fileObj.name,
              type: fileObj.type === "PDF" ? "pdf" : "spreadsheet",
              tags: ["tabular-data"],
            },
          })
        ).unwrap();

        console.log("Tabular data file uploaded:", result);
      }

      setUploadSuccess(
        `Successfully uploaded ${files.length} tabular data file(s)`
      );

      // Refresh documents list
      dispatch(fetchDocumentsByProject(projectId));

      // Clear success message after 5 seconds
      setTimeout(() => setUploadSuccess(null), 5000);
    } catch (error) {
      console.error("Tabular data upload error:", error);
      setUploadError(
        `Failed to upload tabular data files: ${error.message || error}`
      );
      setTimeout(() => setUploadError(null), 5000);
    } finally {
      setUploadingType(null);
    }
  };

  // Handle rejected files
  const handleFilesRejected = (rejectedFiles) => {
    console.warn("Files rejected:", rejectedFiles);
    const reasons = rejectedFiles
      .map((f) => `${f.name}: ${f.reason}`)
      .join(", ");
    setUploadError(`Some files were rejected: ${reasons}`);
    setTimeout(() => setUploadError(null), 5000);
  };

  // Handle clear all project data
  const handleClearAllData = async () => {
    if (!projectId) {
      setUploadError("Project ID is required");
      return;
    }

    const confirmed = await dialogs.clearData(
      "This will permanently delete ALL project data including documents, entities, scenarios, tables, and all associated data. This action cannot be undone.",
      {
        title: "Clear All Project Data",
        warningMsg: "This action will permanently delete ALL data associated with this project, including:",
        msg: "All documents, entities, relations, scenarios, tables, cost estimates, and vector embeddings will be deleted. This action cannot be undone. Are you absolutely sure?",
        okText: "Clear All Data",
        cancelText: "Cancel",
        severity: "error",
      }
    );

    if (!confirmed) {
      return;
    }

    setClearingData(true);
    setUploadError(null);
    setUploadSuccess(null);

    try {
      const result = await dispatch(
        clearAllProjectData({ projectId })
      ).unwrap();

      const total = result.deleted_counts?.total_items || 0;
      setUploadSuccess(
        `Successfully cleared all project data. Deleted ${total} items.`
      );

      // Refresh documents list
      dispatch(fetchDocumentsByProject(projectId));

      // Clear success message after 5 seconds
      setTimeout(() => setUploadSuccess(null), 5000);
    } catch (error) {
      console.error("Clear project data error:", error);
      setUploadError(
        `Failed to clear project data: ${error.message || error}`
      );
      setTimeout(() => setUploadError(null), 5000);
    } finally {
      setClearingData(false);
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", mb: 1 }}>
        <Box>
          <Typography variant="h5" gutterBottom>
            Project Documents
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Upload base case reports and tabular data files for your project.
          </Typography>
        </Box>
        <Button
          variant="outlined"
          color="error"
          startIcon={<DeleteSweep />}
          onClick={handleClearAllData}
          disabled={clearingData || baseCaseUploading || tabularDataUploading}
          sx={{ ml: "auto", minWidth: "200px" }}
        >
          {clearingData ? "Clearing..." : "Clear All Project Data"}
        </Button>
      </Box>

      {/* Error Alert */}
      {uploadError && (
        <Alert
          severity="error"
          sx={{ mb: 2 }}
          onClose={() => setUploadError(null)}
        >
          {uploadError}
        </Alert>
      )}

      {/* Success Alert */}
      {uploadSuccess && (
        <Alert
          severity="success"
          sx={{ mb: 2 }}
          onClose={() => setUploadSuccess(null)}
        >
          {uploadSuccess}
        </Alert>
      )}

      {/* Upload Widgets */}
      <Grid container spacing={3}>
        {/* Base Case Reports Upload */}
        <Grid size={{ xs: 12, md: 6 }}>
          <Paper elevation={1} sx={{ p: 2, height: "100%" }}>
            <FileUpload
              title="Upload Base Case Reports"
              description="Upload PDF feasibility studies, project descriptions, and base case reports."
              supportedTypes={["PDF"]}
              multiple={true}
              maxFiles={10}
              maxSizeInMB={100}
              onFilesSelected={handleBaseCaseUpload}
              onFilesRejected={handleFilesRejected}
              icon={<PdfIcon />}
              iconColor="#d32f2f"
              numberOfFiles={baseCaseDocuments.length}
              disabled={baseCaseUploading || tabularDataUploading}
              showProgress={baseCaseUploading}
              progress={uploadProgress}
              variant="outlined"
              buttonVariant="contained"
              buttonText="Browse Reports"
            />
          </Paper>
        </Grid>

        {/* Tabular Data Files Upload */}
        <Grid size={{ xs: 12, md: 6 }}>
          <Paper elevation={1} sx={{ p: 2, height: "100%" }}>
            <FileUpload
              title="Upload Tabular Data Files"
              description="Upload PDF, Excel (XLS/XLSX), or CSV files containing structured data and tables."
              supportedTypes={["PDF", "XLS", "CSV"]}
              multiple={true}
              maxFiles={20}
              maxSizeInMB={200}
              onFilesSelected={handleTabularDataUpload}
              onFilesRejected={handleFilesRejected}
              icon={<XlsIcon />}
              iconColor="#2e7d32"
              numberOfFiles={tabularDataDocuments.length}
              disabled={baseCaseUploading || tabularDataUploading}
              showProgress={tabularDataUploading}
              progress={uploadProgress}
              variant="outlined"
              buttonVariant="contained"
              buttonText="Browse Data Files"
            />
          </Paper>
        </Grid>
      </Grid>

      {/* Documents List */}
      <Box sx={{ mt: 3 }}>
        <DocumentList 
          baseCaseDocuments={baseCaseDocuments}
          tabularDataDocuments={tabularDataDocuments}
        />
      </Box>
    </Box>
  );
};

export default DocumentsTab;

