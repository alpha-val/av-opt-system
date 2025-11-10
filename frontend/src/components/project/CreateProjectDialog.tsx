import React, { useState } from "react";
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  Box,
  Typography,
  MenuItem,
  Select,
  FormControl,
  InputLabel,
  FormHelperText,
  Alert,
  LinearProgress,
} from "@mui/material";
import { ProjectCreate, ProjectStatus } from "../../types/api";
import { projectApi } from "../../services/api";

interface CreateProjectDialogProps {
  open: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

const OBJECTIVE_TYPES = [
  "increase production",
  "reduce capex",
  "reduce wastage",
  "improve efficiency",
  "reduce opex",
  "optimize capacity",
];

const CreateProjectDialog: React.FC<CreateProjectDialogProps> = ({
  open,
  onClose,
  onSuccess,
}) => {
  const [formData, setFormData] = useState<Partial<ProjectCreate>>({
    name: "",
    description: "",
    global_objective_type: "",
    global_objective_target: "",
    objective_description: "",
    status: ProjectStatus.DRAFT,
    base_case_documents: [],
    tabular_data_documents: [],
  });

  const [baseCaseFiles, setBaseCaseFiles] = useState<File[]>([]);
  const [tabularDataFiles, setTabularDataFiles] = useState<File[]>([]);
  const [targetValue, setTargetValue] = useState<string>("");
  const [targetType, setTargetType] = useState<"%" | "$">("%");
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  /**
   * Validate form data
   */
  const validateForm = (): boolean => {
    if (!formData.name || formData.name.length === 0) {
      setError("Project name is required");
      return false;
    }
    if (formData.name.length > 40) {
      setError("Project name must be 40 characters or less");
      return false;
    }
    if (formData.description && formData.description.length > 80) {
      setError("Description must be 80 characters or less");
      return false;
    }
    if (!formData.global_objective_type) {
      setError("Global objective type is required");
      return false;
    }
    if (!targetValue) {
      setError("Global objective target is required");
      return false;
    }
    if (baseCaseFiles.length === 0) {
      setError("At least one base case document is required");
      return false;
    }
    if (tabularDataFiles.length === 0) {
      setError("At least one tabular data file is required");
      return false;
    }

    // Validate total file size (25MB)
    const MAX_SIZE = 25 * 1024 * 1024; // 25MB in bytes
    const totalSize =
      baseCaseFiles.reduce((sum, file) => sum + file.size, 0) +
      tabularDataFiles.reduce((sum, file) => sum + file.size, 0);

    if (totalSize > MAX_SIZE) {
      setError(`Total file size exceeds 25MB limit (${(totalSize / 1024 / 1024).toFixed(2)}MB)`);
      return false;
    }

    return true;
  };

  /**
   * Handle form submission
   */
  const handleSubmit = async (): Promise<void> => {
    setError(null);

    if (!validateForm()) {
      return;
    }

    setLoading(true);

    try {
      // Build global objective target string
      const globalObjectiveTarget = `${targetValue}${targetType}`;

      // Create project
      const projectData: ProjectCreate = {
        name: formData.name!,
        description: formData.description || undefined,
        global_objective_type: formData.global_objective_type!,
        global_objective_target: globalObjectiveTarget,
        objective_description: formData.objective_description || undefined,
        status: ProjectStatus.DRAFT,
        base_case_documents: [],
        tabular_data_documents: [],
      };

      const project = await projectApi.create(projectData);

      // Upload files
      await projectApi.uploadProjectFiles(
        project.id,
        baseCaseFiles,
        tabularDataFiles
      );

      // Reset form
      setFormData({
        name: "",
        description: "",
        global_objective_type: "",
        global_objective_target: "",
        objective_description: "",
        status: ProjectStatus.DRAFT,
        base_case_documents: [],
        tabular_data_documents: [],
      });
      setBaseCaseFiles([]);
      setTabularDataFiles([]);
      setTargetValue("");
      setTargetType("%");

      onSuccess();
      onClose();
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : "Failed to create project";
      setError(errorMessage);
      console.error("Error creating project:", err);
    } finally {
      setLoading(false);
    }
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

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>Create New Project</DialogTitle>
      <DialogContent>
        {loading && <LinearProgress sx={{ mb: 2 }} />}
        {error && (
          <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
            {error}
          </Alert>
        )}

        <Box sx={{ display: "flex", flexDirection: "column", gap: 2, pt: 1 }}>
          {/* Project Name */}
          <TextField
            label="Project Name"
            required
            fullWidth
            value={formData.name}
            onChange={(e) =>
              setFormData({ ...formData, name: e.target.value })
            }
            inputProps={{ maxLength: 40 }}
            helperText={`${formData.name?.length || 0}/40 characters`}
          />

          {/* Description */}
          <TextField
            label="Description (Optional)"
            fullWidth
            multiline
            rows={2}
            value={formData.description}
            onChange={(e) =>
              setFormData({ ...formData, description: e.target.value })
            }
            inputProps={{ maxLength: 80 }}
            helperText={`${formData.description?.length || 0}/80 characters`}
          />

          {/* Global Objective Type */}
          <FormControl fullWidth required>
            <InputLabel>Global Objective Type</InputLabel>
            <Select
              value={formData.global_objective_type}
              onChange={(e) =>
                setFormData({
                  ...formData,
                  global_objective_type: e.target.value,
                })
              }
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
                onChange={(e) =>
                  setTargetType(e.target.value as "%" | "$")
                }
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
            value={formData.objective_description}
            onChange={(e) =>
              setFormData({
                ...formData,
                objective_description: e.target.value,
              })
            }
            inputProps={{ maxLength: 500 }}
            helperText={`${formData.objective_description?.length || 0}/500 characters`}
          />

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
          </Box>

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
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} disabled={loading}>
          Cancel
        </Button>
        <Button
          onClick={handleSubmit}
          variant="contained"
          disabled={loading}
        >
          {loading ? "Creating..." : "Create Project"}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default CreateProjectDialog;

