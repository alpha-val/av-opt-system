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
    selectEntitiesByProjectAndType,
    selectRelationsByProjectAndType,
    selectSummaryByProjectAndType,
    selectHasEntitiesRelationsData,
    selectIsDataStale,
    selectDataLoading,
    selectDataError,
} from '../../redux/dataSlice';

const BaseCaseView = () => {
    const { projectId } = useParams();
    const dispatch = useDispatch();

    // Use memoized selectors
    const entities = useSelector(state =>
        selectEntitiesByProjectAndType(state, projectId, 'base_case')
    );
    const relations = useSelector(state =>
        selectRelationsByProjectAndType(state, projectId, 'base_case')
    );
    const summary = useSelector(state =>
        selectSummaryByProjectAndType(state, projectId, 'base_case')
    );
    console.log('Entities:', entities);
    console.log('Relations:', relations);
    console.log('Summary:', summary);
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

    // Memoized function to load base case data
    const loadBaseCaseData = useCallback(() => {
        if (projectId && (!hasData || isDataStale)) {
            dispatch(fetchProjectEntitiesRelations({
                projectId,
                artifact_type: 'base_case',
                include_metadata: true
            }));
        } else {
            // console.log('Using cached base case data for project:', projectId);
        }
    }, [dispatch, projectId, hasData, isDataStale]);

    // Load data only when needed
    useEffect(() => {
        loadBaseCaseData();
    }, [loadBaseCaseData]);

    // Memoized function to load scenario data
    const fetchScenarioData = useCallback(() => {
        if (projectId) {
            dispatch(fetchProjectEntitiesRelations({
                projectId,
                artifact_type: 'scenario',
                include_metadata: true
            }));
        }
    }, [dispatch, projectId]);

    // Memoized function to load specific entity types
    const fetchSpecificEntityType = useCallback((entityType) => {
        if (projectId) {
            dispatch(fetchProjectEntitiesRelations({
                projectId,
                artifact_type: 'base_case',
                entity_type: entityType,
                include_metadata: false
            }));
        }
    }, [dispatch, projectId]);

    // Force refresh function
    const forceRefresh = useCallback(() => {
        if (projectId) {
            console.log('Force refreshing base case data');
            dispatch(fetchProjectEntitiesRelations({
                projectId,
                artifact_type: 'base_case',
                include_metadata: true
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
            </Box>

            {loading.fetchEntitiesRelations && (
                <Box sx={{ mb: 2 }}>
                    <LinearProgress />
                    <Typography variant="caption" color="text.secondary">
                        Loading entities and relations...
                    </Typography>
                </Box>
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

            <Box sx={{ mb: 3 }}>
                <Button
                    variant="contained"
                    onClick={fetchScenarioData}
                    sx={{ mr: 2 }}
                >
                    Load Scenario Data
                </Button>

                <Button
                    variant="outlined"
                    onClick={() => fetchSpecificEntityType('COMMODITY')}
                >
                    Load Commodities Only
                </Button>
            </Box>

            <Grid container spacing={3}>
                <Grid item xs={12} md={6}>
                    <Paper sx={{ p: 2 }}>
                        <Typography variant="h6" gutterBottom>
                            Entities ({entities.length})
                        </Typography>

                        {/* Entity types summary*/}
                        <Box sx={{ mb: 2 }}>
                            {Object.entries(entityTypes).map(([type, count]) => (
                                <Chip
                                    key={`entity-type-${type}`}
                                    label={`${type}: ${count}`}
                                    size="small"
                                    sx={{ mr: 1, mb: 1 }}Í
                                />
                            ))}
                        </Box>

                        <Box sx={{ maxHeight: 400, overflow: 'auto' }}>
                            {entities.map((entity, index) => (
                                <Box 
                                    key={entity.entity_id || `entity-${index}`}
                                    sx={{
                                        p: 1,
                                        borderBottom: '1px solid',
                                        borderColor: 'divider'
                                    }}
                                >
                                    <Typography variant="body2" fontWeight="medium">
                                        {entity.name || entity.entity_id}
                                    </Typography>
                                    <Typography variant="caption" color="text.secondary">
                                        Type: {entity.type}
                                    </Typography>
                                </Box>
                            ))}
                        </Box>
                    </Paper>
                </Grid>

                <Grid item xs={12} md={6}>
                    <Paper sx={{ p: 2 }}>
                        <Typography variant="h6" gutterBottom>
                            Relations ({relations.length})
                        </Typography>

                        {/* Relation types summary*/}
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