import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  Box,
  Typography,
  Button,
  CircularProgress,
  Alert,
  Paper,
} from "@mui/material";
import {
  ArrowBack as ArrowBackIcon,
  Refresh as RefreshIcon,
} from "@mui/icons-material";
import { projectApi } from "../../services/api";

/**
 * Report Preview component for displaying markdown reports.
 * 
 * This is a placeholder component that will be extended later to:
 * - Fetch markdown report from API
 * - Render markdown with preview (using react-markdown or similar)
 * - Display project details, entities, cost estimates
 * - Support markdown rendering with proper styling
 */
const ReportPreview: React.FC = () => {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  const [report, setReport] = useState<string>("");
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  /**
   * Fetch project report
   */
  const fetchReport = async (): Promise<void> => {
    if (!projectId) return;

    setLoading(true);
    setError(null);
    try {
      const response = await projectApi.getProjectReport(projectId);
      setReport(response.report);
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : "Failed to fetch report";
      setError(errorMessage);
      console.error("Error fetching report:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReport();
  }, [projectId]);

  if (!projectId) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error">Invalid project ID</Alert>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box
        sx={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          mb: 3,
        }}
      >
        <Box sx={{ display: "flex", alignItems: "center", gap: 2 }}>
          <Button
            startIcon={<ArrowBackIcon />}
            onClick={() => navigate("/projects")}
          >
            Back
          </Button>
          <Typography variant="h4" component="h1">
            Project Report
          </Typography>
        </Box>
        <Button
          startIcon={<RefreshIcon />}
          onClick={fetchReport}
          disabled={loading}
        >
          Refresh
        </Button>
      </Box>

      {/* Error Alert */}
      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
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

export default ReportPreview;

