import React, { useEffect, useState, useRef } from "react";
import {
  Box,
  Card,
  CardContent,
  LinearProgress,
  Typography,
  Chip,
  IconButton,
  Alert,
  Collapse,
} from "@mui/material";
import {
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Close as CloseIcon,
} from "@mui/icons-material";
import { useProgress } from "../../hooks/useProgress";

interface ProgressWidgetProps {
  jobId: string | null;
  title: string;
  onDismiss?: () => void;
  onComplete?: () => void;
}

const ProgressWidget: React.FC<ProgressWidgetProps> = React.memo(({
  jobId,
  title,
  onDismiss,
  onComplete,
}) => {
  // console.log("ProgressWidget rendered with jobId:", jobId, "title:", title);
  const { connected, progress, stage, status, error, meta, reconnectAttempts } =
    useProgress(jobId);
  const [autoHideTimer, setAutoHideTimer] = useState<NodeJS.Timeout | null>(null);
  const [isVisible, setIsVisible] = useState(true);
  
  // console.log("ProgressWidget state:", { connected, progress, stage, status, isVisible, jobId });

  useEffect(() => {
    if (status === "completed" && progress === 100 && stage === "complete") {
      if (onComplete) {
        onComplete();
      }
      
      const timer = setTimeout(() => {
        // console.log("Auto-hiding progress widget");
        setIsVisible(false);
        if (onDismiss) {
          onDismiss();
        }
      }, 3000);
      setAutoHideTimer(timer);
      return () => {
        if (timer) clearTimeout(timer);
      };
    } else {
      if (autoHideTimer) {
        clearTimeout(autoHideTimer);
        setAutoHideTimer(null);
      }
      setIsVisible(true);
    }
  }, [status, progress, stage, onDismiss, onComplete, autoHideTimer]);

  useEffect(() => {
    return () => {
      if (autoHideTimer) {
        clearTimeout(autoHideTimer);
      }
    };
  }, [autoHideTimer]);

  if (!jobId || !isVisible) {
    return null;
  }

  const getStatusColor = (): "default" | "primary" | "success" | "error" => {
    if (status === "completed") return "success";
    if (status === "failed") return "error";
    if (status === "in_progress" || status === "started") return "primary";
    return "default";
  };

  const getStatusIcon = () => {
    if (status === "completed") return <CheckCircleIcon sx={{ fontSize: 20 }} />;
    if (status === "failed") return <ErrorIcon sx={{ fontSize: 20 }} />;
    return null;
  };

  const getStatusText = (): string => {
    if (status === "completed") return "Completed";
    if (status === "failed") return "Failed";
    if (status === "in_progress") return "Processing";
    if (status === "started") return "Starting";
    return "Unknown";
  };

  const getStageDescription = (): string => {
    // Prioritize message from meta if available
    if (meta?.message) {
      return meta.message;
    }
    if (meta?.current_stage) {
      return meta.current_stage;
    }
    if (stage === "complete") return "Processing complete";
    if (stage === "error") return "Error occurred";
    if (stage === "processing") {
      // File upload specific
      if (meta?.current_file) {
        return `Processing: ${meta.current_file}`;
      }
      // Analysis specific
      if (meta?.document_index && meta?.total_documents) {
        return `Processing document ${meta.document_index} of ${meta.total_documents}`;
      }
      // Generic
      if (meta?.file_index && meta?.total_files) {
        return `Processing file ${meta.file_index} of ${meta.total_files}`;
      }
      return "Processing";
    }
    return "Starting";
  };

  const hasErrors = error || (meta?.errors && meta.errors.length > 0);
  // console.log("ProgressWidget", { jobId, title, isVisible, progress, stage, status, error, meta, reconnectAttempts });
  return (
    <Collapse in={isVisible} timeout={300}>
      <Card
        sx={{
          mb: 0,
          boxShadow: 1,
          border: "none",
          borderRadius: 0,
          bgcolor: (theme) =>
            theme.palette.mode === "dark"
              ? "rgba(25, 118, 210, 0.08)"
              : "rgba(25, 118, 210, 0.04)",
        }}
      >
        <CardContent sx={{ p: 1.5, "&:last-child": { pb: 1.5 } }}>
          <Box sx={{ display: "flex", alignItems: "center", justifyContent: "space-between", mb: 1 }}>
            <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
              <Typography variant="h6" sx={{ fontWeight: 600 }}>
                {title}
              </Typography>
              <Chip
                icon={getStatusIcon()}
                label={getStatusText()}
                color={getStatusColor()}
                size="small"
                sx={{ fontWeight: 500 }}
              />
              {!connected && reconnectAttempts > 0 && (
                <Chip
                  label={`Reconnecting... (${reconnectAttempts})`}
                  size="small"
                  color="warning"
                />
              )}
            </Box>
            {onDismiss && (
              <IconButton size="small" onClick={onDismiss}>
                <CloseIcon />
              </IconButton>
            )}
          </Box>

          <Box sx={{ mb: 0 }}>
            <LinearProgress
              variant="determinate"
              value={progress}
              sx={{
                height: 8,
                borderRadius: 4,
                backgroundColor: (theme) =>
                  theme.palette.mode === "dark" ? "rgba(255, 255, 255, 0.1)" : "rgba(0, 0, 0, 0.1)",
              }}
            />
            <Box sx={{ display: "flex", justifyContent: "space-between", mt: 1 }}>
              <Typography variant="body2" color="text.secondary">
                {getStageDescription()}
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ fontWeight: 500 }}>
                {progress}%
              </Typography>
            </Box>
          </Box>

          {hasErrors && (
            <Box sx={{ mt: 2 }}>
              {error && (
                <Alert severity="error" sx={{ mb: 1 }}>
                  {error}
                </Alert>
              )}
              {meta?.errors && meta.errors.length > 0 && (
                <Alert severity="warning">
                  <Typography variant="body2" sx={{ fontWeight: 600, mb: 1 }}>
                    {meta.errors.length} file(s) had errors:
                  </Typography>
                  {meta.errors.slice(0, 3).map((err, idx) => (
                    <Typography key={idx} variant="caption" component="div">
                      {err.filename || err.document_id || err.doc_id || "Unknown"}: {err.error || err.warning || "Unknown error"}
                    </Typography>
                  ))}
                  {meta.errors.length > 3 && (
                    <Typography variant="caption" component="div" sx={{ mt: 0.5 }}>
                      ...and {meta.errors.length - 3} more
                    </Typography>
                  )}
                </Alert>
              )}
            </Box>
          )}

          {!connected && reconnectAttempts === 0 && (
            <Alert severity="info" sx={{ mt: 1 }}>
              Connecting to progress updates...
            </Alert>
          )}
        </CardContent>
      </Card>
    </Collapse>
  );
});

ProgressWidget.displayName = "ProgressWidget";

export default ProgressWidget;

