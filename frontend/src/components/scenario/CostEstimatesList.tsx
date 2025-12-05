import React, { useEffect, useMemo } from "react";
import { useDispatch, useSelector } from "react-redux";
import {
  Box,
  Typography,
  Card,
  CardContent,
  CardActions,
  Grid,
  CircularProgress,
  Alert,
  IconButton,
  Button,
} from "@mui/material";
import {
  Delete as DeleteIcon,
  Description as DescriptionIcon,
  CalendarToday as CalendarIcon,
  AttachMoney as MoneyIcon,
} from "@mui/icons-material";
import {
  fetchCostEstimates,
  deleteCostEstimate,
  selectCostEstimatesByScenario,
  selectCostEstimatesLoading,
  selectCostEstimatesError,
  selectCostEstimateDeleting,
  clearError,
} from "../../redux/costEstimatesSlice";
import { useDialogs } from "../../hooks/useDialogs";

interface CostEstimatesListProps {
  scenarioId: string;
  onCostEstimateSelect?: (costEstimateId: string) => void;
}

/**
 * Cost Estimates List component.
 *
 * Displays a list of cost estimates for a given scenario.
 * Shows an empty state when no cost estimates exist.
 */
const CostEstimatesList: React.FC<CostEstimatesListProps> = ({
  scenarioId,
  onCostEstimateSelect,
}) => {
  const dispatch = useDispatch();
  const dialogs = useDialogs();

  // Memoize the selector to avoid creating a new one on every render
  const memoizedSelector = useMemo(
    () => selectCostEstimatesByScenario(scenarioId),
    [scenarioId]
  );

  const costEstimates = useSelector(memoizedSelector);
  const loading = useSelector(selectCostEstimatesLoading);
  const deleting = useSelector(selectCostEstimateDeleting);
  const error = useSelector(selectCostEstimatesError);

  /**
   * Fetch cost estimates when scenarioId changes
   */
  useEffect(() => {
    if (scenarioId) {
      dispatch(fetchCostEstimates(scenarioId) as any);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [scenarioId, dispatch]);

  /**
   * Format date for display
   */
  const formatDate = (dateString: string): string => {
    try {
      return new Date(dateString).toLocaleDateString("en-US", {
        year: "numeric",
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      });
    } catch {
      return dateString;
    }
  };

  /**
   * Handle cost estimate click
   */
  const handleCostEstimateClick = (costEstimateId: string) => {
    if (onCostEstimateSelect) {
      onCostEstimateSelect(costEstimateId);
    }
  };

  /**
   * Handle delete cost estimate with confirmation
   */
  const handleDelete = async (costEstimateId: string, costEstimateName: string) => {
    const confirmed = await dialogs.confirm(
      `Are you sure you want to delete "${costEstimateName}"? This action cannot be undone.`,
      {
        title: "Delete Cost Estimate",
        severity: "error",
        okText: "Delete",
        cancelText: "Cancel",
      }
    );

    if (!confirmed) {
      return;
    }

    dispatch(clearError());
    dispatch(deleteCostEstimate(costEstimateId) as any);
  };

  /**
   * Get cost comparison report count
   */
  const getReportCount = (costEstimate: any): number => {
    return costEstimate.metadata?.cost_comparison_report?.length || 0;
  };

  return (
    <Box>
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
      {loading.fetch ? (
        <Box
          sx={{
            display: "flex",
            justifyContent: "center",
            alignItems: "center",
            minHeight: "200px",
          }}
        >
          <CircularProgress />
        </Box>
      ) : costEstimates.length === 0 ? (
        /* Empty State */
        <Box
          sx={{
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            minHeight: "300px",
            textAlign: "center",
            p: 4,
          }}
        >
          <MoneyIcon
            sx={{
              fontSize: 64,
              color: "text.secondary",
              mb: 2,
              opacity: 0.5,
            }}
          />
          <Typography variant="h6" gutterBottom color="text.secondary">
            No cost estimates yet
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Create a cost estimate to analyze costs for this scenario.
          </Typography>
        </Box>
      ) : (
        /* Cost Estimates Grid */
        <>
          <Box
            sx={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              mb: 3,
            }}
          >
            <Typography variant="h6">
              Cost Estimates ({costEstimates.length})
            </Typography>
          </Box>

          <Grid container spacing={3}>
            {costEstimates.map((costEstimate) => (
              <Grid item xs={12} sm={6} md={4} key={costEstimate.id}>
                <Card
                  variant="outlined"
                  sx={{
                    height: "100%",
                    display: "flex",
                    flexDirection: "column",
                    cursor: "pointer",
                    transition: "transform 0.2s, box-shadow 0.2s",
                    border: "1px solid",
                    borderColor: "divider",
                    bgcolor: (theme) =>
                      theme.palette.mode === "dark"
                        ? theme.palette.background.card || "#2d2d30"
                        : "#ffffff",
                    "&:hover": {
                      transform: "translateY(-2px)",
                      boxShadow: 2,
                      bgcolor: (theme) =>
                        theme.palette.mode === "dark"
                          ? theme.palette.background.cardHover || "#3c3c3c"
                          : "#f5f5f5",
                    },
                  }}
                  onClick={() => handleCostEstimateClick(costEstimate.id)}
                >
                  <CardContent sx={{ flexGrow: 1, p: 2.5 }}>
                    {/* Header with Title */}
                    <Box
                      sx={{
                        display: "flex",
                        alignItems: "flex-start",
                        mb: 2,
                      }}
                    >
                      <Box sx={{ flex: 1, minWidth: 0 }}>
                        <Typography
                          variant="h6"
                          component="h3"
                          sx={{
                            fontWeight: 600,
                            lineHeight: 1.3,
                            mb: 0.5,
                          }}
                        >
                          {costEstimate.name}
                        </Typography>
                      </Box>
                    </Box>

                    {/* Description */}
                    {costEstimate.description && (
                      <Box
                        sx={{
                          display: "flex",
                          alignItems: "flex-start",
                          gap: 1,
                          mb: 2,
                        }}
                      >
                        <DescriptionIcon
                          fontSize="small"
                          sx={{
                            color: "text.secondary",
                            mt: 0.5,
                            flexShrink: 0,
                          }}
                        />
                        <Typography
                          variant="body2"
                          color="text.secondary"
                          sx={{
                            lineHeight: 1.5,
                            display: "-webkit-box",
                            WebkitLineClamp: 2,
                            WebkitBoxOrient: "vertical",
                            overflow: "hidden",
                          }}
                        >
                          {costEstimate.description}
                        </Typography>
                      </Box>
                    )}

                    {/* Cost Comparison Report Info */}
                    {costEstimate.metadata?.cost_comparison_report && (
                      <Box
                        sx={{
                          display: "flex",
                          alignItems: "center",
                          gap: 1,
                          mb: 2,
                          p: 1.5,
                          borderRadius: 1,
                          bgcolor: (theme) =>
                            theme.palette.mode === "dark"
                              ? "rgba(0, 150, 136, 0.08)"
                              : "rgba(0, 150, 136, 0.04)",
                        }}
                      >
                        <MoneyIcon
                          fontSize="small"
                          sx={{ color: "success.main", flexShrink: 0 }}
                        />
                        <Box sx={{ flex: 1, minWidth: 0 }}>
                          <Typography
                            variant="caption"
                            color="text.secondary"
                            sx={{ display: "block", mb: 0.5 }}
                          >
                            Entities Analyzed
                          </Typography>
                          <Typography
                            variant="body2"
                            sx={{ fontWeight: 600 }}
                          >
                            {getReportCount(costEstimate)} entities
                          </Typography>
                        </Box>
                      </Box>
                    )}

                    {/* Created Date */}
                    <Box
                      sx={{
                        display: "flex",
                        alignItems: "center",
                        gap: 1,
                        mt: "auto",
                        pt: 2,
                        borderTop: 1,
                        borderColor: "divider",
                      }}
                    >
                      <CalendarIcon
                        fontSize="small"
                        sx={{ color: "text.secondary", flexShrink: 0 }}
                      />
                      <Typography variant="caption" color="text.secondary">
                        Created: {formatDate(costEstimate.created_at)}
                      </Typography>
                    </Box>
                  </CardContent>

                  {/* Card Actions */}
                  <CardActions
                    sx={{
                      p: 1.5,
                      pt: 0,
                      justifyContent: "flex-end",
                    }}
                    onClick={(e) => e.stopPropagation()}
                  >
                    <IconButton
                      size="small"
                      color="error"
                      onClick={() =>
                        handleDelete(costEstimate.id, costEstimate.name)
                      }
                      disabled={deleting}
                      aria-label="Delete cost estimate"
                    >
                      <DeleteIcon fontSize="small" />
                    </IconButton>
                  </CardActions>
                </Card>
              </Grid>
            ))}
          </Grid>
        </>
      )}
    </Box>
  );
};

export default CostEstimatesList;

