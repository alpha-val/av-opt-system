import React, { useState, useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import {
  Box,
  Paper,
  Typography,
  Button,
  CircularProgress,
  Alert,
  Tabs,
  Tab,
  IconButton,
} from "@mui/material";
import { Download as DownloadIcon } from "@mui/icons-material";
import {
  generateReport,
  selectReportLoading,
  selectScenarioError,
} from "../../../redux/scenarioSlice";

const ReportViewer = ({ scenario }) => {
  const dispatch = useDispatch();
  const loading = useSelector((state) =>
    selectReportLoading(state, scenario.id)
  );
  const error = useSelector(selectScenarioError);
  const [reportData, setReportData] = useState(null);
  const [format, setFormat] = useState("json");

  const handleGenerateReport = async (reportFormat) => {
    try {
      const result = await dispatch(
        generateReport({ scenarioId: scenario.id, format: reportFormat })
      ).unwrap();
      setReportData(result);
      setFormat(reportFormat);
    } catch (err) {
      console.error("Failed to generate report:", err);
    }
  };

  const handleDownload = () => {
    if (!reportData) return;

    const content =
      format === "markdown"
        ? reportData.content
        : JSON.stringify(reportData, null, 2);
    const blob = new Blob([content], {
      type: format === "markdown" ? "text/markdown" : "application/json",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `scenario-${scenario.id}-report.${format === "markdown" ? "md" : "json"}`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <Box>
      <Box sx={{ display: "flex", justifyContent: "space-between", mb: 2 }}>
        <Typography variant="h6">Report</Typography>
        <Box sx={{ display: "flex", gap: 1 }}>
          <Button
            variant="outlined"
            onClick={() => handleGenerateReport("json")}
            disabled={loading.report?.[scenario.id]}
          >
            {loading.report?.[scenario.id] ? (
              <CircularProgress size={16} />
            ) : (
              "Generate JSON"
            )}
          </Button>
          <Button
            variant="outlined"
            onClick={() => handleGenerateReport("markdown")}
            disabled={loading.report?.[scenario.id]}
          >
            {loading.report?.[scenario.id] ? (
              <CircularProgress size={16} />
            ) : (
              "Generate Markdown"
            )}
          </Button>
          {reportData && (
            <IconButton onClick={handleDownload}>
              <DownloadIcon />
            </IconButton>
          )}
        </Box>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {reportData ? (
        <Paper sx={{ p: 3 }}>
          {format === "markdown" ? (
            <pre
              style={{
                whiteSpace: "pre-wrap",
                fontFamily: "monospace",
                fontSize: "0.875rem",
              }}
            >
              {reportData.content}
            </pre>
          ) : (
            <pre
              style={{
                whiteSpace: "pre-wrap",
                fontFamily: "monospace",
                fontSize: "0.875rem",
              }}
            >
              {JSON.stringify(reportData, null, 2)}
            </pre>
          )}
        </Paper>
      ) : (
        <Alert severity="info">
          Generate a report to view scenario analysis results.
        </Alert>
      )}
    </Box>
  );
};

export default ReportViewer;

