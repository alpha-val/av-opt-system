import React from 'react';
import {
    Table,
    TableBody,
    TableCell,
    TableContainer,
    TableHead,
    TableRow,
    Paper,
    Typography,
    Box,
} from '@mui/material';
import EntityDetailsRow from './EntityDetailsRow';

const EntityDetailsTable = ({ entities = [], title = "Entities" }) => {
    return (
        <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
                {title} ({entities.length})
            </Typography>

            {entities.length > 0 ? (
                <TableContainer sx={{ maxHeight: 600 }}>
                    <Table stickyHeader size="small">
                        <TableHead>
                            <TableRow>
                                <TableCell sx={{ fontWeight: 'bold', minWidth: 200 }}>Name</TableCell>
                                <TableCell sx={{ fontWeight: 'bold', minWidth: 100 }}>Type</TableCell>
                                <TableCell sx={{ fontWeight: 'bold', minWidth: 120 }}>Cost</TableCell>
                                <TableCell sx={{ fontWeight: 'bold', minWidth: 140 }}>Amount/Quantity</TableCell>
                                <TableCell sx={{ fontWeight: 'bold', minWidth: 300, maxWidth: 300 }}>Other Properties</TableCell>
                                <TableCell sx={{ fontWeight: 'bold', minWidth: 180 }}>Sources</TableCell>
                                <TableCell sx={{ fontWeight: 'bold', minWidth: 100 }} align="center">Confidence</TableCell>
                            </TableRow>
                        </TableHead>
                        <TableBody>
                            {entities.map((entity, index) => (
                                <EntityDetailsRow
                                    key={entity.entity_id || `entity-${index}`}
                                    entity={entity}
                                    index={index}
                                />
                            ))}
                        </TableBody>
                    </Table>
                </TableContainer>
            ) : (
                <Box sx={{ textAlign: 'center', py: 4 }}>
                    <Typography variant="body2" color="text.secondary">
                        No entities found
                    </Typography>
                </Box>
            )}
        </Paper>
    );
};

export default EntityDetailsTable;