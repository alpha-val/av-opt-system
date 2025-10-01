import React, { useState, useEffect, useMemo } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useParams } from 'react-router-dom';
import {
    Box,
    Typography,
    Grid,
    Paper,
    Table,
    TableBody,
    TableCell,
    TableContainer,
    TableHead,
    TableRow,
    Button,
    IconButton,
    Chip,
    LinearProgress,
    Alert,
    Snackbar,
} from '@mui/material';
import {
    PictureAsPdf as PdfIcon,
    TableChart as XlsIcon,
    Description as CsvIcon,
    Delete as DeleteIcon,
    CloudUpload as UploadIcon,
} from '@mui/icons-material';

import FileUpload from '../../components/FileUpload';
import {
    fetchProjectDocuments,
    uploadProjectDescription,
    uploadStructuredData,
    deleteProjectDocument,
    setCurrentProject,
    clearError,
    selectAllDocuments,
    selectBaseCaseDocuments,
    selectTabularDataDocuments,
    selectBaseCaseCount,
    selectTabularDataCount,
    selectTotalDocumentCount,
    selectDataLoading,
    selectDataError,
    selectDataProgress,
} from '../../redux/dataSlice';

const Sources = () => {
    const { projectId } = useParams();
    const dispatch = useDispatch();

    // Use memoized selectors
    const allDocuments = useSelector(selectAllDocuments);
    const baseCaseDocuments = useSelector(selectBaseCaseDocuments);
    const scenarioDocuments = useSelector(selectTabularDataDocuments);
    const baseCaseCount = useSelector(selectBaseCaseCount);
    const scenarioCount = useSelector(selectTabularDataCount);
    const totalCount = useSelector(selectTotalDocumentCount);
    const loading = useSelector(selectDataLoading);
    const error = useSelector(selectDataError);
    const progress = useSelector(selectDataProgress);

    // Local state
    const [toast, setToast] = useState({ open: false, message: '', severity: 'success' });

    // Load project documents on mount
    useEffect(() => {
        if (projectId && !loading.fetchDocuments) {
            dispatch(setCurrentProject(projectId));
            dispatch(fetchProjectDocuments({ projectId }));
        }
    }, [dispatch, projectId]);

    // Handle base case upload
    const handleBaseCaseUpload = async (files) => {
        for (const fileObj of files) {
            try {
                await dispatch(uploadProjectDescription({
                    projectId,
                    file: fileObj.file,
                    metadata: {
                        description: `Base case document: ${fileObj.name}`,
                    }
                })).unwrap();

                setToast({
                    open: true,
                    message: `${fileObj.name} uploaded successfully`,
                    severity: 'success'
                });

            } catch (error) {
                setToast({
                    open: true,
                    message: `Upload failed: ${error}`,
                    severity: 'error'
                });
            }
        }
        // Refresh documents
        dispatch(fetchProjectDocuments({ projectId }));
    };

    // Handle scenario data upload  
    const handleTabularDataUpload = async (files) => {
        for (const fileObj of files) {
            try {
                await dispatch(uploadStructuredData({
                    projectId,
                    file: fileObj.file,
                    metadata: {
                        description: `Tabular data: ${fileObj.name}`,
                    }
                })).unwrap();

                setToast({
                    open: true,
                    message: `${fileObj.name} uploaded successfully`,
                    severity: 'success'
                });
            } catch (error) {
                setToast({
                    open: true,
                    message: `Upload failed: ${error}`,
                    severity: 'error'
                });
            }
        }
        // Refresh documents
        dispatch(fetchProjectDocuments({ projectId }));
    };

    // Handle delete
    const handleDeleteFile = async (docId, fileName) => {
        if (window.confirm(`Are you sure you want to delete "${fileName}"?`)) {
            try {
                await dispatch(deleteProjectDocument({ projectId, docId })).unwrap();
                setToast({
                    open: true,
                    message: `${fileName} deleted successfully`,
                    severity: 'success'
                });
            } catch (error) {
                setToast({
                    open: true,
                    message: `Delete failed: ${error}`,
                    severity: 'error'
                });
            }
        }
    };

    // Get file icon based on type
    const getFileIcon = (fileType, fileName) => {
        const name = fileName?.toLowerCase() || '';
        const type = fileType?.toLowerCase() || '';

        if (type.includes('pdf') || name.endsWith('.pdf')) {
            return <PdfIcon sx={{ color: '#d32f2f' }} />;
        } else if (type.includes('excel') || type.includes('spreadsheet') ||
            name.endsWith('.xlsx') || name.endsWith('.xls')) {
            return <XlsIcon sx={{ color: '#2e7d32' }} />;
        } else if (type.includes('csv') || name.endsWith('.csv')) {
            return <CsvIcon sx={{ color: '#1976d2' }} />;
        }
        return <CsvIcon sx={{ color: '#666' }} />;
    };

    // Format file size
    const formatFileSize = (bytes) => {
        if (!bytes) return 'N/A';
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    };

    // Get file type label
    const getFileTypeLabel = (fileName) => {
        const name = fileName?.toLowerCase() || '';
        if (name.endsWith('.pdf')) return 'PDF';
        if (name.endsWith('.xlsx') || name.endsWith('.xls')) return 'XLS';
        if (name.endsWith('.csv')) return 'CSV';
        return 'Unknown';
    };

    // Memoize derived data
    const memoizedBaseCaseDocuments = useMemo(
        () => allDocuments.filter(doc => doc.artifact_type === 'base_case'),
        [allDocuments]
    );

    const memoizedTabularDataDocuments = useMemo(
        () => allDocuments.filter(doc => doc.artifact_type === 'scenario'),
        [allDocuments]
    );

    const memoizedBaseCaseCount = useMemo(
        () => memoizedBaseCaseDocuments.length,
        [memoizedBaseCaseDocuments]
    );

    const memoizedTabularDataCount = useMemo(
        () => memoizedTabularDataDocuments.length,
        [memoizedTabularDataDocuments]
    );

    return (
        <Box>
            <Typography variant="h5" gutterBottom fontWeight="bold">
                Sources
            </Typography>
            <Typography variant="body1" color="text.secondary" sx={{ mb: 0 }}>
                Upload your mining reports, estimation documents, and data tables.
            </Typography>

            {/* Error Alert */}
            {error && (
                <Alert severity="error" sx={{ mb: 3 }} onClose={() => dispatch(clearError())}>
                    {error}
                </Alert>
            )}

            <Grid container spacing={3} sx={{ justifyContent: 'flex-start', flexDirection: 'column' }}>
                {/* Second Row - Full width table */}
                <Grid item xs={12} sx={{ mt: 2, width: '100%' }}>
                    <Paper sx={{ p: 3 }}>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                            <Typography variant="h6">
                                All Documents ({totalCount})
                            </Typography>
                            {/* <Button
                                startIcon={<UploadIcon />}
                                variant="outlined"
                                size="small"
                                onClick={() => {
                                    window.scrollTo({ top: 0, behavior: 'smooth' });
                                }}
                            >
                                Add More Files
                            </Button> */}
                        </Box>

                        {allDocuments.length === 0 ? (
                            <Box sx={{ textAlign: 'center', py: 4 }}>
                                <UploadIcon sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
                                <Typography variant="body2" color="text.secondary">
                                    No documents uploaded yet. Use the upload sections to add your project files.
                                </Typography>
                            </Box>
                        ) : (
                            <TableContainer sx={{ overflow: 'auto', width: '100%' }}>
                                <Table sx={{ minWidth: 650, width: '100%' }} stickyHeader>
                                    <TableHead>
                                        <TableRow>
                                            <TableCell>File Name</TableCell>
                                            <TableCell>Type</TableCell>
                                            <TableCell>Size</TableCell>
                                            <TableCell>Category</TableCell>
                                            <TableCell align="right">Actions</TableCell>
                                        </TableRow>
                                    </TableHead>
                                    <TableBody>
                                        {allDocuments.map((doc, index) => (
                                            <TableRow key={doc.doc_id || `doc-${index}`} hover>
                                                <TableCell>
                                                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                                        {getFileIcon(doc.fileType, doc.fileName)}
                                                        <Box>
                                                            <Typography variant="body2" fontWeight="medium">
                                                                {doc.fileName || doc.originalName || 'Unknown File'}
                                                            </Typography>
                                                        </Box>
                                                    </Box>
                                                </TableCell>
                                                <TableCell>
                                                    <Chip
                                                        label={getFileTypeLabel(doc.fileName)}
                                                        size="small"
                                                        variant="outlined"
                                                    />
                                                </TableCell>
                                                <TableCell>
                                                    {formatFileSize(doc.fileSize)}
                                                </TableCell>
                                                <TableCell>
                                                    <Chip
                                                        label={doc.artifact_type === 'base_case' ? 'Base Case' : 'Tabular Data'}
                                                        size="small"
                                                        color={doc.artifact_type === 'base_case' ? 'primary' : 'secondary'}
                                                    />
                                                </TableCell>
                                                <TableCell align="right">
                                                    <IconButton
                                                        size="small"
                                                        onClick={() => handleDeleteFile(doc.doc_id, doc.fileName)}
                                                        disabled={loading.deleteDocument}
                                                        sx={{ color: 'error.main' }}
                                                    >
                                                        <DeleteIcon />
                                                    </IconButton>
                                                </TableCell>
                                            </TableRow>
                                        ))}
                                    </TableBody>
                                </Table>
                            </TableContainer>
                        )}

                        {/* Global upload progress */}
                        {(loading.uploadBase || loading.uploadTabularData) && (
                            <Box sx={{ mt: 2 }}>
                                <LinearProgress />
                                <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                                    Uploading files and extracting data...
                                </Typography>
                            </Box>
                        )}
                    </Paper>
                </Grid>
                {/* First Row - Two columns for uploads */}
                <Box sx={{ maxWidth: 1200, mx: 'auto', mb: 1, justifyContent: 'flex-start' }}>
                    <Grid container spacing={3} sx={{ justifyContent: 'flex-start' }}>
                        <Grid item xs={12} md={6}>
                            <Paper sx={{ p: 2, height: 'fit-content', }}>
                                {/* <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                    <PdfIcon sx={{ color: '#d32f2f' }} />
                                    Base Case ({memoizedBaseCaseCount})
                                </Typography>
                                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                                    Upload PDF documents containing project descriptions, feasibility studies, and reports.
                                </Typography> */}

                                <FileUpload
                                    title="Upload Base Case Documents"
                                    description="Upload PDF Project descriptions, feasibility studies, and reports."
                                    supportedTypes={["PDF"]}
                                    multiple={true}
                                    maxFiles={10}
                                    maxSizeInMB={100}
                                    onFilesSelected={handleBaseCaseUpload}
                                    icon={<PdfIcon />}
                                    iconColor="#d32f2f"
                                    numberOfFiles={memoizedBaseCaseCount}
                                    disabled={loading.uploadBase}
                                    showProgress={loading.uploadBase}
                                    progress={loading.uploadBase ? progress.upload : 0}
                                />
                            </Paper>
                        </Grid>
                        <Grid item xs={12} md={6}>
                            <Paper sx={{ p: 2, height: 'fit-content', }}>
                                {/* <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                    <XlsIcon sx={{ color: '#2e7d32' }} />
                                    Tabular Data ({memoizedTabularDataCount})
                                </Typography>
                                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                                    Upload files containing structured tabular data for cost analysis and modeling.
                                </Typography> */}

                                <FileUpload
                                    title="Upload Tabular Data Files"
                                    description="Upload PDF, Excel, or CSV files with structured data."
                                    supportedTypes={["PDF", "XLS", "CSV"]}
                                    multiple={true}
                                    maxFiles={20}
                                    maxSizeInMB={200}
                                    onFilesSelected={handleTabularDataUpload}
                                    icon={<XlsIcon />}
                                    iconColor="#2e7d32"
                                    numberOfFiles={memoizedTabularDataCount}
                                    disabled={loading.uploadTabularData}
                                    showProgress={loading.uploadTabularData}
                                    progress={loading.uploadTabularData ? progress.upload : 0}
                                />
                            </Paper>
                        </Grid>
                    </Grid>
                </Box>
            </Grid >

            {/* Toast Notifications */}
            < Snackbar
                open={toast.open}
                autoHideDuration={4000}
                onClose={() => setToast(prev => ({ ...prev, open: false }))}
                anchorOrigin={{ vertical: 'top', horizontal: 'right' }}
            >
                <Alert
                    onClose={() => setToast(prev => ({ ...prev, open: false }))}
                    severity={toast.severity}
                    sx={{ width: '100%' }}
                >
                    {toast.message}
                </Alert>
            </Snackbar >
        </Box >
    );
};

export default Sources;