import React from "react";
import {
  Box,
  Typography,
  Paper,
  Card,
  CardContent,
  Chip,
  Grid,
  Divider,
} from "@mui/material";
import { Star as StarIcon } from "@mui/icons-material";
import ExpectedEffects from "./ExpectedEffects";

const RecommendationsDisplay = ({ recommendation }) => {
  if (!recommendation.approach_options || recommendation.approach_options.length === 0) {
    return (
      <Paper sx={{ p: 2 }}>
        <Typography variant="body2" color="text.secondary">
          No recommendations available
        </Typography>
      </Paper>
    );
  }

  return (
    <Box>
      {recommendation.recommendation_summary && (
        <Paper sx={{ p: 2, mb: 3 }}>
          <Typography variant="h6" gutterBottom>
            Recommendation Summary
          </Typography>
          <Typography variant="body2" style={{ whiteSpace: "pre-line" }}>
            {recommendation.recommendation_summary}
          </Typography>
        </Paper>
      )}

      <Typography variant="h6" gutterBottom sx={{ mb: 2 }}>
        Approach Options ({recommendation.approach_options.length})
      </Typography>

      <Grid container spacing={2}>
        {recommendation.approach_options.map((option, index) => (
          <Grid item xs={12} key={option.option_id || index}>
            <Card
              variant="outlined"
              sx={{
                border:
                  option.option_id === recommendation.recommended_option_id
                    ? 2
                    : 1,
                borderColor:
                  option.option_id === recommendation.recommended_option_id
                    ? "primary.main"
                    : "divider",
              }}
            >
              <CardContent>
                <Box
                  sx={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "start",
                    mb: 2,
                  }}
                >
                  <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                    <Typography variant="h6">{option.title}</Typography>
                    {option.option_id === recommendation.recommended_option_id && (
                      <Chip
                        icon={<StarIcon />}
                        label="Recommended"
                        color="primary"
                        size="small"
                      />
                    )}
                  </Box>
                  <Box sx={{ display: "flex", gap: 1 }}>
                    {option.feasibility_score !== null && (
                      <Chip
                        label={`Feasibility: ${(option.feasibility_score * 100).toFixed(0)}%`}
                        size="small"
                      />
                    )}
                    {option.impact_score !== null && (
                      <Chip
                        label={`Impact: ${(option.impact_score * 100).toFixed(0)}%`}
                        size="small"
                      />
                    )}
                  </Box>
                </Box>

                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  {option.rationale}
                </Typography>

                {option.expected_effects && Object.keys(option.expected_effects).length > 0 && (
                  <>
                    <Divider sx={{ my: 2 }} />
                    <ExpectedEffects expectedEffects={option.expected_effects} />
                  </>
                )}

                {option.dependencies && option.dependencies.length > 0 && (
                  <>
                    <Divider sx={{ my: 2 }} />
                    <Box>
                      <Typography variant="subtitle2" gutterBottom>
                        Dependencies:
                      </Typography>
                      <Box sx={{ display: "flex", flexWrap: "wrap", gap: 0.5 }}>
                        {option.dependencies.map((dep, i) => (
                          <Chip key={i} label={dep} size="small" variant="outlined" />
                        ))}
                      </Box>
                    </Box>
                  </>
                )}
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>
    </Box>
  );
};

export default RecommendationsDisplay;

