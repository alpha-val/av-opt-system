import React, { useState, useEffect, useMemo, useCallback } from "react";
import { useDispatch, useSelector } from "react-redux";
import { useParams } from "react-router-dom";
import {
  Box,
  Typography,
  Grid,
  Paper,
  Button,
  LinearProgress,
  Alert,
  Snackbar,
  Tabs,
  Tab,
} from "@mui/material";

import {
  fetchProjectEntitiesRelations,
  fetchProjectDocuments,
  selectEntitiesByProject,
  selectRelationsByProject,
  selectSummaryByProject,
  selectHasEntitiesRelationsDataForProject,
  selectIsDataStaleForProject,
  selectDataLoading,
  selectDataError,
  selectBaseCaseDocuments,
  selectBaseCaseDocumentsByProjectId,
} from "../../redux/dataSlice";

import EntityDetailsTable from "../../components/EntityDetailsTable";
import RelationsDetailsView from "../../components/RelationsDetailsView";
import TableEntityDetailsTable from "../../components/TableEntityDetailsTable";
import DocumentDetailsView from "../../components/DocumentsMetaDataView";

const InspectDataView = () => {
  const { projectId } = useParams();
  const dispatch = useDispatch();

  // Tab state
  const [tabValue, setTabValue] = useState(0);

  // Get base case documents for the project
  const baseCaseDocsByProjectId = useSelector((state) =>
    selectBaseCaseDocumentsByProjectId(state, projectId)
  ) || [];

  // Get raw entities data
  const rawEntities =
    useSelector((state) => selectEntitiesByProject(state, projectId)) || [];

  // Sort entities by type, then by name
  const entities = useMemo(() => {
    return [...rawEntities].sort((a, b) => {
      // First sort by type
      const typeA = a.type || "Unknown";
      const typeB = b.type || "Unknown";

      if (typeA !== typeB) {
        return typeA.localeCompare(typeB);
      }

      // If types are the same, sort by name
      const nameA = a.properties?.name || a.name || "Unnamed Entity";
      const nameB = b.properties?.name || b.name || "Unnamed Entity";

      return nameA.localeCompare(nameB);
    });
  }, [rawEntities]);

  // Filter entities by artifact_type
  const baseCaseEntities = useMemo(() => {
    return entities.filter(
      (entity) => entity.properties?.artifact_type === "base_case"
    );
  }, [entities]);

  const tabularDataEntities = useMemo(() => {
    return entities.filter(
      (entity) => entity.properties?.artifact_type === "tabular_data"
    );
  }, [entities]);

  // Get relations
  const relations =
    useSelector((state) => selectRelationsByProject(state, projectId)) || [];

  // Filter relations by artifact_type
  const baseCaseRelations = useMemo(() => {
    return relations.filter(
      (relation) => relation.properties?.artifact_type === "base_case"
    );
  }, [relations]);

  const tabularDataRelations = useMemo(() => {
    return relations.filter(
      (relation) => relation.properties?.artifact_type === "tabular_data"
    );
  }, [relations]);

  // Get summary
  const summary = useSelector((state) =>
    selectSummaryByProject(state, projectId)
  );

  const baseCaseDocuments = useSelector(selectBaseCaseDocuments) || [];

  // Check if we have data and if it's stale
  const hasData = useSelector((state) =>
    selectHasEntitiesRelationsDataForProject(state, projectId)
  );

  const isDataStale = useSelector(
    (state) => selectIsDataStaleForProject(state, projectId, 5 * 60 * 1000) // 5 minutes
  );

  const loading = useSelector(selectDataLoading);
  const error = useSelector(selectDataError);

  const [showSnackbar, setShowSnackbar] = useState(false);
  const [lastDocumentCount, setLastDocumentCount] = useState(0);

  // Enhanced function to load base case data
  const loadBaseCaseData = useCallback(() => {
    if (projectId) {
      // Load entities and relations if no data or data is stale
      if (!hasData || isDataStale) {
        dispatch(
          fetchProjectEntitiesRelations({
            projectId,
            include_metadata: true,
          })
        );
      }

      // Load documents if not already loaded
      if (baseCaseDocuments.length === 0) {
        dispatch(
          fetchProjectDocuments({
            projectId,
            artifact_type: "base_case",
          })
        );
      }
    }
  }, [dispatch, projectId, hasData, isDataStale, baseCaseDocuments.length]);

  // Watch for document count changes (indicates deletion/addition)
  useEffect(() => {
    const currentDocumentCount = baseCaseDocuments.length;

    // If document count decreased (document was deleted)
    if (lastDocumentCount > 0 && currentDocumentCount < lastDocumentCount) {
      // Force refresh entities and relations data
      dispatch(
        fetchProjectEntitiesRelations({
          projectId,
          include_metadata: true,
        })
      );
    }

    setLastDocumentCount(currentDocumentCount);
  }, [baseCaseDocuments.length, lastDocumentCount, dispatch, projectId]);

  // Watch for cache invalidation by monitoring data staleness
  useEffect(() => {
    // If data becomes stale (cache was invalidated), reload it
    if (hasData && isDataStale && !loading.fetchEntitiesRelations) {
      loadBaseCaseData();
    }
  }, [hasData, isDataStale, loading.fetchEntitiesRelations, loadBaseCaseData]);

  // Load data on mount
  useEffect(() => {
    loadBaseCaseData();
  }, [loadBaseCaseData]);

  // Force refresh function
  const forceRefresh = useCallback(() => {
    if (projectId) {
      dispatch(
        fetchProjectEntitiesRelations({
          projectId,
          include_metadata: true,
        })
      );
      dispatch(
        fetchProjectDocuments({
          projectId,
          artifact_type: "base_case",
        })
      );
    }
  }, [dispatch, projectId]);

  useEffect(() => {
    if (error) {
      setShowSnackbar(true);
    }
  }, [error]);

  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
  };

  return (
    <Box sx={{ p: 0 }}>
      {loading.fetchEntitiesRelations && (
        <Box sx={{ mb: 2 }}>
          <LinearProgress />
          <Typography variant="caption" color="text.secondary">
            Loading entities and relations...
          </Typography>
        </Box>
      )}

      {/* Show notification when data is being refreshed after deletion */}
      {lastDocumentCount > baseCaseDocuments.length &&
        loading.fetchEntitiesRelations && (
          <Alert severity="info" sx={{ mb: 2 }}>
            Document deleted - refreshing data...
          </Alert>
        )}

      {summary && (
        <Paper sx={{ p: 2, mb: 3 }}>
          <Typography variant="h6" gutterBottom>
            Summary
          </Typography>
          <Grid container spacing={2}>
            <Grid xs={4}>
              <Typography variant="body2" color="text.secondary">
                Entities
              </Typography>
              <Typography variant="h5">{summary.entity_count}</Typography>
            </Grid>
            <Grid xs={4}>
              <Typography variant="body2" color="text.secondary">
                Relations
              </Typography>
              <Typography variant="h5">{summary.relation_count}</Typography>
            </Grid>
            <Grid xs={4}>
              <Typography variant="body2" color="text.secondary">
                Documents
              </Typography>
              <Typography variant="h5">{summary.document_count}</Typography>
            </Grid>
          </Grid>
        </Paper>
      )}

      <Paper elevation={0} sx={{ p: 0, width: "100%" }}>
        <Tabs
          value={tabValue}
          onChange={handleTabChange}
          indicatorColor="primary"
          textColor="primary"
          sx={{ borderBottom: 1, borderColor: "divider" }}
        >
          <Tab
            label={`Base Case Entities (${baseCaseEntities.length})`}
            id="tab-0"
            aria-controls="tabpanel-0"
          />
          <Tab
            label={`Base Case Relations (${baseCaseRelations.length})`}
            id="tab-1"
            aria-controls="tabpanel-1"
          />
          <Tab
            label={`Tabular Data (${tabularDataEntities.length})`}
            id="tab-2"
            aria-controls="tabpanel-2"
          />
          <Tab
            label={`Documents Meta Data (${baseCaseDocsByProjectId.length})`}
            id="tab-3"
            aria-controls="tabpanel-3"
          />
        </Tabs>

        {/* Base Case Entities Tab */}
        <Box
          role="tabpanel"
          hidden={tabValue !== 0}
          id="tabpanel-0"
          aria-labelledby="tab-0"
          sx={{ p: 0 }}
        >
          {tabValue === 0 && (
            <EntityDetailsTable
              entities={baseCaseEntities}
              title="Base Case Entities"
            />
          )}
        </Box>

        {/* Base Case Relations Tab */}
        <Box
          role="tabpanel"
          hidden={tabValue !== 1}
          id="tabpanel-1"
          aria-labelledby="tab-1"
          sx={{ p: 0 }}
        >
          {tabValue === 1 && (
            <RelationsDetailsView
              relations={baseCaseRelations}
              entities={baseCaseEntities}
              title="Base Case Relations"
            />
          )}
        </Box>

        {/* Tabular Data Tab */}
        <Box
          role="tabpanel"
          hidden={tabValue !== 2}
          id="tabpanel-2"
          aria-labelledby="tab-2"
          sx={{ p: 0 }}
        >
          {tabValue === 2 && (
            <EntityDetailsTable
              entities={tabularDataEntities}
              title="Tabular Data Entities"
            />
          )}
        </Box>

        {/* Documents Meta Data Tab */}
        <Box
          role="tabpanel"
          hidden={tabValue !== 3}
          id="tabpanel-3"
          aria-labelledby="tab-3"
          sx={{ p: 0 }}
        >
          {tabValue === 3 && (
            <DocumentDetailsView
              documents={baseCaseDocsByProjectId}
              title="Documents Meta Data"
            />
          )}
        </Box>
      </Paper>

      <Snackbar
        open={showSnackbar}
        autoHideDuration={6000}
        onClose={() => setShowSnackbar(false)}
      >
        <Alert onClose={() => setShowSnackbar(false)} severity="error">
          {error}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default InspectDataView;
