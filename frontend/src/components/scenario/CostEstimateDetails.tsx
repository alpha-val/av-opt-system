import React, { useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import {
  Box,
  Typography,
  Paper,
  Button,
  CircularProgress,
  Alert,
  Divider,
  Card,
  CardContent,
  Grid,
  Breadcrumbs,
  Link,
} from "@mui/material";
import {
  ArrowBack as ArrowBackIcon,
  Description as DescriptionIcon,
  CalendarToday as CalendarIcon,
  AttachMoney as MoneyIcon,
} from "@mui/icons-material";
import {
  fetchCostEstimateById,
  selectCurrentCostEstimate,
  selectCostEstimatesLoading,
  selectCostEstimatesError,
  clearError,
} from "../../redux/costEstimatesSlice";
import CostComparisonReport from "./CostComparisonReport";
import { CostComparisonRow, CostInfo } from "../../types/api";

interface CostEstimateDetailsProps {
  costEstimateId: string;
  scenarioId?: string;
  onBack?: () => void;
}

/**
 * Cost Estimate Details component.
 *
 * Displays detailed information about a cost estimate including:
 * - Basic information (name, description, dates)
 * - Cost comparison report
 * - Metadata and calculation details
 */
const CostEstimateDetails: React.FC<CostEstimateDetailsProps> = ({
  costEstimateId,
  scenarioId,
  onBack,
}) => {
  const dispatch = useDispatch();
  const costEstimate = useSelector(selectCurrentCostEstimate);
  const loading = useSelector(selectCostEstimatesLoading);
  const error = useSelector(selectCostEstimatesError);

  /**
   * Fetch cost estimate details when costEstimateId changes
   */
  useEffect(() => {
    if (costEstimateId) {
      dispatch(fetchCostEstimateById(costEstimateId) as any);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [costEstimateId, dispatch]);

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
   * Transform new cost comparison report structure to old format
   * New format: { bc: entity, base_cost: number, tabular_cost: [{td: entity, cost: number}] }
   * Old format: { entity_id, entity_name, entity_type, base_cost_info: CostInfo, tabular_matches: TabularMatch[] }
   */
  const transformCostComparisonReport = (
    report: any[]
  ): CostComparisonRow[] => {
    if (!report || !Array.isArray(report)) {
      return [];
    }

    return report.map((item) => {
      const baseEntity = item.bc || {};
      const baseCost = item.base_cost ?? null;
      const tabularCosts = item.tabular_cost || [];

      // Extract base entity information
      const entityId = baseEntity.id || "";
      const entityName = baseEntity.properties?.name || "Unknown Entity";
      const entityType = baseEntity.type || "Unknown";

      // Get currency from base entity cost_information, default to USD
      const baseCostCurrency =
        baseEntity.properties?.cost_information?.cost_currency ||
        baseEntity.properties?.cost_currency ||
        "USD";

      // Create base_cost_info
      const baseCostInfo: CostInfo = {
        value: baseCost,
        currency: baseCostCurrency,
        unit: null,
        basis:
          baseEntity.properties?.cost_information?.cost_basis_year ||
          baseEntity.properties?.cost_basis_year ||
          null,
      };

      // Transform tabular_cost to tabular_matches
      const tabularMatches = tabularCosts.map((tc: any) => {
        const tabularEntity = tc.td || {};
        const tabularCost = tc.cost ?? null;
        const tabularId = tabularEntity.id || "";
        const tabularName = tabularEntity.properties?.name || "Unknown Entity";
        const tabularType = tabularEntity.type || "Unknown";
        const relevanceScore = tabularEntity.relevance_score || 0;

        // Get currency from tabular entity cost_information, default to USD
        const tabularCostCurrency =
          tabularEntity.properties?.cost_information?.cost_currency ||
          tabularEntity.properties?.cost_currency ||
          "USD";

        const tabularCostInfo: CostInfo = {
          value: tabularCost,
          currency: tabularCostCurrency,
          unit: null,
          basis:
            tabularEntity.properties?.cost_information?.cost_basis_year ||
            tabularEntity.properties?.cost_basis_year ||
            null,
        };

        return {
          entity_id: tabularId,
          entity_name: tabularName,
          entity_type: tabularType,
          cost_info: tabularCostInfo,
          score: relevanceScore,
        };
      });

      // Sort tabular matches by score (highest first)
      tabularMatches.sort((a, b) => b.score - a.score);

      return {
        entity_id: entityId,
        entity_name: entityName,
        entity_type: entityType,
        base_cost_info: baseCostInfo,
        tabular_matches: tabularMatches,
      };
    });
  };

  /**
   * Get cost comparison report data and transform it
   */
  const rawReport = costEstimate?.metadata?.cost_comparison_report || [];
  const costComparisonReport = transformCostComparisonReport(rawReport);

  /**
   * Get cost details
   */
  const costDetails = costEstimate?.metadata?.cost_details || {};

  if (loading.fetchById) {
    return (
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
    );
  }

  if (error) {
    return (
      <Alert
        severity="error"
        action={
          <Button
            color="inherit"
            size="small"
            onClick={() => {
              dispatch(clearError());
              if (costEstimateId) {
                dispatch(fetchCostEstimateById(costEstimateId) as any);
              }
            }}
          >
            Retry
          </Button>
        }
      >
        {error}
      </Alert>
    );
  }

  if (!costEstimate) {
    return <Alert severity="warning">Cost estimate not found</Alert>;
  }

  return (
    <Box
      sx={{ display: "flex", flexDirection: "column", height: "100%", p: 0 }}
    >
      {/* Header with Back Button */}
      <Box
        sx={{
          mb: 2,
          display: "flex",
          alignItems: "center",
          gap: 2,
        }}
      >
        {onBack && (
          <Button
            startIcon={<ArrowBackIcon />}
            onClick={onBack}
            variant="outlined"
            size="small"
            sx={{ textTransform: "none" }}
          >
            All Cost Estimates
          </Button>
        )}
      </Box>
      <Typography variant="h5" component="h1" sx={{ fontWeight: 600, mb: 2 }}>
        {costEstimate.name}
      </Typography>

      {/* Basic Information Card */}
      <Card sx={{ mb: 2 }}>
        <CardContent>
          {/* <Box sx={{ display: "flex", alignItems: "center", mb: 2 }}>
            <DescriptionIcon
              sx={{
                mr: 1.5,
                fontSize: 24,
                color: "primary.main",
              }}
            />
            <Typography variant="h6" sx={{ fontWeight: 600, flex: 1 }}>
              Cost Estimate Information
            </Typography>
          </Box> */}

          {costEstimate.description && (
            <Typography variant="body1" sx={{ mb: 3 }}>
              {costEstimate.description}
            </Typography>
          )}

          {/* Cost Summary */}
          {costComparisonReport.length > 0 && (
            <>
              {/* <Box sx={{ display: "flex", alignItems: "center", mb: 2 }}>
                <MoneyIcon
                  sx={{
                    mr: 1.5,
                    fontSize: 24,
                    color: "success.main",
                  }}
                />
                <Typography variant="h6" sx={{ fontWeight: 600 }}>
                  Cost Summary
                </Typography>
              </Box> */}

              <Grid container spacing={1}>
                <Grid item xs={12} md={4}>
                  <Typography variant="subtitle2" color="text.secondary">
                    Entities Analyzed
                  </Typography>
                  <Typography variant="h5" sx={{ fontWeight: 700 }}>
                    {costComparisonReport.length}
                  </Typography>
                </Grid>

                {costDetails.base_entities && (
                  <Grid item xs={12} md={4}>
                    <Typography variant="subtitle2" color="text.secondary">
                      Base Case Entities
                    </Typography>
                    <Typography variant="h5" sx={{ fontWeight: 700 }}>
                      {costDetails.base_entities.length || 0}
                    </Typography>
                  </Grid>
                )}
                {costDetails.tabular_entities && (
                  <Grid item xs={12} md={4}>
                    <Typography variant="subtitle2" color="text.secondary">
                      Tabular Entities
                    </Typography>
                    <Typography variant="h5" sx={{ fontWeight: 700 }}>
                      {costDetails.tabular_entities.length || 0}
                    </Typography>
                  </Grid>
                )}
              </Grid>
            </>
          )}
          <Divider sx={{ my: 2 }} />
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <Box sx={{ display: "flex", alignItems: "center", mb: 1 }}>
                <CalendarIcon
                  sx={{
                    mr: 1,
                    fontSize: 18,
                    color: "text.secondary",
                  }}
                />
                <Typography
                  variant="subtitle2"
                  color="text.secondary"
                  sx={{ fontWeight: 500 }}
                >
                  Created
                </Typography>
              </Box>
              <Typography variant="body1">
                {formatDate(costEstimate.created_at)}
              </Typography>
            </Grid>
            <Grid item xs={12} md={6}>
              <Box sx={{ display: "flex", alignItems: "center", mb: 1 }}>
                <CalendarIcon
                  sx={{
                    mr: 1,
                    fontSize: 18,
                    color: "text.secondary",
                  }}
                />
                <Typography
                  variant="subtitle2"
                  color="text.secondary"
                  sx={{ fontWeight: 500 }}
                >
                  Last Updated
                </Typography>
              </Box>
              <Typography variant="body1">
                {formatDate(costEstimate.updated_at)}
              </Typography>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Cost Comparison Report */}
      {costComparisonReport.length > 0 ? (
        <Paper sx={{ flex: 1, p: 3 }}>
          <Typography variant="h6" gutterBottom sx={{ mb: 3 }}>
            Cost Comparison Report
          </Typography>
          <CostComparisonReport reportData={costComparisonReport} />
        </Paper>
      ) : (
        <Alert severity="info">
          <Typography variant="body2">
            No cost comparison data available. This cost estimate may not have
            been calculated yet.
          </Typography>
        </Alert>
      )}
    </Box>
  );
};

export default CostEstimateDetails;
