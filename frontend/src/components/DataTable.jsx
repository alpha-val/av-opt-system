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
                            onClick={onRowClick ? () => onRowClick(row, rowIndex) : undefined}
                            sx={{ cursor: onRowClick ? 'pointer' : 'default' }}
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