import React, { useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import {
  Box,
  Typography,
  Button,
  CircularProgress,
  Alert,
  Paper,
} from "@mui/material";
import { Refresh as RefreshIcon } from "@mui/icons-material";
import {
  getProjectReport,
  selectProjectReport,
  selectProjectsError,
  clearError,
} from "../../redux/projectsSlice";

interface ReportPreviewContentProps {
  projectId: string;
}

/**
 * Report Preview content component (for embedding in tabs).
 * 
 * This component displays the markdown report for a project.
 * It does not include headers or navigation - those are handled by the parent.
 */
const ReportPreviewContent: React.FC<ReportPreviewContentProps> = ({
  projectId,
}) => {
  const dispatch = useDispatch();
  const reportData = useSelector((state: any) =>
    projectId ? selectProjectReport(projectId)(state) : null
  );
  const loading = useSelector((state: any) => state.projects.loading.getReport);
  const error = useSelector(selectProjectsError);

  // Extract report string from reportData
  const report = reportData?.report || "";

  /**
   * Fetch project report
   */
  const handleFetchReport = (): void => {
    if (projectId) {
      dispatch(getProjectReport(projectId) as any);
    }
  };

  useEffect(() => {
    handleFetchReport();
  }, [projectId, dispatch]);

  return (
    <Box>
      <Box sx={{ display: "flex", justifyContent: "flex-end", mb: 2 }}>
        <Button
          startIcon={<RefreshIcon />}
          onClick={handleFetchReport}
          disabled={loading}
        >
          Refresh
        </Button>
      </Box>

      {/* Error Alert */}
      {error && (
        <Alert
          severity="error"
          sx={{ mb: 2 }}
          onClose={() => dispatch(clearError())}
        >
          {error}
        </Alert>
      )}

      {/* Loading State */}
      {loading ? (
        <Box
          sx={{
            display: "flex",
            justifyContent: "center",
            alignItems: "center",
            minHeight: "400px",
          }}
        >
          <CircularProgress />
        </Box>
      ) : (
        /* Report Content */
        <Paper sx={{ p: 3 }}>
          {report ? (
            <Box
              component="pre"
              sx={{
                whiteSpace: "pre-wrap",
                fontFamily: "monospace",
                fontSize: "0.875rem",
                lineHeight: 1.6,
                overflow: "auto",
                maxHeight: "70vh",
              }}
            >
              {report}
            </Box>
          ) : (
            <Alert severity="info">
              Report not available yet. Generate a report after processing documents.
            </Alert>
          )}
        </Paper>
      )}

      {/* Note about future markdown rendering */}
      <Alert severity="info" sx={{ mt: 2 }}>
        <Typography variant="body2">
          <strong>Note:</strong> This is a placeholder view. Future implementation will
          include proper markdown rendering with syntax highlighting, tables, and
          formatted content.
        </Typography>
      </Alert>
    </Box>
  );
};

export default ReportPreviewContent;

