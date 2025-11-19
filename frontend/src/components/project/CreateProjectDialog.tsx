import React, { useState, useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
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
import { ProjectCreate, ProjectStatus, ProjectUpdate } from "../../types/api";
import {
  createProject,
  updateProject,
  selectProjectCreating,
  selectProjectsError,
  clearError,
} from "../../redux/projectsSlice";

interface CreateProjectDialogProps {
  open: boolean;
  onClose: () => void;
  onSuccess: (projectId?: string) => void;
  // Edit mode props
  projectId?: string;
  initialName?: string;
  initialDescription?: string;
}

const CreateProjectDialog: React.FC<CreateProjectDialogProps> = ({
  open,
  onClose,
  onSuccess,
  projectId,
  initialName,
  initialDescription,
}) => {
  const dispatch = useDispatch();
  const isEditMode = !!projectId;
  const creating = useSelector(selectProjectCreating);
  const updating = useSelector(
    (state: any) => state.projects.loading.update
  );
  const loading = isEditMode ? updating : creating;
  const reduxError = useSelector(selectProjectsError);
  const [localError, setLocalError] = useState<string | null>(null);

  const [formData, setFormData] = useState<Partial<ProjectCreate>>({
    name: "",
    description: "",
    status: ProjectStatus.DRAFT,
    base_case_documents: [],
    tabular_data_documents: [],
  });

  // Initialize form data when dialog opens or initial values change
  useEffect(() => {
    if (open) {
      if (isEditMode) {
        // Edit mode: use initial values
        setFormData({
          name: initialName || "",
          description: initialDescription || "",
          status: ProjectStatus.DRAFT,
          base_case_documents: [],
          tabular_data_documents: [],
        });
      } else {
        // Create mode: reset to empty
        setFormData({
          name: "",
          description: "",
          status: ProjectStatus.DRAFT,
          base_case_documents: [],
          tabular_data_documents: [],
        });
      }
    }
  }, [open, isEditMode, initialName, initialDescription]);

  // Combine local and Redux errors
  const error = localError || reduxError;

  // Clear errors when dialog opens/closes
  useEffect(() => {
    if (open) {
      setLocalError(null);
      dispatch(clearError());
    }
  }, [open, dispatch]);

  /**
   * Check if form is valid (for button enable/disable)
   * This is a lighter check than validateForm - doesn't set error messages
   */
  const isFormValid = (): boolean => {
    // Only check required fields: name
    if (!formData.name || formData.name.trim().length === 0 || formData.name.length > 40) {
      return false;
    }
    return true;
  };

  /**
   * Validate form data
   */
  const validateForm = (): boolean => {
    if (!formData.name || formData.name.length === 0) {
      setLocalError("Project name is required");
      return false;
    }
    if (formData.name.length > 40) {
      setLocalError("Project name must be 40 characters or less");
      return false;
    }
    if (formData.description && formData.description.length > 80) {
      setLocalError("Description must be 80 characters or less");
      return false;
    }
    return true;
  };

  /**
   * Handle form submission
   */
  const handleSubmit = (): void => {
    setLocalError(null);
    dispatch(clearError());

    if (!validateForm()) {
      return;
    }

    if (isEditMode && projectId) {
      // Edit mode: update project
      const projectData: ProjectUpdate = {
        name: formData.name!,
        description: formData.description || null,
      };

      dispatch(updateProject({ projectId, projectData }) as any).then(
        (result: any) => {
          if (updateProject.fulfilled.match(result)) {
            onSuccess(projectId);
            onClose();
          }
        }
      );
    } else {
      // Create mode: create new project
      const projectData: ProjectCreate = {
        name: formData.name!,
        description: formData.description || undefined,
        status: ProjectStatus.DRAFT,
        base_case_documents: [],
        tabular_data_documents: [],
      };

      dispatch(createProject(projectData) as any).then((result: any) => {
        if (createProject.fulfilled.match(result)) {
          // Success - reset form and close dialog
          const createdProjectId = result.payload?.id;
          setFormData({
            name: "",
            description: "",
            status: ProjectStatus.DRAFT,
            base_case_documents: [],
            tabular_data_documents: [],
          });
          onSuccess(createdProjectId);
          onClose();
        }
      });
    }
  };


  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>
        {isEditMode ? "Edit Project" : "Create New Project"}
      </DialogTitle>
      <DialogContent>
        {loading && <LinearProgress sx={{ mb: 2 }} />}
        {error && (
          <Alert
            severity="error"
            sx={{ mb: 2 }}
            onClose={() => {
              setLocalError(null);
              dispatch(clearError());
            }}
          >
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

          {!isEditMode && (
            <Alert severity="info" sx={{ mt: 1 }}>
              <Typography variant="body2">
                You can add objective details and upload documents in Project >
                Scenario Details view after creating the project.
              </Typography>
            </Alert>
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
          disabled={loading || !isFormValid()}
        >
          {loading
            ? isEditMode
              ? "Updating..."
              : "Creating..."
            : isEditMode
            ? "Update Project"
            : "Create Project"}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default CreateProjectDialog;

