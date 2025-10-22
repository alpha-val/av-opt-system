import React, { useState } from 'react';
import { useSelector } from 'react-redux';
import {
    Card,
    CardContent,
    Typography,
    Chip,
    Box,
    Grid,
    Collapse,
    IconButton,
    Divider,
    Tooltip,
} from '@mui/material';
import {
    ExpandMore as ExpandMoreIcon,
    Info as InfoIcon,
    Source as SourceIcon,
    Description as DocumentIcon,
} from '@mui/icons-material';

// Import the selector
import { selectBaseCaseDocuments } from '../redux/dataSlice';

const EntityDetails = ({ entity, compact = false }) => {
    const [expanded, setExpanded] = useState(false);

    // Get base case documents using the selector
    const baseCaseDocuments = useSelector(selectBaseCaseDocuments);

    const handleExpandClick = () => {
        setExpanded(!expanded);
    };

    // Extract main properties
    const entityName = entity.properties?.name || entity.name || 'Unnamed Entity';
    const entityType = entity.type || 'Unknown';
    const confidence = entity.properties?.confidence || entity.confidence;
    const shortDescription = entity.properties?.short_description || entity.properties?.description;

    // Find the document that this entity belongs to

    const entityDocument = baseCaseDocuments.find(doc => doc.doc_id === entity.properties.doc_id);

    // Filter out common metadata fields to show only relevant properties
    const excludeFields = new Set([
        'name', 'type', 'confidence', 'short_description', 'description',
        'project_id', 'user_id', 'doc_id', 'canonical_key', 'artifact_type',
        'extracted_from', 'entity_id', 'sources'
    ]);

    // Get properties from either the properties object or the entity itself
    const allProperties = { ...entity.properties, ...entity };
    const relevantProperties = Object.entries(allProperties)
        .filter(([key, value]) =>
            !excludeFields.has(key) &&
            value != null &&
            value !== '' &&
            typeof value !== 'object'
        )
        .sort(([a], [b]) => a.localeCompare(b));

    // Format property names for display
    const formatPropertyName = (key) => {
        return key
            .replace(/([A-Z])/g, ' $1')
            .replace(/_/g, ' ')
            .replace(/\b\w/g, l => l.toUpperCase());
    };

    // Format property values
    const formatPropertyValue = (value) => {
        if (typeof value === 'string' && value.length > 50 && !expanded) {
            return value.substring(0, 50) + '...';
        }
        return value;
    };

    // Get entity type color
    const getTypeColor = (type) => {
        const colors = {
            'Material': 'primary',
            'Equipment': 'secondary',
            'Location': 'success',
            'Process': 'warning',
            'Chemical': 'info',
            'Commodity': 'error',
        };
        return colors[type] || 'default';
    };

    // Format document name for display
    const getDocumentDisplayName = (doc) => {
        if (!doc) return 'Unknown Document';

        // Use originalName if available, otherwise fileName, otherwise doc_id
        return doc.originalName || doc.fileName || `Document ${doc.doc_id.substring(0, 8)}...`;
    };

    return (
        <Card
            variant="outlined"
            sx={{
                mb: 1,
                transition: 'all 0.2s ease-in-out',
                '&:hover': {
                    boxShadow: 2,
                    transform: 'translateY(-1px)',
                },
                ...(compact && { maxWidth: 400 })
            }}
        >
            <CardContent sx={{ p: 2, '&:last-child': { pb: 2 } }}>
                {/* Header */}
                <Box sx={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', mb: 1 }}>
                    <Box sx={{ flex: 1, minWidth: 0 }}>
                        <Typography
                            variant="h6"
                            component="div"
                            sx={{
                                fontWeight: 600,
                                fontSize: '1rem',
                                overflow: 'hidden',
                                textOverflow: 'ellipsis',
                                whiteSpace: 'nowrap',
                                mb: 0.5
                            }}
                        >
                            {entityName}
                        </Typography>

                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap' }}>
                            <Chip
                                label={entityType}
                                size="small"
                                color={getTypeColor(entityType)}
                                variant="outlined"
                            />

                            {confidence && (
                                <Tooltip title="Extraction Confidence">
                                    <Chip
                                        icon={<InfoIcon sx={{ fontSize: 14 }} />}
                                        label={`${Math.round(parseFloat(confidence) * 100)}%`}
                                        size="small"
                                        variant="outlined"
                                        color={parseFloat(confidence) > 0.8 ? 'success' : 'warning'}
                                    />
                                </Tooltip>
                            )}

                            {/* Show document chip if we found the document */}
                            {entityDocument && (
                                <Tooltip title={`Source: ${getDocumentDisplayName(entityDocument)}`}>
                                    <Chip
                                        icon={<DocumentIcon sx={{ fontSize: 14 }} />}
                                        label={`Source: ${entityDocument ? getDocumentDisplayName(entityDocument) : ''}`}
                                        size="small"
                                        variant="outlined"
                                        color="info"
                                    />
                                </Tooltip>
                            )}

                            {/* Legacy sources support */}
                            {/* {entity.sources && entity.sources.length > 0 && (
                                <Tooltip title={`${entity.sources.length} source(s)`}>
                                    <Chip
                                        icon={<SourceIcon sx={{ fontSize: 14 }} />}
                                        label={entity.sources.length}
                                        size="small"
                                        variant="outlined"
                                        color="secondary"
                                    />
                                </Tooltip>
                            )} */}
                        </Box>
                    </Box>

                    {(relevantProperties.length > 0 || entityDocument || (entity.sources && entity.sources.length > 0)) && (
                        <IconButton
                            onClick={handleExpandClick}
                            size="small"
                            sx={{
                                transform: expanded ? 'rotate(180deg)' : 'rotate(0deg)',
                                transition: 'transform 0.2s ease-in-out',
                            }}
                        >
                            <ExpandMoreIcon />
                        </IconButton>
                    )}
                </Box>

                {/* Short Description */}
                {shortDescription && (
                    <Typography
                        variant="body2"
                        color="text.secondary"
                        sx={{
                            mb: 1,
                            fontStyle: 'italic',
                            overflow: 'hidden',
                            textOverflow: 'ellipsis',
                            whiteSpace: expanded ? 'normal' : 'nowrap'
                        }}
                    >
                        {formatPropertyValue(shortDescription)}
                    </Typography>
                )}

                {/* Quick Properties Preview (top 3) */}
                {!expanded && relevantProperties.length > 0 && (
                    <Box sx={{ mt: 1 }}>
                        <Grid container spacing={1}>
                            {relevantProperties.slice(0, 3).map(([key, value]) => (
                                <Grid xs={12} sm={6} key={key}>
                                    <Typography variant="caption" color="text.secondary" display="block">
                                        {formatPropertyName(key)}
                                    </Typography>
                                    <Typography variant="body2" sx={{ fontWeight: 500 }}>
                                        {formatPropertyValue(String(value))}
                                    </Typography>
                                </Grid>
                            ))}
                        </Grid>

                        {relevantProperties.length > 3 && (
                            <Typography
                                variant="caption"
                                color="primary"
                                sx={{ display: 'block', mt: 1, cursor: 'pointer' }}
                                onClick={handleExpandClick}
                            >
                                +{relevantProperties.length - 3} more properties
                            </Typography>
                        )}
                    </Box>
                )}

                {/* Expanded Properties and Sources */}
                <Collapse in={expanded} timeout="auto" unmountOnExit>
                    {/* Properties Section */}
                    {relevantProperties.length > 0 && (
                        <>
                            <Divider sx={{ my: 2 }} />
                            <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 600 }}>
                                Properties
                            </Typography>
                            <Grid container spacing={1}>
                                {relevantProperties.map(([key, value]) => (
                                    <Grid xs={12} sm={6} key={key}>
                                        <Box sx={{ mb: 1 }}>
                                            <Typography variant="caption" color="text.secondary" display="block">
                                                {formatPropertyName(key)}
                                            </Typography>
                                            <Typography variant="body2" sx={{ fontWeight: 500, wordBreak: 'break-word' }}>
                                                {String(value)}
                                            </Typography>
                                        </Box>
                                    </Grid>
                                ))}
                            </Grid>
                        </>
                    )}

                    {/* Sources Information - UPDATED */}
                    {(entityDocument || (entity.sources && entity.sources.length > 0)) && (
                        <>
                            <Divider sx={{ my: 2 }} />
                            <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 600 }}>
                                Sources
                            </Typography>

                            {/* Show document from selector */}
                            {entityDocument && (
                                <Box sx={{ mb: 1, p: 1, bgcolor: 'action.hover', borderRadius: 1 }}>
                                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                        <DocumentIcon fontSize="small" color="primary" />
                                        <Typography variant="body2" fontWeight="medium">
                                            {getDocumentDisplayName(entityDocument)}
                                        </Typography>
                                    </Box>
                                    <Typography variant="caption" color="text.secondary" sx={{ ml: 3 }}>
                                        Type: {entityDocument.artifact_type || 'base_case'}, 
                                        Size: {entityDocument.fileSize ? `${Math.round(entityDocument.fileSize / 1024)} KB` : 'Unknown'} •
                                    </Typography>
                                    {entityDocument.created_at && (
                                        <Typography variant="caption" color="text.secondary" display="block" sx={{ ml: 3 }}>
                                            Uploaded: {new Date(entityDocument.created_at).toLocaleDateString()}
                                        </Typography>
                                    )}
                                </Box>
                            )}

                            {/* Show legacy sources if they exist */}
                            {/* {entity.sources && entity.sources.map((source, index) => (
                                <Box key={index} sx={{ mb: 1, p: 1, bgcolor: 'action.hover', borderRadius: 1 }}>
                                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                        <SourceIcon fontSize="small" color="secondary" />
                                        <Typography variant="body2" color="text.secondary">
                                            {source.type || 'Document'}: {source.reference || 'Unknown'}
                                        </Typography>
                                    </Box>
                                </Box>
                            ))} */}
                        </>
                    )}

                    {/* Metadata Section */}
                    <Divider sx={{ my: 2 }} />
                    <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 600 }}>
                        Metadata
                    </Typography>
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                        {entity.doc_id && (
                            <Chip
                                label={`Doc ID: ${entity.doc_id.substring(0, 8)}...`}
                                size="small"
                                variant="outlined"
                                color="default"
                            />
                        )}
                        {entity.properties?.extracted_from && (
                            <Chip
                                label={`Extracted from: ${entity.properties.extracted_from}`}
                                size="small"
                                variant="outlined"
                                color="default"
                            />
                        )}
                        {entity.properties?.artifact_type && (
                            <Chip
                                label={`Artifact: ${entity.properties.artifact_type}`}
                                size="small"
                                variant="outlined"
                                color="default"
                            />
                        )}
                        {confidence && (
                            <Chip
                                label={`Confidence: ${Math.round(parseFloat(confidence) * 100)}%`}
                                size="small"
                                variant="outlined"
                                color={parseFloat(confidence) > 0.8 ? 'success' : 'warning'}
                            />
                        )}
                    </Box>
                </Collapse>
            </CardContent>
        </Card>
    );
};

export default EntityDetails;