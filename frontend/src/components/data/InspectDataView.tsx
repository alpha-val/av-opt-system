import React, { useEffect, useState } from "react";
import { Box, CircularProgress, Alert } from "@mui/material";
import { projectApi } from "../../services/api";
import EntityDetailsTable from "./EntityDetailsTable";

interface InspectDataViewProps {
  projectId: string;
  artifactType?: string;
}

/**
 * InspectDataView Component
 *
 * Fetches and displays tabular data entities for a given project.
 * Uses EntityDetailsTable to display the entities in a structured table format.
 */
const InspectDataView: React.FC<InspectDataViewProps> = ({
  projectId,
  artifactType = "tabular_data",
}) => {
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [entities, setEntities] = useState<Array<{
    id: string;
    type: string;
    properties: {
      name?: string;
      [key: string]: any;
    };
  }>>([]);

  useEffect(() => {
    const fetchEntities = async () => {
      if (!projectId) {
        setError("Project ID is required");
        setLoading(false);
        return;
      }

      try {
        setLoading(true);
        setError(null);

        const data = await projectApi.getEntities(projectId, artifactType);
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
  }, [projectId, artifactType]);

  if (loading) {
    return (
      <Box sx={{ display: "flex", justifyContent: "center", p: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ mb: 2 }}>
        {error}
      </Alert>
    );
  }

  const title = artifactType === "base_case" 
    ? "Base Case Entities" 
    : artifactType === "tabular_data"
    ? "Tabular Data Entities"
    : "Project Entities";
  // console.log("[InspectDataView] Entities:", entities);
  return (
    <Box>
      <EntityDetailsTable entities={entities} title={title} />
    </Box>
  );
};

export default InspectDataView;

