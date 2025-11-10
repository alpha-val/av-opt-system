import React from "react";
import {
  Card,
  CardContent,
  Typography,
  Box,
  Divider,
  Grid,
} from "@mui/material";

// Helper to get cost value from entity
function getCost(entity) {
  const props = entity.properties || {};
  return (
    Number(props.cost_value) ||
    Number(entity.cost_value) ||
    Number(props.base_cost) ||
    Number(props.unit_cost) ||
    0
  );
}

function getName(entity) {
  return entity.properties?.name || entity.name || "Unnamed";
}

const CostDetails = ({ data }) => {
  if (!data || !data.metadata) return null;
  console.log("[CostDetails] data:", data); // Debug log
  const baseCaseEntities = data.metadata.cost_details.matched_data.map((d) => d.base_entity) || [];
  const tabularEntities = data.metadata.cost_details.tabular_entities || [];
  const baseTotal = baseCaseEntities.reduce((sum, e) => sum + getCost(e), 0);
  const tabularTotal = tabularEntities.reduce((sum, e) => sum + getCost(e), 0);
  const delta = tabularTotal - baseTotal;

  return (
    <Box sx={{ mt: 2 }}>
      <Grid container spacing={2}>
        {/* Base Case Entities Card */}
        <Grid item xs={12} md={4}>
          <Card variant="outlined">
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Base Case Entities
              </Typography>
              <Divider sx={{ mb: 1 }} />
              {baseCaseEntities.map((e) => (
                <Box key={e.id} sx={{ mb: 1 }}>
                  <Typography variant="body2">
                    {getName(e)}: <b>${getCost(e).toLocaleString()}</b>
                  </Typography>
                </Box>
              ))}
              <Divider sx={{ my: 1 }} />
              <Typography variant="subtitle1">
                <b>Total: ${baseTotal.toLocaleString()}</b>
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* Proposed (Tabular) Entities Card */}
        <Grid item xs={12} md={4}>
          <Card variant="outlined">
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Proposed (Tabular) Entities
              </Typography>
              <Divider sx={{ mb: 1 }} />
              {tabularEntities.map((e) => (
                <Box key={e.id} sx={{ mb: 1 }}>
                  <Typography variant="body2">
                    {getName(e)}: <b>${getCost(e).toLocaleString()}</b>
                  </Typography>
                </Box>
              ))}
              <Divider sx={{ my: 1 }} />
              <Typography variant="subtitle1">
                <b>Total: ${tabularTotal.toLocaleString()}</b>
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* Delta Card */}
        <Grid item xs={12} md={4}>
          <Card variant="outlined" sx={{ bgcolor: "#f9f9f9" }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Cost Difference
              </Typography>
              <Divider sx={{ mb: 1 }} />
              <Typography variant="body1">
                <b>Proposed - Base Case: ${delta.toLocaleString()}</b>
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default CostDetails;
