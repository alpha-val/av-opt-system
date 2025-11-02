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

const DataTable = ({
    headers = [],
    data = [],
    sx = {},
    containerSx = {},
    renderCell = null,
    onRowClick = null,
    hover = true
}) => {
    // Default cell renderer
    const defaultRenderCell = (value, key, row, rowIndex) => {
        if (React.isValidElement(value)) {
            return value;
        }

        if (Array.isArray(value)) {
            return (
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
                    {value.map((item, idx) => (
                        <Typography key={idx} variant="body2">
                            {item}
                        </Typography>
                    ))}
                </Box>
            );
        }

        return (
            <Typography variant="body2">
                {value}
            </Typography>
        );
    };

    const cellRenderer = renderCell || defaultRenderCell;

    // Handle row click - avoid triggering when clicking buttons/interactive elements
    const handleRowClick = (event, row, rowIndex) => {
        // Don't trigger row click if user clicked on a button or other interactive element
        if (event.target.closest('button') || event.target.closest('[role="button"]')) {
            return;
        }

        if (onRowClick) {
            onRowClick(row, rowIndex);
        }
    };

    return (
        <TableContainer
            component={Paper}
            sx={{ borderRadius: 2, ...containerSx }}
        >
            <Table sx={sx}>
                <TableHead>
                    <TableRow>
                        {headers.map((header, index) => (
                            <TableCell key={index}>
                                <Typography variant="body1" fontWeight="bold">
                                    {header.display_value}
                                </Typography>
                            </TableCell>
                        ))}
                    </TableRow>
                </TableHead>
                <TableBody>
                    {data.map((row, rowIndex) => (
                        <TableRow
                            key={rowIndex}
                            hover={hover}
                            onClick={(event) => handleRowClick(event, row, rowIndex)}
                            sx={{
                                cursor: onRowClick ? 'pointer' : 'default',
                                '&:hover': onRowClick ? {
                                    backgroundColor: 'action.hover',
                                } : {}
                            }}
                        >
                            {headers.map((header, cellIndex) => {
                                const value = row[header.key] || '';

                                return (
                                    <TableCell key={cellIndex}>
                                        {cellRenderer(value, header.key, row, rowIndex)}
                                    </TableCell>
                                );
                            })}
                        </TableRow>
                    ))}
                </TableBody>
            </Table>
        </TableContainer>
    );
};

export default DataTable;