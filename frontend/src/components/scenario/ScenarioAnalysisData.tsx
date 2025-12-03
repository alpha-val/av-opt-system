import React, { useCallback, useEffect, useMemo, useState } from "react";
import {
  Alert,
  Box,
  Chip,
  CircularProgress,
  Divider,
  IconButton,
  Paper,
  Stack,
  Tooltip,
  Typography,
} from "@mui/material";
import RefreshIcon from "@mui/icons-material/Refresh";
import ReactJson from "react-json-view";

import { scenarioApi } from "../../services/api";
import { ScenarioAnalysisResult } from "../../types/api";

interface ScenarioAnalysisDataProps {
  scenarioId: string;
  workflow?: string;
}

const formatDateTime = (value?: string | null): string => {
  if (!value) return "N/A";
  const date = new Date(value);
  return Number.isNaN(date.getTime())
    ? value
    : date.toLocaleString(undefined, {
        year: "numeric",
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
      });
};

const formatErrorMessage = (error: unknown): string => {
  if (!error) return "Unknown error";
  if (typeof error === "string") return error;
  if (error instanceof Error) return error.message;

  const responseDetail =
    (error as any)?.response?.data?.detail ?? (error as any)?.detail;
  if (typeof responseDetail === "string") return responseDetail;
  if (responseDetail && typeof responseDetail === "object") {
    try {
      return JSON.stringify(responseDetail);
    } catch {
      return "Failed to fetch analysis data";
    }
  }

  try {
    return JSON.stringify(error);
  } catch {
    return "Failed to fetch analysis data";
  }
};

const ScenarioAnalysisData: React.FC<ScenarioAnalysisDataProps> = ({
  scenarioId,
  workflow,
}) => {
  const [result, setResult] = useState<ScenarioAnalysisResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastRefreshedAt, setLastRefreshedAt] = useState<string | null>(null);

  const fetchAnalysisResult = useCallback(async () => {
    if (!scenarioId) {
      setError("Scenario ID is required to load analysis data.");
      setResult(null);
      return;
    }

    try {
      setLoading(true);
      setError(null);
      const response = await scenarioApi.getAnalysisResult(scenarioId, workflow);
      setResult(response);
      setLastRefreshedAt(new Date().toISOString());
    } catch (err) {
      setResult(null);
      setError(formatErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }, [scenarioId, workflow]);

  useEffect(() => {
    fetchAnalysisResult();
  }, [fetchAnalysisResult]);

  const contextEntries = useMemo(() => {
    const context = result?.context;
    if (!context) return [];

    const ordered = [
      {
        label: "Scenario Request",
        value: context.scenario_request_block,
      },
      {
        label: "Base Case",
        value: context.base_case_block,
      },
      {
        label: "Tabular Data",
        value: context.tabular_data_block,
      },
    ];

    return ordered.filter(
      (entry) => entry.value && entry.value.trim().length > 0
    );
  }, [result?.context]);

  if (loading && !result && !error) {
    return (
      <Paper elevation={0} sx={{ p: 3 }}>
        <Box sx={{ display: "flex", justifyContent: "center", p: 2 }}>
          <CircularProgress />
        </Box>
      </Paper>
    );
  }

  if (error) {
    return (
      <Paper elevation={0} sx={{ p: 3 }}>
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
        <Box sx={{ display: "flex", justifyContent: "flex-end" }}>
          <Tooltip title="Retry">
            <span>
              <IconButton onClick={fetchAnalysisResult} disabled={loading}>
                {loading ? <CircularProgress size={18} /> : <RefreshIcon />}
              </IconButton>
            </span>
          </Tooltip>
        </Box>
      </Paper>
    );
  }

  if (!result) {
    return (
      <Paper elevation={0} sx={{ p: 3 }}>
        <Alert severity="info" sx={{ mb: 2 }}>
          No scenario analysis results were found for this scenario.
        </Alert>
        <Box sx={{ display: "flex", justifyContent: "flex-end" }}>
          <Tooltip title="Fetch latest result">
            <span>
              <IconButton onClick={fetchAnalysisResult} disabled={loading}>
                {loading ? <CircularProgress size={18} /> : <RefreshIcon />}
              </IconButton>
            </span>
          </Tooltip>
        </Box>
      </Paper>
    );
  }

  return (
    <Paper elevation={0} sx={{ p: 3 }}>
      <Box
        sx={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "flex-start",
          gap: 2,
        }}
      >
        <Box>
          <Typography variant="h6" gutterBottom>
            Scenario Analysis Result
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Scenario ID: {result.scenario_id}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Last updated: {formatDateTime(result.updated_at)}
          </Typography>
          {lastRefreshedAt && (
            <Typography variant="caption" color="text.secondary">
              Retrieved: {formatDateTime(lastRefreshedAt)}
            </Typography>
          )}
        </Box>

        <Stack direction="row" spacing={1} alignItems="center">
          {result.workflow && (
            <Chip label={`Workflow: ${result.workflow}`} size="small" />
          )}
          {result.job_id && <Chip label={`Job: ${result.job_id}`} size="small" />}
          <Tooltip title="Refresh analysis result">
            <span>
              <IconButton onClick={fetchAnalysisResult} disabled={loading}>
                {loading ? <CircularProgress size={18} /> : <RefreshIcon />}
              </IconButton>
            </span>
          </Tooltip>
        </Stack>
      </Box>

      <Divider sx={{ my: 3 }} />

      <Box>
        <Typography variant="subtitle1" gutterBottom>
          Context Blocks
        </Typography>
        {contextEntries.length === 0 ? (
          <Typography variant="body2" color="text.secondary">
            No context blocks were provided in this analysis result.
          </Typography>
        ) : (
          contextEntries.map((entry) => (
            <Paper
              key={entry.label}
              variant="outlined"
              sx={{
                p: 2,
                mb: 2,
                backgroundColor: (theme) =>
                  theme.palette.mode === "dark"
                    ? "rgba(255,255,255,0.02)"
                    : "grey.50",
              }}
            >
              <Typography
                variant="subtitle2"
                color="text.secondary"
                sx={{ mb: 1 }}
              >
                {entry.label}
              </Typography>
              <Box
                component="pre"
                sx={{
                  m: 0,
                  whiteSpace: "pre-wrap",
                  fontFamily: "monospace",
                  fontSize: "0.85rem",
                }}
              >
                {entry.value || "N/A"}
              </Box>
            </Paper>
          ))
        )}
      </Box>

      <Divider sx={{ my: 3 }} />

      <Box>
        <Typography variant="subtitle1" gutterBottom>
          Structured Result
        </Typography>
        <Paper
          variant="outlined"
          sx={{
            p: 2,
            backgroundColor: (theme) =>
              theme.palette.mode === "dark"
                ? "rgba(255,255,255,0.02)"
                : "grey.50",
          }}
        >
          <ReactJson
            src={result.result || {}}
            name={null}
            collapsed={2}
            enableClipboard={false}
            displayDataTypes={false}
            displayObjectSize={false}
          />
        </Paper>
      </Box>
    </Paper>
  );
};

export default ScenarioAnalysisData;

