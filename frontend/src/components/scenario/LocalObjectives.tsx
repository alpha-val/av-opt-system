import React, { useEffect, useState } from "react";
import {
  Box,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  CircularProgress,
  Alert,
  Chip,
} from "@mui/material";
import { scenarioApi } from "../../services/api";

interface LocalObjectivesProps {
  scenarioId: string;
}

/**
 * Local Objectives Component
 * 
 * Displays base case entities for a scenario in a tabular format.
 * Shows Name, Type, Attributes, and MSIO classification.
 */
const LocalObjectives: React.FC<LocalObjectivesProps> = ({ scenarioId }) => {
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [entities, setEntities] = useState<Array<{
    id: string;
    type: string;
    properties: {
      name?: string;
      discipline?: string;
      category?: string;
      subcategory?: string;
      entity?: string;
      attributes?: Array<{
        name: string;
        value: number | null;
        unit: string | null;
        evidence_text: string | null;
        confidence: number;
      }>;
      [key: string]: any;
    };
  }>>([]);

  useEffect(() => {
    const fetchEntities = async () => {
      if (!scenarioId) {
        setError("Scenario ID is required");
        setLoading(false);
        return;
      }

      try {
        setLoading(true);
        setError(null);
        const data = await scenarioApi.getEntities(scenarioId, "base_case");
        setEntities(data.entities || []);
      } catch (err) {
        const errorMessage =
          err instanceof Error ? err.message : "Failed to fetch entities";
        setError(errorMessage);
        setEntities([]);
      } finally {
        setLoading(false);
      }
    };

    fetchEntities();
  }, [scenarioId]);

  /**
   * Format attributes for display
   */
  const formatAttributes = (attributes?: Array<{
    name: string;
    value: number | null;
    unit: string | null;
    evidence_text: string | null;
    confidence: number;
  }>): string => {
    if (!attributes || attributes.length === 0) {
      return "N/A";
    }

    return attributes
      .map((attr) => {
        const value = attr.value !== null ? attr.value : "N/A";
        const unit = attr.unit || "";
        return `${attr.name}: ${value}${unit ? ` ${unit}` : ""}`;
      })
      .join(", ");
  };

  /**
   * Format MSIO classification for display
   */
  const formatMSIOClassification = (props: {
    discipline?: string;
    category?: string;
    subcategory?: string;
    entity?: string;
  }): string => {
    const parts = [
      props.discipline || "N/A",
      props.category || "N/A",
      props.subcategory || "N/A",
      props.entity || "N/A",
    ];
    return parts.join(" / ");
  };

  if (loading) {
    return (
      <Box sx={{ display: "flex", justifyContent: "center", p: 3 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ m: 2 }}>
        {error}
      </Alert>
    );
  }

  if (entities.length === 0) {
    return (
      <Alert severity="info" sx={{ m: 2 }}>
        No base case entities found for this scenario. Run analysis to extract entities.
      </Alert>
    );
  }

  return (
    <Box>
      <Typography variant="body2" color="text.secondary" gutterBottom>
        Showing {entities.length} base case entities
      </Typography>
      <TableContainer component={Paper} sx={{ mt: 2 }}>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell><strong>Name</strong></TableCell>
              <TableCell><strong>Type</strong></TableCell>
              <TableCell><strong>Attributes</strong></TableCell>
              <TableCell><strong>MSIO Classification</strong></TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {entities.map((entity) => (
              <TableRow key={entity.id}>
                <TableCell>
                  {entity.properties?.name || "N/A"}
                </TableCell>
                <TableCell>
                  <Chip label={entity.type} size="small" variant="outlined" />
                </TableCell>
                <TableCell>
                  <Typography variant="body2" sx={{ fontSize: "0.875rem" }}>
                    {formatAttributes(entity.properties?.attributes)}
                  </Typography>
                </TableCell>
                <TableCell>
                  <Typography variant="body2" sx={{ fontSize: "0.875rem" }}>
                    {formatMSIOClassification({
                      discipline: entity.properties?.discipline,
                      category: entity.properties?.category,
                      subcategory: entity.properties?.subcategory,
                      entity: entity.properties?.entity,
                    })}
                  </Typography>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
};

export default LocalObjectives;

