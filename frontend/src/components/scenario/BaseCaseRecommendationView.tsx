import React, { useEffect, useState } from "react";
import {
  Box,
  Typography,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Alert,
  Divider,
} from "@mui/material";
import { scenarioApi } from "../../services/api";
import { RecommendationsResponse, Recommendation } from "../../types/api";

interface BaseCaseRecommendationViewProps {
  scenarioId: string;
}

/**
 * Base Case Recommendation View Component
 * 
 * Displays base case recommendations for a scenario, including
 * recommendations and relevant entities (if available from V2 workflow).
 */
const BaseCaseRecommendationView: React.FC<BaseCaseRecommendationViewProps> = ({
  scenarioId,
}) => {
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [recommendationsData, setRecommendationsData] = useState<RecommendationsResponse | null>(null);

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
          err instanceof Error ? err.message : "Failed to fetch recommendations";
        setError(errorMessage);
        setRecommendationsData(null);
      } finally {
        setLoading(false);
      }
    };

    fetchRecommendations();
  }, [scenarioId]);

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

  /**
   * Render a single recommendation card
   */
  const renderRecommendation = (recommendation: Recommendation, index: number) => {
    return (
      <Card key={recommendation.recommendation_id || index} variant="outlined" sx={{ mb: 1.5 }}>
        <CardContent sx={{ p: 2, "&:last-child": { pb: 2 } }}>
          <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", mb: 1 }}>
            <Typography variant="subtitle1" component="h3" sx={{ fontWeight: 600, flex: 1, mr: 1 }}>
              {recommendation.title}
            </Typography>
            <Box sx={{ display: "flex", gap: 0.5, alignItems: "center", flexShrink: 0 }}>
              {recommendation.type && (
                <Chip label={recommendation.type} size="small" variant="outlined" />
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

          <Typography variant="body2" sx={{ mb: 1.5, lineHeight: 1.6 }}>
            {recommendation.description}
          </Typography>

          {(recommendation.rationale || recommendation.estimated_impact || recommendation.implementation_complexity) && (
            <Box sx={{ display: "flex", flexDirection: "column", gap: 1, mb: 1 }}>
              {recommendation.rationale && (
                <Box>
                  <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 500 }}>
                    Rationale:{" "}
                  </Typography>
                  <Typography variant="body2" color="text.secondary" component="span">
                    {recommendation.rationale}
                  </Typography>
                </Box>
              )}
              <Box sx={{ display: "flex", gap: 2, flexWrap: "wrap" }}>
                {recommendation.estimated_impact && (
                  <Box>
                    <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 500 }}>
                      Impact:{" "}
                    </Typography>
                    <Typography variant="body2" component="span">
                      {recommendation.estimated_impact}
                    </Typography>
                  </Box>
                )}
                {recommendation.implementation_complexity && (
                  <Box>
                    <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 500 }}>
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

          {recommendation.affected_entities && recommendation.affected_entities.length > 0 && (
            <Box sx={{ mt: 1, pt: 1, borderTop: "1px solid", borderColor: "divider" }}>
              <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 500, mr: 1 }}>
                Affected Entities:
              </Typography>
              <Box sx={{ display: "inline-flex", gap: 0.5, flexWrap: "wrap", mt: 0.5 }}>
                {recommendation.affected_entities.map((entity, idx) => (
                  <Chip key={idx} label={entity} size="small" variant="outlined" />
                ))}
              </Box>
            </Box>
          )}
        </CardContent>
      </Card>
    );
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

  if (!recommendationsData) {
    return (
      <Alert severity="info" sx={{ m: 1 }}>
        No recommendations available for this scenario. Run analysis to generate recommendations.
      </Alert>
    );
  }

  // Handle case where multiple recommendation documents are returned
  const recommendations = recommendationsData.recommendations_documents
    ? recommendationsData.recommendations_documents.flatMap((doc) => doc.recommendations || [])
    : recommendationsData.recommendations || [];

  if (recommendations.length === 0) {
    return (
      <Alert severity="info" sx={{ m: 1 }}>
        No recommendations found for this scenario. Run analysis to generate recommendations.
      </Alert>
    );
  }

  return (
    <Box>
      {recommendationsData.global_objective_type && (
        <Box sx={{ mb: 1.5 }}>
          <Typography variant="body2" color="text.secondary">
            <strong>Objective:</strong> {recommendationsData.global_objective_type}
            {recommendationsData.global_objective_target && (
              <> - {recommendationsData.global_objective_target}</>
            )}
          </Typography>
        </Box>
      )}

      <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 1 }}>
        Recommendations ({recommendations.length})
      </Typography>

      <Box sx={{ display: "flex", flexDirection: "column", gap: 1 }}>
        {recommendations.map((recommendation, index) =>
          renderRecommendation(recommendation, index)
        )}
      </Box>

      {recommendationsData.relevant_entities &&
        recommendationsData.relevant_entities.length > 0 && (
          <>
            <Divider sx={{ my: 2 }} />
            <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 1 }}>
              Relevant Entities ({recommendationsData.relevant_entities.length})
            </Typography>
            <Box sx={{ display: "flex", flexDirection: "column", gap: 1 }}>
              {recommendationsData.relevant_entities.map((entity: any, index: number) => {
                // Handle both old structure (RelevantEntity) and new full node structure
                const isFullNode = entity.id && entity.type && entity.properties;
                const entityName = isFullNode 
                  ? entity.properties?.name || entity.properties?.entity_name || "Unknown"
                  : entity.entity_name || "Unknown";
                const entityType = isFullNode 
                  ? entity.type 
                  : entity.entity_type || "Unknown";
                const priority = isFullNode
                  ? entity.properties?.extraction_priority || entity.properties?.priority || "medium"
                  : entity.priority || "medium";
                const msioClassification = isFullNode
                  ? {
                      discipline: entity.properties?.discipline || "",
                      category: entity.properties?.category || "",
                      subcategory: entity.properties?.subcategory || "",
                      entity: entity.properties?.entity || "",
                    }
                  : entity.msio_classification;
                const rationale = isFullNode
                  ? entity.properties?.extraction_rationale || entity.properties?.rationale
                  : entity.rationale;
                const expectedAttributes = isFullNode
                  ? entity.properties?.expected_attributes
                  : entity.expected_attributes;
                const entityId = isFullNode ? entity.id : `entity_${index}`;

                return (
                  <Card key={entityId} variant="outlined" sx={{ mb: 0 }}>
                    <CardContent sx={{ p: 1.5, "&:last-child": { pb: 1.5 } }}>
                      <Box
                        sx={{
                          display: "flex",
                          justifyContent: "space-between",
                          alignItems: "flex-start",
                          mb: 0.5,
                        }}
                      >
                        <Typography variant="body1" fontWeight={600}>
                          {entityName}
                        </Typography>
                        {priority && (
                          <Chip
                            label={priority.toUpperCase()}
                            size="small"
                            color={getPriorityColor(priority as "high" | "medium" | "low")}
                          />
                        )}
                      </Box>
                      <Typography variant="caption" color="text.secondary" sx={{ display: "block", mb: 0.5 }}>
                        Type: {entityType}
                      </Typography>
                      {msioClassification && 
                       (msioClassification.discipline || 
                        msioClassification.category || 
                        msioClassification.subcategory || 
                        msioClassification.entity) && (
                        <Box sx={{ mt: 0.5 }}>
                          <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 500 }}>
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
                          <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 500 }}>
                            Rationale:{" "}
                          </Typography>
                          <Typography variant="caption" color="text.secondary" component="span">
                            {rationale}
                          </Typography>
                        </Box>
                      )}
                      {expectedAttributes &&
                        expectedAttributes.length > 0 && (
                          <Box sx={{ mt: 0.5, pt: 0.5, borderTop: "1px solid", borderColor: "divider" }}>
                            <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 500, mr: 0.5 }}>
                              Attributes:
                            </Typography>
                            <Box sx={{ display: "inline-flex", gap: 0.5, flexWrap: "wrap", mt: 0.25 }}>
                              {expectedAttributes.map((attr: string, idx: number) => (
                                <Chip key={idx} label={attr} size="small" variant="outlined" />
                              ))}
                            </Box>
                          </Box>
                        )}
                    </CardContent>
                  </Card>
                );
              })}
            </Box>
          </>
        )}
    </Box>
  );
};

export default BaseCaseRecommendationView;

