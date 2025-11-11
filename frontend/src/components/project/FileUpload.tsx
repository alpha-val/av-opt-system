import React, { useState, useCallback, useRef, useEffect } from "react";
import {
  Box,
  Button,
  Typography,
  Paper,
  LinearProgress,
  Alert,
  IconButton,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
} from "@mui/material";
import {
  CloudUpload as UploadIcon,
  Delete as DeleteIcon,
  InsertDriveFile as FileIcon,
  PictureAsPdf as PdfIcon,
  TableChart as XlsIcon,
  Description as CsvIcon,
} from "@mui/icons-material";

// File type configurations
const FILE_TYPE_CONFIG = {
  PDF: {
    mimeTypes: ["application/pdf"],
    extensions: [".pdf"],
    icon: <PdfIcon />,
    color: "#d32f2f",
  },
  XLS: {
    mimeTypes: [
      "application/vnd.ms-excel",
      "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ],
    extensions: [".xls", ".xlsx"],
    icon: <XlsIcon />,
    color: "#2e7d32",
  },
  CSV: {
    mimeTypes: ["text/csv", "application/csv"],
    extensions: [".csv"],
    icon: <CsvIcon />,
    color: "#1976d2",
  },
};

export interface FileUploadProps {
  title?: string;
  description?: string;
  supportedTypes?: string[];
  multiple?: boolean;
  maxFiles?: number;
  maxSizeInMB?: number;
  onFilesSelected?: (files: File[]) => void;
  onFilesRejected?: (files: Array<{ file: File; reason: string }>) => void;
  disabled?: boolean;
  showProgress?: boolean;
  progress?: number;
  showSelectedFiles?: boolean;
  showRejectedFiles?: boolean;
  clearTrigger?: any;
}

interface SelectedFile {
  id: string;
  file: File;
  name: string;
  size: number;
  type: string;
  sizeFormatted: string;
}

/**
 * File upload widget with drag-and-drop support.
 * 
 * Supports PDF, Excel, and CSV files with validation.
 */
const FileUpload: React.FC<FileUploadProps> = ({
  title = "Upload Files",
  description = "Drag and drop files here or click to browse",
  supportedTypes = ["PDF"],
  multiple = true,
  maxFiles = 10,
  maxSizeInMB = 50,
  onFilesSelected,
  onFilesRejected,
  disabled = false,
  showProgress = false,
  progress = 0,
  showSelectedFiles = true,
  showRejectedFiles = true,
  clearTrigger = null,
}) => {
  const [dragActive, setDragActive] = useState(false);
  const [selectedFiles, setSelectedFiles] = useState<SelectedFile[]>([]);
  const [rejectedFiles, setRejectedFiles] = useState<Array<{ file: File; reason: string }>>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const prevClearTriggerRef = useRef(clearTrigger);

  // Get all allowed mime types and extensions
  const getAllowedMimeTypes = useCallback(() => {
    return supportedTypes.flatMap(
      (type) => FILE_TYPE_CONFIG[type as keyof typeof FILE_TYPE_CONFIG]?.mimeTypes || []
    );
  }, [supportedTypes]);

  const getAllowedExtensions = useCallback(() => {
    return supportedTypes.flatMap(
      (type) => FILE_TYPE_CONFIG[type as keyof typeof FILE_TYPE_CONFIG]?.extensions || []
    );
  }, [supportedTypes]);

  // Validate file type
  const isFileTypeValid = useCallback(
    (file: File) => {
      const allowedMimeTypes = getAllowedMimeTypes();
      const allowedExtensions = getAllowedExtensions();

      // Check mime type
      if (allowedMimeTypes.includes(file.type)) {
        return true;
      }

      // Check file extension as fallback
      const fileName = file.name.toLowerCase();
      return allowedExtensions.some((ext) =>
        fileName.endsWith(ext.toLowerCase())
      );
    },
    [getAllowedMimeTypes, getAllowedExtensions]
  );

  // Validate file size
  const isFileSizeValid = useCallback(
    (file: File) => {
      const maxSizeInBytes = maxSizeInMB * 1024 * 1024;
      return file.size <= maxSizeInBytes;
    },
    [maxSizeInMB]
  );

  // Get file type from file
  const getFileType = useCallback(
    (file: File) => {
      for (const [type, config] of Object.entries(FILE_TYPE_CONFIG)) {
        if (supportedTypes.includes(type)) {
          const isValidMime = config.mimeTypes.includes(file.type);
          const isValidExt = config.extensions.some((ext) =>
            file.name.toLowerCase().endsWith(ext.toLowerCase())
          );
          if (isValidMime || isValidExt) {
            return type;
          }
        }
      }
      return "UNKNOWN";
    },
    [supportedTypes]
  );

  // Format file size
  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return "0 Bytes";
    const k = 1024;
    const sizes = ["Bytes", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
  };

  // Process files
  const processFiles = useCallback(
    (files: FileList | File[]) => {
      const fileArray = Array.from(files);
      const validFiles: SelectedFile[] = [];
      const invalidFiles: Array<{ file: File; reason: string }> = [];

      fileArray.forEach((file) => {
        const isTypeValid = isFileTypeValid(file);
        const isSizeValid = isFileSizeValid(file);

        if (isTypeValid && isSizeValid) {
          validFiles.push({
            id: `${file.name}-${file.size}-${Date.now()}-${Math.random()}`,
            file,
            name: file.name,
            size: file.size,
            type: getFileType(file),
            sizeFormatted: formatFileSize(file.size),
          });
        } else {
          let reason = "";
          if (!isTypeValid) {
            reason = `File type not supported. Allowed: ${supportedTypes.join(", ")}`;
          } else if (!isSizeValid) {
            reason = `File size exceeds ${maxSizeInMB}MB limit`;
          }

          invalidFiles.push({
            file,
            reason,
          });
        }
      });

      // Check max files limit
      const totalFiles = selectedFiles.length + validFiles.length;
      if (totalFiles > maxFiles) {
        const excessFiles = totalFiles - maxFiles;
        const filesToAdd = validFiles.slice(0, validFiles.length - excessFiles);
        const excessFilesArray = validFiles.slice(-excessFiles);

        excessFilesArray.forEach((fileObj) => {
          invalidFiles.push({
            file: fileObj.file,
            reason: `Maximum ${maxFiles} files allowed`,
          });
        });

        setSelectedFiles((prev) => [...prev, ...filesToAdd]);
        if (onFilesSelected && filesToAdd.length > 0) {
          onFilesSelected(filesToAdd.map((f) => f.file));
        }
      } else {
        setSelectedFiles((prev) => [...prev, ...validFiles]);
        if (onFilesSelected && validFiles.length > 0) {
          onFilesSelected(validFiles.map((f) => f.file));
        }
      }

      if (invalidFiles.length > 0) {
        setRejectedFiles((prev) => [...prev, ...invalidFiles]);
        if (onFilesRejected) {
          onFilesRejected(invalidFiles);
        }
      }
    },
    [
      selectedFiles,
      supportedTypes,
      maxFiles,
      isFileTypeValid,
      isFileSizeValid,
      getFileType,
      onFilesSelected,
      onFilesRejected,
    ]
  );

  // Drag and drop handlers
  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      setDragActive(false);

      if (disabled) return;

      if (e.dataTransfer.files && e.dataTransfer.files[0]) {
        processFiles(e.dataTransfer.files);
      }
    },
    [processFiles, disabled]
  );

  // File input change handler
  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      processFiles(e.target.files);
      // Reset input to allow selecting the same file again
      if (e.target) {
        e.target.value = "";
      }
    }
  };

  // Remove file
  const removeFile = (fileId: string) => {
    setSelectedFiles((prev) => prev.filter((f) => f.id !== fileId));
  };

  // Clear rejected files
  const clearRejectedFiles = () => {
    setRejectedFiles([]);
  };

  // Clear selected files when clearTrigger changes
  useEffect(() => {
    if (clearTrigger !== null && clearTrigger !== prevClearTriggerRef.current) {
      setSelectedFiles([]);
      setRejectedFiles([]);
      prevClearTriggerRef.current = clearTrigger;
    }
  }, [clearTrigger]);

  // Get file icon
  const getFileIcon = (type: string) => {
    return FILE_TYPE_CONFIG[type as keyof typeof FILE_TYPE_CONFIG]?.icon || <FileIcon />;
  };

  // Get file color
  const getFileColor = (type: string) => {
    return FILE_TYPE_CONFIG[type as keyof typeof FILE_TYPE_CONFIG]?.color || "#666";
  };

  return (
    <Box>
      {/* Upload Area */}
      <Paper
        sx={{
          p: 2,
          textAlign: "center",
          backgroundColor: dragActive ? "action.hover" : "background.paper",
          cursor: disabled ? "not-allowed" : "pointer",
          opacity: disabled ? 0.6 : 1,
          transition: "all 0.2s ease-in-out",
          border: "2px dashed",
          borderColor: dragActive ? "primary.main" : "divider",
          "&:hover": {
            borderColor: disabled ? "divider" : "primary.main",
          },
        }}
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
          accept={getAllowedMimeTypes().join(",")}
          onChange={handleFileInputChange}
          style={{ display: "none" }}
          disabled={disabled}
        />
        {/* Icon and Title */}
        <Box
          sx={{
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            gap: 1.5,
            mb: 2,
          }}
        >
          <UploadIcon
            sx={{
              fontSize: 48,
              color: dragActive ? "primary.main" : "text.secondary",
            }}
          />
          <Typography variant="h6">{title}</Typography>
        </Box>

        {/* Description */}
        <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
          {description}
        </Typography>

        {/* File limits info */}
        <Typography
          variant="caption"
          color="text.secondary"
          sx={{ mb: 2, display: "block" }}
        >
          Max file size: {maxSizeInMB}MB
          {multiple && ` • Max files: ${maxFiles}`}
        </Typography>

        {/* Browse button */}
        <Box sx={{ mt: 2, display: "flex", justifyContent: "center" }}>
          <Button
            variant="outlined"
            size="medium"
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
          <Typography
            variant="caption"
            color="text.secondary"
            sx={{ mt: 0.5, display: "block" }}
          >
            {progress}% uploaded
          </Typography>
        </Box>
      )}

      {/* Selected Files */}
      {showSelectedFiles && selectedFiles.length > 0 && (
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
      {showRejectedFiles && rejectedFiles.length > 0 && (
        <Box sx={{ mt: 2 }}>
          <Alert severity="error" onClose={clearRejectedFiles} sx={{ mb: 1 }}>
            <Typography variant="subtitle2" gutterBottom>
              {rejectedFiles.length} file(s) rejected:
            </Typography>
            {rejectedFiles.map((fileObj, index) => (
              <Typography key={index} variant="caption" display="block">
                • {fileObj.file.name}: {fileObj.reason}
              </Typography>
            ))}
          </Alert>
        </Box>
      )}
    </Box>
  );
};

export default FileUpload;

