import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useDispatch, useSelector } from "react-redux";
import {
  Box,
  Typography,
  Button,
  CircularProgress,
  Alert,
  Paper,
  Card,
  CardContent,
  TextField,
  MenuItem,
  Select,
  FormControl,
  InputLabel,
  Divider,
} from "@mui/material";
import {
  ArrowBack as ArrowBackIcon,
  Save as SaveIcon,
  Upload as UploadIcon,
} from "@mui/icons-material";
import {
  fetchProjectById,
  updateProject,
  uploadProjectFiles,
  selectCurrentProject,
  selectProjectsLoading,
  selectProjectsError,
  selectProjectUpdating,
  selectProjectUploadingFiles,
  clearError,
} from "../../redux/projectsSlice";
import { ProjectUpdate } from "../../types/api";

const OBJECTIVE_TYPES = [
  "increase production",
  "reduce capex",
  "reduce wastage",
  "improve efficiency",
  "reduce opex",
  "optimize capacity",
];

/**
 * System Base Design view for entity validation.
 * 
 * This is a placeholder component that will be extended later to:
 * - Display extracted entities in structured view
 * - Show entity attributes (tank diameter, height, pump ratings, etc.)
 * - Allow editing attributes (mark as fixed/variable, set ranges)
 * - Submit updated system design
 */
const SystemBaseDesign: React.FC = () => {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const project = useSelector(selectCurrentProject);
  const loading = useSelector((state: any) => state.projects.loading.fetchById);
  const updating = useSelector(selectProjectUpdating);
  const uploadingFiles = useSelector(selectProjectUploadingFiles);
  const error = useSelector(selectProjectsError);

  // Objective details form state
  const [objectiveType, setObjectiveType] = useState<string>("");
  const [targetValue, setTargetValue] = useState<string>("");
  const [targetType, setTargetType] = useState<"%" | "$">("%");
  const [objectiveDescription, setObjectiveDescription] = useState<string>("");

  // File upload state
  const [baseCaseFiles, setBaseCaseFiles] = useState<File[]>([]);
  const [tabularDataFiles, setTabularDataFiles] = useState<File[]>([]);
  const [objectiveError, setObjectiveError] = useState<string | null>(null);
  const [fileError, setFileError] = useState<string | null>(null);

  /**
   * Fetch project data
   */
  useEffect(() => {
    if (projectId) {
      // Only fetch if we don't have the project or it's a different project
      if (!project || project.id !== projectId) {
        dispatch(fetchProjectById(projectId) as any);
      }
    }
  }, [projectId, project, dispatch]);

  /**
   * Initialize form with project data when project loads
   */
  useEffect(() => {
    if (project) {
      setObjectiveType(project.global_objective_type || "");
      // Parse target value and type from global_objective_target
      if (project.global_objective_target) {
        const match = project.global_objective_target.match(/^([\d.]+)([%$])$/);
        if (match) {
          setTargetValue(match[1]);
          setTargetType(match[2] as "%" | "$");
        } else {
          setTargetValue(project.global_objective_target);
        }
      }
      setObjectiveDescription(project.objective_description || "");
    }
  }, [project]);

  /**
   * Handle saving objective details
   */
  const handleSaveObjectiveDetails = (): void => {
    if (!projectId) return;

    setObjectiveError(null);
    dispatch(clearError());

    // Validate objective fields
    if (!objectiveType) {
      setObjectiveError("Global objective type is required");
      return;
    }
    if (!targetValue || targetValue.trim().length === 0) {
      setObjectiveError("Global objective target is required");
      return;
    }

    // Build global objective target string
    const globalObjectiveTarget = `${targetValue}${targetType}`;

    // Create update payload
    const updateData: ProjectUpdate = {
      global_objective_type: objectiveType,
      global_objective_target: globalObjectiveTarget,
      objective_description: objectiveDescription || undefined,
    };

    // Dispatch update
    dispatch(updateProject({ projectId, projectData: updateData }) as any);
  };

  /**
   * Handle file upload
   */
  const handleUploadFiles = (): void => {
    if (!projectId) return;

    setFileError(null);
    dispatch(clearError());

    // Validate files
    if (baseCaseFiles.length === 0) {
      setFileError("At least one base case document is required");
      return;
    }
    if (tabularDataFiles.length === 0) {
      setFileError("At least one tabular data file is required");
      return;
    }

    // Validate total file size (25MB)
    const MAX_SIZE = 25 * 1024 * 1024; // 25MB in bytes
    const totalSize =
      baseCaseFiles.reduce((sum, file) => sum + file.size, 0) +
      tabularDataFiles.reduce((sum, file) => sum + file.size, 0);

    if (totalSize > MAX_SIZE) {
      setFileError(
        `Total file size exceeds 25MB limit (${(totalSize / 1024 / 1024).toFixed(2)}MB)`
      );
      return;
    }

    // Dispatch file upload
    dispatch(
      uploadProjectFiles({
        projectId,
        baseCaseFiles,
        tabularDataFiles,
      }) as any
    ).then((result: any) => {
      if (uploadProjectFiles.fulfilled.match(result)) {
        // Clear file selections on success
        setBaseCaseFiles([]);
        setTabularDataFiles([]);
      }
    });
  };

  /**
   * Handle file selection for base case documents
   */
  const handleBaseCaseFilesChange = (
    event: React.ChangeEvent<HTMLInputElement>
  ): void => {
    if (event.target.files) {
      const files = Array.from(event.target.files);
      // Filter for PDF files only
      const pdfFiles = files.filter(
        (file) => file.type === "application/pdf"
      );
      setBaseCaseFiles([...baseCaseFiles, ...pdfFiles]);
    }
  };

  /**
   * Handle file selection for tabular data
   */
  const handleTabularDataFilesChange = (
    event: React.ChangeEvent<HTMLInputElement>
  ): void => {
    if (event.target.files) {
      const files = Array.from(event.target.files);
      // Filter for allowed types: PDF, Excel, CSV
      const allowedTypes = [
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/vnd.ms-excel",
        "text/csv",
      ];
      const validFiles = files.filter((file) =>
        allowedTypes.includes(file.type)
      );
      setTabularDataFiles([...tabularDataFiles, ...validFiles]);
    }
  };

  /**
   * Remove a base case file
   */
  const removeBaseCaseFile = (index: number): void => {
    setBaseCaseFiles(baseCaseFiles.filter((_, i) => i !== index));
  };

  /**
   * Remove a tabular data file
   */
  const removeTabularDataFile = (index: number): void => {
    setTabularDataFiles(tabularDataFiles.filter((_, i) => i !== index));
  };

  /**
   * Format file size for display
   */
  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(2)} KB`;
    return `${(bytes / 1024 / 1024).toFixed(2)} MB`;
  };

  if (!projectId) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error">Invalid project ID</Alert>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box
        sx={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          mb: 3,
        }}
      >
        <Box sx={{ display: "flex", alignItems: "center", gap: 2 }}>
          <Button
            startIcon={<ArrowBackIcon />}
            onClick={() => navigate("/projects")}
          >
            Back
          </Button>
          <Typography variant="h4" component="h1">
            System Design
          </Typography>
        </Box>
      </Box>

      {/* Error Alert */}
      {error && (
        <Alert
          severity="error"
          sx={{ mb: 2 }}
          onClose={() => dispatch(clearError())}
        >
          {error}
        </Alert>
      )}

      {/* Loading State */}
      {loading ? (
        <Box
          sx={{
            display: "flex",
            justifyContent: "center",
            alignItems: "center",
            minHeight: "400px",
          }}
        >
          <CircularProgress />
        </Box>
      ) : project ? (
        /* Project Info and Forms */
        <Box sx={{ display: "flex", flexDirection: "column", gap: 3 }}>
          {/* Project Information */}
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Project: {project.name}
              </Typography>
              {project.description && (
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  {project.description}
                </Typography>
              )}
              {project.global_objective_type && project.global_objective_target && (
                <Typography variant="body2" color="text.secondary">
                  Objective: {project.global_objective_type} - {project.global_objective_target}
                </Typography>
              )}
            </CardContent>
          </Card>

          {/* Objective Details Form */}
          <Card>
            <CardContent>
              <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", mb: 2 }}>
                <Typography variant="h6">Objective Details</Typography>
                <Button
                  variant="contained"
                  startIcon={<SaveIcon />}
                  onClick={handleSaveObjectiveDetails}
                  disabled={updating || loading}
                >
                  {updating ? "Saving..." : "Save Objective Details"}
                </Button>
              </Box>

              {objectiveError && (
                <Alert severity="error" sx={{ mb: 2 }} onClose={() => setObjectiveError(null)}>
                  {objectiveError}
                </Alert>
              )}

              <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
                {/* Global Objective Type */}
                <FormControl fullWidth required>
                  <InputLabel>Global Objective Type</InputLabel>
                  <Select
                    value={objectiveType}
                    onChange={(e) => setObjectiveType(e.target.value)}
                    label="Global Objective Type"
                  >
                    {OBJECTIVE_TYPES.map((type) => (
                      <MenuItem key={type} value={type}>
                        {type}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>

                {/* Global Objective Target */}
                <Box sx={{ display: "flex", gap: 1, alignItems: "flex-start" }}>
                  <TextField
                    label="Global Objective Target"
                    required
                    type="number"
                    value={targetValue}
                    onChange={(e) => setTargetValue(e.target.value)}
                    sx={{ flex: 1 }}
                  />
                  <FormControl sx={{ minWidth: 80 }}>
                    <Select
                      value={targetType}
                      onChange={(e) => setTargetType(e.target.value as "%" | "$")}
                    >
                      <MenuItem value="%">%</MenuItem>
                      <MenuItem value="$">$</MenuItem>
                    </Select>
                  </FormControl>
                </Box>

                {/* Objective Description */}
                <TextField
                  label="Objective Description (Optional)"
                  fullWidth
                  multiline
                  rows={3}
                  value={objectiveDescription}
                  onChange={(e) => setObjectiveDescription(e.target.value)}
                  inputProps={{ maxLength: 500 }}
                  helperText={`${objectiveDescription.length}/500 characters`}
                />
              </Box>
            </CardContent>
          </Card>

          {/* File Upload Section */}
          <Card>
            <CardContent>
              <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", mb: 2 }}>
                <Typography variant="h6">Document Upload</Typography>
                <Button
                  variant="contained"
                  startIcon={<UploadIcon />}
                  onClick={handleUploadFiles}
                  disabled={uploadingFiles || loading}
                >
                  {uploadingFiles ? "Uploading..." : "Upload Documents"}
                </Button>
              </Box>

              {fileError && (
                <Alert severity="error" sx={{ mb: 2 }} onClose={() => setFileError(null)}>
                  {fileError}
                </Alert>
              )}

              <Box sx={{ display: "flex", flexDirection: "column", gap: 3 }}>
                {/* Base Case Documents */}
                <Box>
                  <Typography variant="subtitle2" gutterBottom>
                    Base Case Report Documents (PDF) - Required
                  </Typography>
                  <input
                    accept="application/pdf"
                    style={{ display: "none" }}
                    id="base-case-files-input"
                    type="file"
                    multiple
                    onChange={handleBaseCaseFilesChange}
                  />
                  <label htmlFor="base-case-files-input">
                    <Button variant="outlined" component="span" size="small">
                      Add PDF Files
                    </Button>
                  </label>
                  {baseCaseFiles.length > 0 && (
                    <Box sx={{ mt: 1 }}>
                      {baseCaseFiles.map((file, index) => (
                        <Box
                          key={index}
                          sx={{
                            display: "flex",
                            justifyContent: "space-between",
                            alignItems: "center",
                            p: 1,
                            border: "1px solid",
                            borderColor: "divider",
                            borderRadius: 1,
                            mb: 0.5,
                          }}
                        >
                          <Typography variant="body2">
                            {file.name} ({formatFileSize(file.size)})
                          </Typography>
                          <Button
                            size="small"
                            color="error"
                            onClick={() => removeBaseCaseFile(index)}
                          >
                            Remove
                          </Button>
                        </Box>
                      ))}
                    </Box>
                  )}
                  {project.base_case_documents && project.base_case_documents.length > 0 && (
                    <Alert severity="success" sx={{ mt: 1 }}>
                      {project.base_case_documents.length} base case document(s) uploaded
                    </Alert>
                  )}
                </Box>

                <Divider />

                {/* Tabular Data Files */}
                <Box>
                  <Typography variant="subtitle2" gutterBottom>
                    Tabular Data Files (PDF, Excel, CSV) - Required
                  </Typography>
                  <input
                    accept=".pdf,.xlsx,.xls,.csv"
                    style={{ display: "none" }}
                    id="tabular-data-files-input"
                    type="file"
                    multiple
                    onChange={handleTabularDataFilesChange}
                  />
                  <label htmlFor="tabular-data-files-input">
                    <Button variant="outlined" component="span" size="small">
                      Add Files
                    </Button>
                  </label>
                  {tabularDataFiles.length > 0 && (
                    <Box sx={{ mt: 1 }}>
                      {tabularDataFiles.map((file, index) => (
                        <Box
                          key={index}
                          sx={{
                            display: "flex",
                            justifyContent: "space-between",
                            alignItems: "center",
                            p: 1,
                            border: "1px solid",
                            borderColor: "divider",
                            borderRadius: 1,
                            mb: 0.5,
                          }}
                        >
                          <Typography variant="body2">
                            {file.name} ({formatFileSize(file.size)})
                          </Typography>
                          <Button
                            size="small"
                            color="error"
                            onClick={() => removeTabularDataFile(index)}
                          >
                            Remove
                          </Button>
                        </Box>
                      ))}
                    </Box>
                  )}
                  {project.tabular_data_documents && project.tabular_data_documents.length > 0 && (
                    <Alert severity="success" sx={{ mt: 1 }}>
                      {project.tabular_data_documents.length} tabular data file(s) uploaded
                    </Alert>
                  )}
                </Box>

                {/* Total File Size Display */}
                {(baseCaseFiles.length > 0 || tabularDataFiles.length > 0) && (
                  <Typography variant="caption" color="text.secondary">
                    Total size:{" "}
                    {formatFileSize(
                      baseCaseFiles.reduce((sum, f) => sum + f.size, 0) +
                        tabularDataFiles.reduce((sum, f) => sum + f.size, 0)
                    )}{" "}
                    / 25 MB
                  </Typography>
                )}
              </Box>
            </CardContent>
          </Card>

          {/* Placeholder for Entity Validation */}
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Extracted Entities
              </Typography>
              <Typography variant="body2" color="text.secondary">
                This is a placeholder view. The actual implementation will:
              </Typography>
              <Box component="ul" sx={{ mt: 2, pl: 3 }}>
                <li>
                  <Typography variant="body2">
                    Display extracted entities in a structured view
                  </Typography>
                </li>
                <li>
                  <Typography variant="body2">
                    Show entity attributes (tank diameter, height, pump ratings, etc.)
                  </Typography>
                </li>
                <li>
                  <Typography variant="body2">
                    Allow editing attributes (mark as fixed/variable, set ranges)
                  </Typography>
                </li>
                <li>
                  <Typography variant="body2">
                    Submit updated system design to backend
                  </Typography>
                </li>
              </Box>
              <Alert severity="info" sx={{ mt: 2 }}>
                No entities extracted yet. Upload and process documents first.
              </Alert>
            </CardContent>
          </Card>
        </Box>
      ) : (
        <Alert severity="warning">Project not found</Alert>
      )}
    </Box>
  );
};

export default SystemBaseDesign;

