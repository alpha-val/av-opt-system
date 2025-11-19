import React, { useEffect, useState } from "react";
import {
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Box,
  Typography,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Alert,
  Divider,
} from "@mui/material";
import { ExpandMore as ExpandMoreIcon } from "@mui/icons-material";
import SummarizeOutlinedIcon from "@mui/icons-material/SummarizeOutlined";
import ChecklistOutlinedIcon from "@mui/icons-material/ChecklistOutlined";
import GridViewOutlinedIcon from "@mui/icons-material/GridViewOutlined";
import { scenarioApi } from "../../services/api";
import { RecommendationsResponse, Recommendation } from "../../types/api";

interface BaseCaseRecommendationViewProps {
  scenarioId: string;
}

/**
 * Base Case Recommendation View Component
 *
 * Displays base case recommendations for a scenario, including
 * recommendations and relevant entities from the latest recommendation document.
 */
const BaseCaseRecommendationView: React.FC<BaseCaseRecommendationViewProps> = ({
  scenarioId,
}) => {
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [recommendationsData, setRecommendationsData] =
    useState<RecommendationsResponse | null>(null);

  useEffect(() => {
    const fetchRecommendations = async () => {
      if (!scenarioId) {
        setError("Scenario ID is required");
        setLoading(false);
        return;
      }

      try {
        setLoading(true);
        setError(null);
        const data = await scenarioApi.getRecommendations(scenarioId);
        setRecommendationsData(data);
      } catch (err) {
        const errorMessage =
          err instanceof Error
            ? err.message
            : "Failed to fetch recommendations";
        setError(errorMessage);
        setRecommendationsData(null);
      } finally {
        setLoading(false);
      }
    };

    fetchRecommendations();
  }, [scenarioId]);
  console.log("recommendationsData", recommendationsData);
  /**
   * Get priority color for chip
   */
  const getPriorityColor = (
    priority: "high" | "medium" | "low"
  ): "error" | "warning" | "success" | "default" => {
    switch (priority) {
      case "high":
        return "error";
      case "medium":
        return "warning";
      case "low":
        return "success";
      default:
        return "default";
    }
  };

  if (loading) {
    return (
      <Box sx={{ display: "flex", justifyContent: "center", p: 2 }}>
        <CircularProgress size={24} />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ m: 1 }}>
        {error}
      </Alert>
    );
  }

  // if (!recommendationsData) {
  //   return (
  //     <Alert severity="info" sx={{ m: 1 }}>
  //       No recommendations available for this scenario. Run analysis to generate
  //       recommendations.
  //     </Alert>
  //   );
  // }

  // Get the latest recommendation document
  let latestDoc: any = null;
  if (
    Array.isArray(recommendationsData.recommendations_documents) &&
    recommendationsData.recommendations_documents.length > 0
  ) {
    // Pick the last element from the array
    latestDoc =
      recommendationsData.recommendations_documents[
        recommendationsData.recommendations_documents.length - 1
      ];
  } else if (
    recommendationsData.recommendations_documents &&
    !Array.isArray(recommendationsData.recommendations_documents)
  ) {
    // Handle case where it's a single object
    latestDoc = recommendationsData.recommendations_documents;
  }

  // Fallback to top-level recommendations if no documents found
  const recommendations =
    latestDoc?.recommendations || recommendationsData.recommendations || [];
  const relevantEntities =
    latestDoc?.relevant_entities || recommendationsData.relevant_entities || [];
  const globalObjectiveType =
    latestDoc?.global_objective_type ||
    recommendationsData.global_objective_type;
  const globalObjectiveTarget =
    latestDoc?.global_objective_target ||
    recommendationsData.global_objective_target;
  // console.log("recommendations", recommendations);
  // if (recommendations.length === 0 && relevantEntities.length === 0) {
  //   return (
  //     <Alert severity="info" sx={{ m: 1 }}>
  //       No recommendations found for this scenario. Run analysis to generate
  //       recommendations.
  //     </Alert>
  //   );
  // }

  return (
    <Box>
      {globalObjectiveType && (
        <Box sx={{ mb: 2 }}>
          <Typography variant="body2" color="text.secondary">
            <strong>Objective:</strong> {globalObjectiveType}
            {globalObjectiveTarget && <> - {globalObjectiveTarget}</>}
          </Typography>
        </Box>
      )}

      {recommendations.length > 0 && (
        <Accordion
          defaultExpanded={false}
          sx={{ backgroundColor: "#f9f9f9", mb: 1 }}
        >
          <AccordionSummary
            expandIcon={<ExpandMoreIcon />}
            aria-controls="recommendations-content"
            id="recommendations-header"
          >
            <SummarizeOutlinedIcon sx={{ mr: 1 }} />
            <Typography variant="subtitle1" fontWeight={600}>
              Recommendations ({recommendations.length})
            </Typography>
          </AccordionSummary>
          <AccordionDetails>
            <Box
              sx={{ display: "flex", flexDirection: "column", gap: 1.5, mb: 3 }}
            >
              {recommendations.map(
                (recommendation: Recommendation, index: number) => (
                  <Card
                    key={recommendation.recommendation_id || index}
                    variant="outlined"
                  >
                    <CardContent sx={{ p: 2, "&:last-child": { pb: 2 } }}>
                      <Box
                        sx={{
                          display: "flex",
                          justifyContent: "space-between",
                          alignItems: "flex-start",
                          mb: 1,
                        }}
                      >
                        <Typography
                          variant="subtitle1"
                          component="h3"
                          sx={{ fontWeight: 600, flex: 1, mr: 1 }}
                        >
                          {recommendation.title}
                        </Typography>
                        <Box
                          sx={{
                            display: "flex",
                            gap: 0.5,
                            alignItems: "center",
                            flexShrink: 0,
                          }}
                        >
                          {recommendation.type && (
                            <Chip
                              label={recommendation.type}
                              size="small"
                              variant="outlined"
                            />
                          )}
                          {recommendation.priority && (
                            <Chip
                              label={recommendation.priority.toUpperCase()}
                              size="small"
                              color={getPriorityColor(recommendation.priority)}
                            />
                          )}
                        </Box>
                      </Box>

                      <Typography
                        variant="body2"
                        sx={{ mb: 1.5, lineHeight: 1.6 }}
                      >
                        {recommendation.description}
                      </Typography>

                      {(recommendation.rationale ||
                        recommendation.estimated_impact ||
                        recommendation.implementation_complexity) && (
                        <Box
                          sx={{
                            display: "flex",
                            flexDirection: "column",
                            gap: 1,
                          }}
                        >
                          {recommendation.rationale && (
                            <Box>
                              <Typography
                                variant="caption"
                                color="text.secondary"
                                sx={{ fontWeight: 500 }}
                              >
                                Rationale:{" "}
                              </Typography>
                              <Typography
                                variant="body2"
                                color="text.secondary"
                                component="span"
                              >
                                {recommendation.rationale}
                              </Typography>
                            </Box>
                          )}
                          <Box
                            sx={{ display: "flex", gap: 2, flexWrap: "wrap" }}
                          >
                            {recommendation.estimated_impact && (
                              <Box>
                                <Typography
                                  variant="caption"
                                  color="text.secondary"
                                  sx={{ fontWeight: 500 }}
                                >
                                  Impact:{" "}
                                </Typography>
                                <Typography variant="body2" component="span">
                                  {recommendation.estimated_impact}
                                </Typography>
                              </Box>
                            )}
                            {recommendation.implementation_complexity && (
                              <Box>
                                <Typography
                                  variant="caption"
                                  color="text.secondary"
                                  sx={{ fontWeight: 500 }}
                                >
                                  Complexity:{" "}
                                </Typography>
                                <Typography variant="body2" component="span">
                                  {recommendation.implementation_complexity}
                                </Typography>
                              </Box>
                            )}
                          </Box>
                        </Box>
                      )}
                    </CardContent>
                  </Card>
                )
              )}
            </Box>
          </AccordionDetails>
        </Accordion>
      )}

      {relevantEntities.length > 0 && (
        <Accordion
          defaultExpanded={false}
          sx={{ backgroundColor: "#f9f9f9", mb: 1 }}
        >
          <AccordionSummary
            expandIcon={<ExpandMoreIcon />}
            aria-controls="recommendations-content"
            id="recommendations-header"
          >
            <GridViewOutlinedIcon sx={{ mr: 1 }} />
            <Typography variant="subtitle1" fontWeight={600}>
              Relevant Entities ({relevantEntities.length})
            </Typography>
          </AccordionSummary>
          <AccordionDetails>
            <Box sx={{ display: "flex", flexDirection: "column", gap: 1 }}>
              {relevantEntities.map((entity: any, index: number) => {
                // Handle full node structure (id, type, properties)
                const isFullNode =
                  entity.id && entity.type && entity.properties;
                const entityName = isFullNode
                  ? entity.properties?.name || "Unknown"
                  : entity.entity_name || "Unknown";
                const entityType = isFullNode
                  ? entity.type
                  : entity.entity_type || "Unknown";
                const priority = isFullNode
                  ? entity.properties?.extraction_priority || "medium"
                  : entity.priority || "medium";
                const msioClassification = isFullNode
                  ? {
                      discipline: entity.properties?.discipline || "",
                      category: entity.properties?.category || "",
                      subcategory: entity.properties?.subcategory || "",
                      entity: entity.properties?.entity || "",
                    }
                  : entity.msio_classification || {};
                const rationale = isFullNode
                  ? entity.properties?.extraction_rationale
                  : entity.rationale;
                const expectedAttributes = isFullNode
                  ? entity.properties?.expected_attributes
                  : entity.expected_attributes;
                const entityId = isFullNode ? entity.id : `entity_${index}`;
                const isPlaceholder = isFullNode
                  ? entity.properties?.is_placeholder
                  : false;

                return (
                  <Card key={entityId} variant="outlined">
                    <CardContent sx={{ p: 1.5, "&:last-child": { pb: 1.5 } }}>
                      <Box
                        sx={{
                          display: "flex",
                          justifyContent: "space-between",
                          alignItems: "flex-start",
                          mb: 0.5,
                        }}
                      >
                        <Box
                          sx={{ display: "flex", alignItems: "center", gap: 1 }}
                        >
                          <Typography
                            variant="body1"
                            fontWeight={600}
                            component="span"
                          >
                            {entityName}
                          </Typography>
                          {isPlaceholder && (
                            <Chip
                              label="Placeholder"
                              size="small"
                              variant="outlined"
                            />
                          )}
                        </Box>
                        {priority && (
                          <Chip
                            label={priority.toUpperCase()}
                            size="small"
                            color={getPriorityColor(
                              priority as "high" | "medium" | "low"
                            )}
                          />
                        )}
                      </Box>
                      <Typography
                        variant="caption"
                        color="text.secondary"
                        sx={{ display: "block", mb: 0.5 }}
                      >
                        Type: {entityType}
                      </Typography>
                      {(msioClassification.discipline ||
                        msioClassification.category ||
                        msioClassification.subcategory ||
                        msioClassification.entity) && (
                        <Box sx={{ mt: 0.5 }}>
                          <Typography
                            variant="caption"
                            color="text.secondary"
                            sx={{ fontWeight: 500 }}
                          >
                            MSIO:{" "}
                          </Typography>
                          <Typography variant="caption" component="span">
                            {msioClassification.discipline || "N/A"} /{" "}
                            {msioClassification.category || "N/A"} /{" "}
                            {msioClassification.subcategory || "N/A"} /{" "}
                            {msioClassification.entity || "N/A"}
                          </Typography>
                        </Box>
                      )}
                      {rationale && (
                        <Box sx={{ mt: 0.5 }}>
                          <Typography
                            variant="caption"
                            color="text.secondary"
                            sx={{ fontWeight: 500 }}
                          >
                            Rationale:{" "}
                          </Typography>
                          <Typography
                            variant="caption"
                            color="text.secondary"
                            component="span"
                          >
                            {rationale}
                          </Typography>
                        </Box>
                      )}
                      {expectedAttributes &&
                        Array.isArray(expectedAttributes) &&
                        expectedAttributes.length > 0 && (
                          <Box
                            sx={{
                              mt: 0.5,
                              pt: 0.5,
                              borderTop: "1px solid",
                              borderColor: "divider",
                            }}
                          >
                            <Typography
                              variant="caption"
                              color="text.secondary"
                              sx={{ fontWeight: 500, mr: 0.5 }}
                            >
                              Expected Attributes:
                            </Typography>
                            <Box
                              sx={{
                                display: "inline-flex",
                                gap: 0.5,
                                flexWrap: "wrap",
                                mt: 0.25,
                              }}
                            >
                              {expectedAttributes.map(
                                (attr: string, idx: number) => (
                                  <Chip
                                    key={idx}
                                    label={attr}
                                    size="small"
                                    variant="outlined"
                                  />
                                )
                              )}
                            </Box>
                          </Box>
                        )}
                    </CardContent>
                  </Card>
                );
              })}
            </Box>
          </AccordionDetails>
        </Accordion>
      )}
    </Box>
  );
};

export default BaseCaseRecommendationView;
