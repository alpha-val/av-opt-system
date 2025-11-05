import React, { useState, useEffect, useMemo, useCallback } from "react";
import { useDispatch, useSelector } from "react-redux";
import {
  Box,
  Typography,
  Paper,
  Button,
  LinearProgress,
  Alert,
  Tabs,
  Tab,
  Grid,
} from "@mui/material";
import { Refresh as RefreshIcon } from "@mui/icons-material";

import {
  fetchProjectEntitiesRelations,
  selectEntitiesByProject,
  selectRelationsByProject,
  selectSummaryByProject,
  selectHasEntitiesRelationsDataForProject,
  selectIsDataStaleForProject,
  selectDataLoading,
  selectDataError,
} from "../../../redux/dataSlice";
import { selectDocumentsLoading } from "../../../redux/documentSlice";

import EntityDetailsTable from "../data/EntityDetailsTable";
import RelationsDetailsView from "../data/RelationsDetailsView";

const ViewDataTab = ({ projectId }) => {
  const dispatch = useDispatch();
  const [tabValue, setTabValue] = useState(0);

  // Get raw entities data
  const rawEntities =
    useSelector((state) => selectEntitiesByProject(state, projectId)) || [];
  console.log("rawEntities", rawEntities);
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

  // Check if we have data and if it's stale
  const hasData = useSelector((state) =>
    selectHasEntitiesRelationsDataForProject(state, projectId)
  );

  const isDataStale = useSelector(
    (state) => selectIsDataStaleForProject(state, projectId, 5 * 60 * 1000) // 5 minutes
  );

  const loading = useSelector(selectDataLoading);
  const error = useSelector(selectDataError);
  const documentsLoading = useSelector(selectDocumentsLoading);

  // Track previous ingestion state to detect completion
  const prevIngestBaseCaseRef = React.useRef(false);
  const prevUploadRef = React.useRef(false);

  // Initialize refs on mount
  React.useEffect(() => {
    prevIngestBaseCaseRef.current = documentsLoading.ingestBaseCase;
    prevUploadRef.current = documentsLoading.upload;
  }, []); // Only on mount

  // Load data function
  const loadData = useCallback(() => {
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
    }
  }, [dispatch, projectId, hasData, isDataStale]);

  // Load data on mount and when stale
  useEffect(() => {
    loadData();
  }, [loadData]);

  // Auto-refresh when document ingestion completes
  useEffect(() => {
    const ingestJustCompleted =
      prevIngestBaseCaseRef.current && !documentsLoading.ingestBaseCase;
    const uploadJustCompleted =
      prevUploadRef.current && !documentsLoading.upload;

    if ((ingestJustCompleted || uploadJustCompleted) && projectId) {
      // Wait a brief moment for backend to finish processing
      const timer = setTimeout(() => {
        dispatch(
          fetchProjectEntitiesRelations({
            projectId,
            include_metadata: true,
          })
        );
      }, 1000); // 1 second delay to ensure backend has processed

      return () => clearTimeout(timer);
    }

    // Update refs
    prevIngestBaseCaseRef.current = documentsLoading.ingestBaseCase;
    prevUploadRef.current = documentsLoading.upload;
  }, [
    documentsLoading.ingestBaseCase,
    documentsLoading.upload,
    dispatch,
    projectId,
  ]);

  // Force refresh function
  const forceRefresh = useCallback(() => {
    if (projectId) {
      dispatch(
        fetchProjectEntitiesRelations({
          projectId,
          include_metadata: true,
        })
      );
    }
  }, [dispatch, projectId]);

  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
  };

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box
        sx={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          mb: 3,
        }}
      >
        <Box>
          <Typography variant="h5" gutterBottom>
            View Extracted Data
          </Typography>
          <Typography variant="body2" color="text.secondary">
            View entities and relations extracted from documents
          </Typography>
        </Box>
        <Button
          variant="outlined"
          startIcon={<RefreshIcon />}
          onClick={forceRefresh}
          disabled={loading.fetchEntitiesRelations}
        >
          Refresh
        </Button>
      </Box>

      {/* Loading indicator */}
      {loading.fetchEntitiesRelations && (
        <Box sx={{ mb: 2 }}>
          <LinearProgress />
          <Typography variant="caption" color="text.secondary">
            Loading entities and relations...
          </Typography>
        </Box>
      )}

      {/* Error alert */}
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {/* Summary */}
      {summary && (
        <Paper sx={{ p: 2, mb: 3 }}>
          <Typography variant="h6" gutterBottom>
            Summary
          </Typography>
          <Grid container spacing={2}>
            <Grid item xs={12} sm={4}>
              <Typography variant="body2" color="text.secondary">
                Total Entities
              </Typography>
              <Typography variant="h5">{entities.length}</Typography>
              <Typography variant="caption" color="text.secondary">
                Base Case: {baseCaseEntities.length} | Tabular:{" "}
                {tabularDataEntities.length}
              </Typography>
            </Grid>
            <Grid item xs={12} sm={4}>
              <Typography variant="body2" color="text.secondary">
                Total Relations
              </Typography>
              <Typography variant="h5">{relations.length}</Typography>
              <Typography variant="caption" color="text.secondary">
                Base Case: {baseCaseRelations.length} | Tabular:{" "}
                {tabularDataRelations.length}
              </Typography>
            </Grid>
            <Grid item xs={12} sm={4}>
              <Typography variant="body2" color="text.secondary">
                Documents Processed
              </Typography>
              <Typography variant="h5">
                {summary.document_count || 0}
              </Typography>
            </Grid>
          </Grid>
        </Paper>
      )}

      {/* Tabs for different views */}
      <Paper elevation={0} sx={{ width: "100%" }}>
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
            label={`Tabular Data Entities (${tabularDataEntities.length})`}
            id="tab-2"
            aria-controls="tabpanel-2"
          />
          <Tab
            label={`Tabular Data Relations (${tabularDataRelations.length})`}
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
        >
          {tabValue === 1 && (
            <RelationsDetailsView
              relations={baseCaseRelations}
              entities={baseCaseEntities}
              title="Base Case Relations"
            />
          )}
        </Box>

        {/* Tabular Data Entities Tab */}
        <Box
          role="tabpanel"
          hidden={tabValue !== 2}
          id="tabpanel-2"
          aria-labelledby="tab-2"
        >
          {tabValue === 2 && (
            <EntityDetailsTable
              entities={tabularDataEntities}
              title="Tabular Data Entities"
            />
          )}
        </Box>

        {/* Tabular Data Relations Tab */}
        <Box
          role="tabpanel"
          hidden={tabValue !== 3}
          id="tabpanel-3"
          aria-labelledby="tab-3"
        >
          {tabValue === 3 && (
            <RelationsDetailsView
              relations={tabularDataRelations}
              entities={tabularDataEntities}
              title="Tabular Data Relations"
            />
          )}
        </Box>
      </Paper>

      {/* No data message */}
      {!loading.fetchEntitiesRelations && entities.length === 0 && (
        <Box sx={{ textAlign: "center", py: 4 }}>
          <Typography variant="h6" color="text.secondary" gutterBottom>
            No Entities Found
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Upload and process documents to see extracted entities here.
          </Typography>
        </Box>
      )}
    </Box>
  );
};

export default ViewDataTab;
