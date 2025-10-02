import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useParams } from 'react-router-dom';
import {
    Box,
    Typography,
    Grid,
    Paper,
    Button,
    Chip,
    LinearProgress,
    Alert,
    Snackbar,
} from '@mui/material';

import {
    fetchProjectEntitiesRelations,
    fetchProjectDocuments,
    selectEntitiesByProjectAndType,
    selectRelationsByProjectAndType,
    selectSummaryByProjectAndType,
    selectHasEntitiesRelationsData,
    selectIsDataStale,
    selectDataLoading,
    selectDataError,
    selectBaseCaseDocuments,
} from '../../redux/dataSlice';

import EntityDetailsTable from '../../components/EntityDetailsTable';

const BaseCaseView = () => {
    const { projectId } = useParams();
    const dispatch = useDispatch();

    // Get raw entities data
    const rawEntities = useSelector(state =>
        selectEntitiesByProjectAndType(state, projectId, 'base_case')
    ) || [];

    // Sort entities by type, then by name
    const entities = useMemo(() => {
        return [...rawEntities].sort((a, b) => {
            // First sort by type
            const typeA = a.type || 'Unknown';
            const typeB = b.type || 'Unknown';
            
            if (typeA !== typeB) {
                return typeA.localeCompare(typeB);
            }
            
            // If types are the same, sort by name
            const nameA = a.properties?.name || a.name || 'Unnamed Entity';
            const nameB = b.properties?.name || b.name || 'Unnamed Entity';
            
            return nameA.localeCompare(nameB);
        });
    }, [rawEntities]);

    const relations = useSelector(state =>
        selectRelationsByProjectAndType(state, projectId, 'base_case')
    ) || [];

    const summary = useSelector(state =>
        selectSummaryByProjectAndType(state, projectId, 'base_case')
    );

    const baseCaseDocuments = useSelector(selectBaseCaseDocuments) || [];

    // Check if we have data and if it's stale
    const hasData = useSelector(state =>
        selectHasEntitiesRelationsData(state, projectId, 'base_case')
    );
    const isDataStale = useSelector(state =>
        selectIsDataStale(state, projectId, 'base_case', 5 * 60 * 1000) // 5 minutes
    );

    const loading = useSelector(selectDataLoading);
    const error = useSelector(selectDataError);

    const [showSnackbar, setShowSnackbar] = useState(false);
    const [lastDocumentCount, setLastDocumentCount] = useState(0); // ✅ Track document count

    // Enhanced function to load base case data
    const loadBaseCaseData = useCallback(() => {
        if (projectId) {
            // Load entities and relations if no data or data is stale
            if (!hasData || isDataStale) {
                console.log('Loading base case data for project:', projectId);
                dispatch(fetchProjectEntitiesRelations({
                    projectId,
                    artifact_type: 'base_case',
                    include_metadata: true
                }));
            }

            // Load documents if not already loaded
            if (baseCaseDocuments.length === 0) {
                dispatch(fetchProjectDocuments({
                    projectId,
                    artifact_type: 'base_case'
                }));
            }
        }
    }, [dispatch, projectId, hasData, isDataStale, baseCaseDocuments.length]);

    // ✅ Watch for document count changes (indicates deletion/addition)
    useEffect(() => {
        const currentDocumentCount = baseCaseDocuments.length;
        
        // If document count decreased (document was deleted)
        if (lastDocumentCount > 0 && currentDocumentCount < lastDocumentCount) {
            console.log(`Document deleted - count changed from ${lastDocumentCount} to ${currentDocumentCount}`);
            
            // Force refresh entities and relations data
            dispatch(fetchProjectEntitiesRelations({
                projectId,
                artifact_type: 'base_case',
                include_metadata: true
            }));
        }
        
        setLastDocumentCount(currentDocumentCount);
    }, [baseCaseDocuments.length, lastDocumentCount, dispatch, projectId]);

    // ✅ Watch for cache invalidation by monitoring data staleness
    useEffect(() => {
        // If data becomes stale (cache was invalidated), reload it
        if (hasData && isDataStale && !loading.fetchEntitiesRelations) {
            console.log('Cache invalidated - reloading base case data');
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
            console.log('Force refreshing base case data');
            dispatch(fetchProjectEntitiesRelations({
                projectId,
                artifact_type: 'base_case',
                include_metadata: true
            }));
            dispatch(fetchProjectDocuments({
                projectId,
                artifact_type: 'base_case'
            }));
        }
    }, [dispatch, projectId]);

    // Memoized entity types for performance
    const entityTypes = useMemo(() => {
        const types = {};
        entities.forEach(entity => {
            const type = entity.type || 'unknown';
            types[type] = (types[type] || 0) + 1;
        });
        return types;
    }, [entities]);

    // Memoized relation types for performance
    const relationTypes = useMemo(() => {
        const types = {};
        relations.forEach(relation => {
            const type = relation.relation_type || relation.type || 'unknown';
            types[type] = (types[type] || 0) + 1;
        });
        return types;
    }, [relations]);

    useEffect(() => {
        if (error) {
            setShowSnackbar(true);
        }
    }, [error]);

    return (
        <Box sx={{ p: 3 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
                <Typography variant="h4" gutterBottom>
                    Base Case Analysis
                </Typography>
                {/* ✅ Add refresh button for manual cache refresh */}
                <Button
                    variant="outlined"
                    onClick={forceRefresh}
                    disabled={loading.fetchEntitiesRelations || loading.fetchDocuments}
                >
                    Refresh Data
                </Button>
            </Box>

            {loading.fetchEntitiesRelations && (
                <Box sx={{ mb: 2 }}>
                    <LinearProgress />
                    <Typography variant="caption" color="text.secondary">
                        Loading entities and relations...
                    </Typography>
                </Box>
            )}

            {/* ✅ Show notification when data is being refreshed after deletion */}
            {lastDocumentCount > baseCaseDocuments.length && loading.fetchEntitiesRelations && (
                <Alert severity="info" sx={{ mb: 2 }}>
                    Document deleted - refreshing data...
                </Alert>
            )}

            {summary && (
                <Paper sx={{ p: 2, mb: 3 }}>
                    <Typography variant="h6" gutterBottom>Summary</Typography>
                    <Grid container spacing={2}>
                        <Grid item xs={4}>
                            <Typography variant="body2" color="text.secondary">Entities</Typography>
                            <Typography variant="h5">{summary.entity_count}</Typography>
                        </Grid>
                        <Grid item xs={4}>
                            <Typography variant="body2" color="text.secondary">Relations</Typography>
                            <Typography variant="h5">{summary.relation_count}</Typography>
                        </Grid>
                        <Grid item xs={4}>
                            <Typography variant="body2" color="text.secondary">Documents</Typography>
                            <Typography variant="h5">{summary.document_count}</Typography>
                        </Grid>
                    </Grid>
                </Paper>
            )}

            <Grid container spacing={3}>
                <Grid item xs={12}>
                    <EntityDetailsTable 
                        entities={entities} 
                        title="Base Case Entities" 
                    />
                </Grid>

                <Grid item xs={12}>
                    <Paper sx={{ p: 2 }}>
                        <Typography variant="h6" gutterBottom>
                            Relations ({relations.length})
                        </Typography>

                        <Box sx={{ mb: 2 }}>
                            {Object.entries(relationTypes).map(([type, count]) => (
                                <Chip
                                    key={`relation-type-${type}`}
                                    label={`${type}: ${count}`}
                                    size="small"
                                    sx={{ mr: 1, mb: 1 }}
                                />
                            ))}
                        </Box>

                        <Box sx={{ maxHeight: 400, overflow: 'auto' }}>
                            {relations.map((relation, index) => (
                                <Box
                                    key={relation.relation_id || `relation-${index}`}
                                    sx={{
                                        p: 1,
                                        borderBottom: '1px solid',
                                        borderColor: 'divider'
                                    }}
                                >
                                    <Typography variant="body2">
                                        {relation.source_entity} → {relation.target_entity}
                                    </Typography>
                                    <Typography variant="caption" color="text.secondary">
                                        Type: {relation.relation_type || relation.type}
                                    </Typography>
                                </Box>
                            ))}
                        </Box>
                    </Paper>
                </Grid>
            </Grid>

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

export default BaseCaseView;