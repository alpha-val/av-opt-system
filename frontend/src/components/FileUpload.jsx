import React, { useState, useCallback, useRef } from 'react';
import {
    Box,
    Button,
    Typography,
    Paper,
    LinearProgress,
    Alert,
    Chip,
    IconButton,
    List,
    ListItem,
    ListItemText,
    ListItemSecondaryAction,
} from '@mui/material';
import {
    CloudUpload as UploadIcon,
    Delete as DeleteIcon,
    InsertDriveFile as FileIcon,
    PictureAsPdf as PdfIcon,
    TableChart as XlsIcon,
    Description as CsvIcon,
} from '@mui/icons-material';

const FileUpload = ({
    title = "Upload Files",
    description = "Drag and drop files here or click to browse",
    supportedTypes = ["PDF", "XLS", "CSV"],
    multiple = true,
    maxFiles = 10,
    maxSizeInMB = 50,
    onFilesSelected = null,
    onFilesRejected = null,
    icon = null,
    iconColor = '#000',
    numberOfFiles = 0,
    disabled = false,
    showProgress = false,
    progress = 0,
    sx = {}
}) => {
    const [dragActive, setDragActive] = useState(false);
    const [selectedFiles, setSelectedFiles] = useState([]);
    const [rejectedFiles, setRejectedFiles] = useState([]);
    const fileInputRef = useRef(null);

    // File type mappings
    const fileTypeConfig = {
        PDF: {
            mimeTypes: ['application/pdf'],
            extensions: ['.pdf'],
            icon: <PdfIcon />,
            color: '#d32f2f'
        },
        XLS: {
            mimeTypes: [
                'application/vnd.ms-excel',
                'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            ],
            extensions: ['.xls', '.xlsx'],
            icon: <XlsIcon />,
            color: '#2e7d32'
        },
        CSV: {
            mimeTypes: ['text/csv', 'application/csv'],
            extensions: ['.csv'],
            icon: <CsvIcon />,
            color: '#1976d2'
        }
    };

    // Get all allowed mime types and extensions
    const getAllowedMimeTypes = () => {
        return supportedTypes.flatMap(type => fileTypeConfig[type]?.mimeTypes || []);
    };

    const getAllowedExtensions = () => {
        return supportedTypes.flatMap(type => fileTypeConfig[type]?.extensions || []);
    };

    // Validate file type
    const isFileTypeValid = (file) => {
        const allowedMimeTypes = getAllowedMimeTypes();
        const allowedExtensions = getAllowedExtensions();

        // Check mime type
        if (allowedMimeTypes.includes(file.type)) {
            return true;
        }

        // Check file extension as fallback
        const fileName = file.name.toLowerCase();
        return allowedExtensions.some(ext => fileName.endsWith(ext.toLowerCase()));
    };

    // Validate file size
    const isFileSizeValid = (file) => {
        const maxSizeInBytes = maxSizeInMB * 1024 * 1024;
        return file.size <= maxSizeInBytes;
    };

    // Get file type from file
    const getFileType = (file) => {
        for (const [type, config] of Object.entries(fileTypeConfig)) {
            if (supportedTypes.includes(type)) {
                const isValidMime = config.mimeTypes.includes(file.type);
                const isValidExt = config.extensions.some(ext =>
                    file.name.toLowerCase().endsWith(ext.toLowerCase())
                );
                if (isValidMime || isValidExt) {
                    return type;
                }
            }
        }
        return 'UNKNOWN';
    };

    // Process files
    const processFiles = useCallback((files) => {
        const fileArray = Array.from(files);
        const validFiles = [];
        const invalidFiles = [];

        fileArray.forEach(file => {
            const isTypeValid = isFileTypeValid(file);
            const isSizeValid = isFileSizeValid(file);

            if (isTypeValid && isSizeValid) {
                validFiles.push({
                    file,
                    id: `${file.name}-${file.size}-${Date.now()}`,
                    name: file.name,
                    size: file.size,
                    type: getFileType(file),
                    sizeFormatted: formatFileSize(file.size)
                });
            } else {
                let reason = '';
                if (!isTypeValid) {
                    reason = `File type not supported. Allowed: ${supportedTypes.join(', ')}`;
                } else if (!isSizeValid) {
                    reason = `File size exceeds ${maxSizeInMB}MB limit`;
                }

                invalidFiles.push({
                    file,
                    name: file.name,
                    reason,
                    type: getFileType(file)
                });
            }
        });

        // Check max files limit
        const totalFiles = selectedFiles.length + validFiles.length;
        if (totalFiles > maxFiles) {
            const excessFiles = totalFiles - maxFiles;
            const filesToAdd = validFiles.slice(0, validFiles.length - excessFiles);
            const excessFilesArray = validFiles.slice(-excessFiles);

            excessFilesArray.forEach(fileObj => {
                invalidFiles.push({
                    ...fileObj,
                    reason: `Maximum ${maxFiles} files allowed`
                });
            });

            setSelectedFiles(prev => [...prev, ...filesToAdd]);
        } else {
            setSelectedFiles(prev => [...prev, ...validFiles]);
        }

        if (invalidFiles.length > 0) {
            setRejectedFiles(prev => [...prev, ...invalidFiles]);
            if (onFilesRejected) {
                onFilesRejected(invalidFiles);
            }
        }

        if (validFiles.length > 0 && onFilesSelected) {
            const finalValidFiles = totalFiles > maxFiles ?
                validFiles.slice(0, validFiles.length - (totalFiles - maxFiles)) :
                validFiles;
            onFilesSelected(finalValidFiles);
        }
    }, [selectedFiles, supportedTypes, maxFiles, maxSizeInMB, onFilesSelected, onFilesRejected]);

    // Format file size
    const formatFileSize = (bytes) => {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    };

    // Drag and drop handlers
    const handleDrag = useCallback((e) => {
        e.preventDefault();
        e.stopPropagation();
        if (e.type === "dragenter" || e.type === "dragover") {
            setDragActive(true);
        } else if (e.type === "dragleave") {
            setDragActive(false);
        }
    }, []);

    const handleDrop = useCallback((e) => {
        e.preventDefault();
        e.stopPropagation();
        setDragActive(false);

        if (disabled) return;

        if (e.dataTransfer.files && e.dataTransfer.files[0]) {
            processFiles(e.dataTransfer.files);
        }
    }, [processFiles, disabled]);

    // File input change handler
    const handleFileInputChange = (e) => {
        if (e.target.files && e.target.files[0]) {
            processFiles(e.target.files);
        }
    };

    // Remove file
    const removeFile = (fileId) => {
        setSelectedFiles(prev => prev.filter(f => f.id !== fileId));
    };

    // Clear rejected files
    const clearRejectedFiles = () => {
        setRejectedFiles([]);
    };

    // Get file icon
    const getFileIcon = (type) => {
        return fileTypeConfig[type]?.icon || <FileIcon />;
    };

    // Get file color
    const getFileColor = (type) => {
        return fileTypeConfig[type]?.color || '#666';
    };

    return (
        <Box sx={{ width: '100%', maxWidth: 600, ...sx }}>
            {/* Upload Area */}
            <Paper
                sx={{
                    p: 2,
                    textAlign: 'center',
                    border: '2px dashed',
                    borderColor: dragActive ? 'primary.main' : 'divider',
                    backgroundColor: dragActive ? 'action.hover' : 'background.paper',
                    cursor: disabled ? 'not-allowed' : 'pointer',
                    opacity: disabled ? 0.6 : 1,
                    transition: 'all 0.2s ease-in-out',
                    '&:hover': {
                        borderColor: disabled ? 'divider' : 'primary.main',
                        backgroundColor: disabled ? 'background.paper' : 'action.hover',
                    }
                }}
                elevation={0}
                onClick={() => !disabled && fileInputRef.current?.click()}
                onDragEnter={handleDrag}
                onDragLeave={handleDrag}
                onDragOver={handleDrag}
                onDrop={handleDrop}
            >
                <input
                    ref={fileInputRef}
                    type="file"
                    multiple={multiple}
                    accept={getAllowedMimeTypes().join(',')}
                    onChange={handleFileInputChange}
                    style={{ display: 'none' }}
                    disabled={disabled}
                />

                {/* <UploadIcon sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} /> */}

                <Typography variant="h6" gutterBottom>
                    {icon && <Box component="span" sx={{ color: iconColor, mr: 1 }}>{icon}</Box>} {title} {numberOfFiles > 0 && `(${numberOfFiles})`}
                </Typography>

                <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                    {description}
                </Typography>

                <Box sx={{ display: 'flex', justifyContent: 'center', gap: 1, mb: 2 }}>
                    {supportedTypes.map(type => (
                        <Chip
                            key={type}
                            label={type}
                            size="small"
                            variant="outlined"
                            sx={{ color: getFileColor(type), borderColor: getFileColor(type) }}
                        />
                    ))}
                </Box>

                <Typography variant="caption" color="text.secondary">
                    Max file size: {maxSizeInMB}MB • Max files: {maxFiles}
                </Typography>

                <Box sx={{ mt: 2 }}>
                    <Button
                        variant="outlined"
                        size='small'
                        startIcon={<UploadIcon />}
                        disabled={disabled}
                        onClick={(e) => {
                            e.stopPropagation();
                            fileInputRef.current?.click();
                        }}
                    >
                        Browse Files
                    </Button>
                </Box>
            </Paper>

            {/* Upload Progress */}
            {showProgress && (
                <Box sx={{ mt: 2 }}>
                    <LinearProgress
                        variant="determinate"
                        value={progress}
                        sx={{ height: 8, borderRadius: 4 }}
                    />
                    <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: 'block' }}>
                        {progress}% uploaded
                    </Typography>
                </Box>
            )}

            {/* Selected Files */}
            {selectedFiles.length > 0 && (
                <Box sx={{ mt: 3 }}>
                    <Typography variant="subtitle2" gutterBottom>
                        Selected Files ({selectedFiles.length})
                    </Typography>
                    <List dense>
                        {selectedFiles.map((fileObj) => (
                            <ListItem key={fileObj.id} sx={{ px: 0 }}>
                                <Box sx={{ mr: 2, color: getFileColor(fileObj.type) }}>
                                    {getFileIcon(fileObj.type)}
                                </Box>
                                <ListItemText
                                    primary={fileObj.name}
                                    secondary={`${fileObj.sizeFormatted} • ${fileObj.type}`}
                                />
                                <ListItemSecondaryAction>
                                    <IconButton
                                        edge="end"
                                        size="small"
                                        onClick={() => removeFile(fileObj.id)}
                                        disabled={disabled}
                                    >
                                        <DeleteIcon />
                                    </IconButton>
                                </ListItemSecondaryAction>
                            </ListItem>
                        ))}
                    </List>
                </Box>
            )}

            {/* Rejected Files */}
            {rejectedFiles.length > 0 && (
                <Box sx={{ mt: 2 }}>
                    <Alert
                        severity="error"
                        onClose={clearRejectedFiles}
                        sx={{ mb: 1 }}
                    >
                        <Typography variant="subtitle2" gutterBottom>
                            {rejectedFiles.length} file(s) rejected:
                        </Typography>
                        {rejectedFiles.map((fileObj, index) => (
                            <Typography key={index} variant="caption" display="block">
                                • {fileObj.name}: {fileObj.reason}
                            </Typography>
                        ))}
                    </Alert>
                </Box>
            )}
        </Box>
    );
};

export default FileUpload;