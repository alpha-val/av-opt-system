import React, { useState, useCallback, useRef, useEffect } from "react";
import PropTypes from "prop-types";
import {
  Box,
  Button,
  Typography,
  Paper,
  LinearProgress,
  Alert,
  Chip,
  Grid,
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
  Image as ImageIcon,
  VideoFile as VideoIcon,
  AudioFile as AudioIcon,
} from "@mui/icons-material";

// Default file type configurations
const DEFAULT_FILE_TYPES = {
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
  IMAGE: {
    mimeTypes: ["image/jpeg", "image/png", "image/gif", "image/webp"],
    extensions: [".jpg", ".jpeg", ".png", ".gif", ".webp"],
    icon: <ImageIcon />,
    color: "#ed6c02",
  },
  VIDEO: {
    mimeTypes: ["video/mp4", "video/quicktime", "video/x-msvideo"],
    extensions: [".mp4", ".mov", ".avi"],
    icon: <VideoIcon />,
    color: "#9c27b0",
  },
  AUDIO: {
    mimeTypes: ["audio/mpeg", "audio/wav", "audio/ogg"],
    extensions: [".mp3", ".wav", ".ogg"],
    icon: <AudioIcon />,
    color: "#0288d1",
  },
};

/**
 * Generic styled file upload widget with drag-and-drop support
 * @param {Object} props
 * @param {string} props.title - Title of the upload widget
 * @param {string} props.description - Description text
 * @param {Array<string>} props.supportedTypes - Array of file types (e.g., ["PDF", "XLS"])
 * @param {Object} props.customFileTypes - Custom file type configurations to extend defaults
 * @param {boolean} props.multiple - Allow multiple file selection
 * @param {number} props.maxFiles - Maximum number of files allowed
 * @param {number} props.maxSizeInMB - Maximum file size in MB
 * @param {Function} props.onFilesSelected - Callback when files are selected
 * @param {Function} props.onFilesRejected - Callback when files are rejected
 * @param {ReactNode} props.icon - Custom icon to display
 * @param {string} props.iconColor - Color for the custom icon
 * @param {number} props.numberOfFiles - Number of existing files (displayed in title)
 * @param {boolean} props.disabled - Disable the upload widget
 * @param {boolean} props.showProgress - Show upload progress
 * @param {number} props.progress - Upload progress percentage (0-100)
 * @param {boolean} props.showSelectedFiles - Show list of selected files
 * @param {boolean} props.showRejectedFiles - Show rejected files alert
 * @param {Object} props.sx - Custom styles for the container
 * @param {Object} props.paperSx - Custom styles for the upload area Paper
 * @param {string} props.variant - Visual variant: "outlined" | "elevated" | "contained"
 * @param {string} props.buttonVariant - Button variant: "outlined" | "contained" | "text"
 * @param {string} props.buttonText - Custom button text
 * @param {any} props.clearTrigger - Trigger value to clear selected files (clears when value changes)
 */
const FileUpload = ({
  title = "Upload Files",
  description = "Drag and drop files here or click to browse",
  supportedTypes = ["PDF"],
  customFileTypes = {},
  multiple = true,
  maxFiles = 10,
  maxSizeInMB = 50,
  onFilesSelected = null,
  onFilesRejected = null,
  icon = null,
  iconColor = "#1976d2",
  numberOfFiles = 0,
  disabled = false,
  showProgress = false,
  progress = 0,
  showSelectedFiles = true,
  showRejectedFiles = true,
  sx = {},
  paperSx = {},
  variant = "outlined",
  buttonVariant = "outlined",
  buttonText = "Browse Files",
  clearTrigger = null,
}) => {
  const [dragActive, setDragActive] = useState(false);
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [rejectedFiles, setRejectedFiles] = useState([]);
  const fileInputRef = useRef(null);
  const prevClearTriggerRef = useRef(clearTrigger);

  // Merge default and custom file types
  const fileTypeConfig = { ...DEFAULT_FILE_TYPES, ...customFileTypes };

  // Get all allowed mime types and extensions
  const getAllowedMimeTypes = useCallback(() => {
    return supportedTypes.flatMap(
      (type) => fileTypeConfig[type]?.mimeTypes || []
    );
  }, [supportedTypes, fileTypeConfig]);

  const getAllowedExtensions = useCallback(() => {
    return supportedTypes.flatMap(
      (type) => fileTypeConfig[type]?.extensions || []
    );
  }, [supportedTypes, fileTypeConfig]);

  // Validate file type
  const isFileTypeValid = useCallback(
    (file) => {
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
    (file) => {
      const maxSizeInBytes = maxSizeInMB * 1024 * 1024;
      return file.size <= maxSizeInBytes;
    },
    [maxSizeInMB]
  );

  // Get file type from file
  const getFileType = useCallback(
    (file) => {
      for (const [type, config] of Object.entries(fileTypeConfig)) {
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
    [supportedTypes, fileTypeConfig]
  );

  // Format file size
  const formatFileSize = (bytes) => {
    if (bytes === 0) return "0 Bytes";
    const k = 1024;
    const sizes = ["Bytes", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
  };

  // Process files
  const processFiles = useCallback(
    (files) => {
      const fileArray = Array.from(files);
      const validFiles = [];
      const invalidFiles = [];

      fileArray.forEach((file) => {
        const isTypeValid = isFileTypeValid(file);
        const isSizeValid = isFileSizeValid(file);

        if (isTypeValid && isSizeValid) {
          validFiles.push({
            file,
            id: `${file.name}-${file.size}-${Date.now()}-${Math.random()}`,
            name: file.name,
            size: file.size,
            type: getFileType(file),
            sizeFormatted: formatFileSize(file.size),
          });
        } else {
          let reason = "";
          if (!isTypeValid) {
            reason = `File type not supported. Allowed: ${supportedTypes.join(
              ", "
            )}`;
          } else if (!isSizeValid) {
            reason = `File size exceeds ${maxSizeInMB}MB limit`;
          }

          invalidFiles.push({
            file,
            name: file.name,
            reason,
            type: getFileType(file),
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
            ...fileObj,
            reason: `Maximum ${maxFiles} files allowed`,
          });
        });

        setSelectedFiles((prev) => [...prev, ...filesToAdd]);
        if (onFilesSelected && filesToAdd.length > 0) {
          onFilesSelected(filesToAdd);
        }
      } else {
        setSelectedFiles((prev) => [...prev, ...validFiles]);
        if (onFilesSelected && validFiles.length > 0) {
          onFilesSelected(validFiles);
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
  const handleDrag = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  }, []);

  const handleDrop = useCallback(
    (e) => {
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
  const handleFileInputChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      processFiles(e.target.files);
      // Reset input to allow selecting the same file again
      e.target.value = "";
    }
  };

  // Remove file
  const removeFile = (fileId) => {
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
  const getFileIcon = (type) => {
    return fileTypeConfig[type]?.icon || <FileIcon />;
  };

  // Get file color
  const getFileColor = (type) => {
    return fileTypeConfig[type]?.color || "#666";
  };

  // Get border style based on variant
  const getBorderStyle = () => {
    switch (variant) {
      case "contained":
        return {
          border: "none",
          backgroundColor: dragActive ? "action.selected" : "action.hover",
        };
      case "elevated":
        return {
          border: "none",
          elevation: dragActive ? 4 : 1,
        };
      case "outlined":
      default:
        return {
          border: "2px dashed",
          borderColor: dragActive ? "primary.main" : "divider",
        };
    }
  };

  return (
    <Box sx={sx}>
      {/* Upload Area */}
      <Paper
        sx={{
          p: 2,
          textAlign: "center",
          backgroundColor: dragActive
            ? "action.hover"
            : variant === "contained"
            ? "action.hover"
            : "background.paper",
          cursor: disabled ? "not-allowed" : "pointer",
          opacity: disabled ? 0.6 : 1,
          transition: "all 0.2s ease-in-out",
          width: "100%",
          "&:hover": {
            borderColor: disabled
              ? "divider"
              : variant === "outlined"
              ? "primary.main"
              : undefined,
            backgroundColor:
              disabled || variant === "outlined"
                ? "background.paper"
                : "action.selected",
          },
          ...getBorderStyle(),
          ...paperSx,
        }}
        elevation={variant === "elevated" ? (dragActive ? 4 : 1) : 0}
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
        {/* Icon and Title - same line, centered */}
        <Box
          sx={{
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            gap: 1.5,
            mb: 2,
          }}
        >
          {/* Custom or default icon */}
          {icon ? (
            <Box sx={{ color: iconColor, fontSize: 48, display: "flex", alignItems: "center" }}>
              {icon}
            </Box>
          ) : (
            <UploadIcon
              sx={{
                fontSize: 48,
                color: dragActive ? "primary.main" : "text.secondary",
              }}
            />
          )}

          {/* Title */}
          <Typography variant="h6">
            {title} {numberOfFiles > 0 && `(${numberOfFiles})`}
          </Typography>
        </Box>

        {/* Description */}
        <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
          {description}
        </Typography>

        {/* Supported file types chips */}
        {/* {supportedTypes.length > 0 && (
          <Box
            sx={{ display: "flex", justifyContent: "center", gap: 1, mb: 2 }}
          >
            {supportedTypes.map((type) => (
              <Chip
                key={type}
                label={type}
                size="small"
                variant="outlined"
                sx={{
                  color: getFileColor(type),
                  borderColor: getFileColor(type),
                }}
              />
            ))}
          </Box>
        )} */}

        {/* File limits info */}
        <Typography
          variant="caption"
          color="text.secondary"
          sx={{ mb: 2, display: "block" }}
        >
          Max file size: {maxSizeInMB}MB{" "}
          {multiple && `• Max files: ${maxFiles}`}
        </Typography>

        {/* Browse button */}
        <Box sx={{ mt: 2, display: "flex", justifyContent: "center" }}>
          <Button
            variant={buttonVariant}
            size="medium"
            startIcon={<UploadIcon />}
            disabled={disabled}
            onClick={(e) => {
              e.stopPropagation();
              fileInputRef.current?.click();
            }}
          >
            {buttonText}
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
                • {fileObj.name}: {fileObj.reason}
              </Typography>
            ))}
          </Alert>
        </Box>
      )}
    </Box>
  );
};

FileUpload.propTypes = {
  title: PropTypes.string,
  description: PropTypes.string,
  supportedTypes: PropTypes.arrayOf(PropTypes.string),
  customFileTypes: PropTypes.object,
  multiple: PropTypes.bool,
  maxFiles: PropTypes.number,
  maxSizeInMB: PropTypes.number,
  onFilesSelected: PropTypes.func,
  onFilesRejected: PropTypes.func,
  icon: PropTypes.node,
  iconColor: PropTypes.string,
  numberOfFiles: PropTypes.number,
  disabled: PropTypes.bool,
  showProgress: PropTypes.bool,
  progress: PropTypes.number,
  showSelectedFiles: PropTypes.bool,
  showRejectedFiles: PropTypes.bool,
  sx: PropTypes.object,
  paperSx: PropTypes.object,
  variant: PropTypes.oneOf(["outlined", "elevated", "contained"]),
  buttonVariant: PropTypes.oneOf(["outlined", "contained", "text"]),
  buttonText: PropTypes.string,
};

export default FileUpload;
