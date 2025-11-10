import React, { useState, useEffect } from "react";
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Box,
  Typography,
  Divider,
  CircularProgress,
} from "@mui/material";
import { useDispatch, useSelector } from "react-redux";
import {
  createScenario,
  updateScenario,
  selectScenariosLoading,
} from "../../../redux/scenarioSlice";

const ScenarioFormDialog = ({
  open,
  onClose,
  projectId,
  scenario = null, // If provided, we're editing
}) => {
  const dispatch = useDispatch();
  const loading = useSelector(selectScenariosLoading);
  const isEditMode = !!scenario;

  const [formData, setFormData] = useState({
    name: "",
    description: "",
    global_objective: {
      goal_type: "increase_production",
      change_direction: "increase",
      change_magnitude: 0,
      change_unit: "%",
      description: "",
    },
    base_case_reference_id: "",
    status: "draft",
  });

  const [errors, setErrors] = useState({});

  // Initialize form data when scenario is provided (edit mode)
  useEffect(() => {
    if (scenario) {
      setFormData({
        name: scenario.name || "",
        description: scenario.description || "",
        global_objective: scenario.global_objective || {
          goal_type: "increase_production",
          change_direction: "increase",
          change_magnitude: 0,
          change_unit: "%",
          description: "",
        },
        base_case_reference_id: scenario.base_case_reference_id || "",
        status: scenario.status || "draft",
      });
    } else {
      // Reset form for new scenario
      setFormData({
        name: "",
        description: "",
        global_objective: {
          goal_type: "increase_production",
          change_direction: "increase",
          change_magnitude: 0,
          change_unit: "%",
          description: "",
        },
        base_case_reference_id: "",
        status: "draft",
      });
    }
    setErrors({});
  }, [scenario, open]);

  const handleChange = (field) => (event) => {
    const value = event.target.value;
    if (field.startsWith("global_objective.")) {
      const subField = field.split(".")[1];
      setFormData({
        ...formData,
        global_objective: {
          ...formData.global_objective,
          [subField]: value,
        },
      });
    } else {
      setFormData({
        ...formData,
        [field]: value,
      });
    }
    // Clear error for this field
    if (errors[field]) {
      setErrors({ ...errors, [field]: null });
    }
  };

  const validateForm = () => {
    const newErrors = {};
    if (!formData.name.trim()) {
      newErrors.name = "Name is required";
    }
    if (formData.name.length > 200) {
      newErrors.name = "Name must be 200 characters or less";
    }
    if (formData.global_objective.change_magnitude < 0) {
      newErrors.change_magnitude = "Change magnitude must be positive";
    }
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async () => {
    if (!validateForm()) {
      return;
    }

    const scenarioData = {
      ...formData,
      project_id: projectId,
    };

    try {
      if (isEditMode) {
        await dispatch(
          updateScenario({ scenarioId: scenario.id, data: scenarioData })
        ).unwrap();
      } else {
        await dispatch(createScenario(scenarioData)).unwrap();
      }
      onClose(true); // Pass true to indicate success
    } catch (error) {
      console.error("Failed to save scenario:", error);
      // Error will be handled by Redux state
    }
  };

  const goalTypes = [
    { value: "increase_production", label: "Increase Production" },
    { value: "reduce_capex", label: "Reduce CAPEX" },
    { value: "improve_quality", label: "Improve Quality" },
    { value: "change_technology", label: "Change Technology" },
    { value: "other", label: "Other" },
  ];

  return (
    <Dialog
      open={open}
      onClose={() => onClose(false)}
      maxWidth="md"
      fullWidth
      PaperProps={{
        component: "form",
        onSubmit: (e) => {
          e.preventDefault();
          handleSubmit();
        },
      }}
    >
      <DialogTitle>
        {isEditMode ? "Edit Scenario" : "Create New Scenario"}
      </DialogTitle>
      <DialogContent>
        <Box sx={{ display: "flex", flexDirection: "column", gap: 3, pt: 2 }}>
          {/* Name */}
          <TextField
            label="Scenario Name"
            required
            fullWidth
            value={formData.name}
            onChange={handleChange("name")}
            error={!!errors.name}
            helperText={errors.name || `${formData.name.length}/200 characters`}
            inputProps={{ maxLength: 200 }}
          />

          {/* Description */}
          <TextField
            label="Description"
            fullWidth
            multiline
            rows={3}
            value={formData.description}
            onChange={handleChange("description")}
            helperText="Optional description of the scenario"
          />

          <Divider sx={{ my: 1 }} />

          {/* Global Objective Section */}
          <Typography variant="h6">Global Objective</Typography>

          {/* Goal Type */}
          <FormControl fullWidth>
            <InputLabel>Goal Type</InputLabel>
            <Select
              value={formData.global_objective.goal_type}
              onChange={handleChange("global_objective.goal_type")}
              label="Goal Type"
            >
              {goalTypes.map((type) => (
                <MenuItem key={type.value} value={type.value}>
                  {type.label}
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          {/* Change Direction */}
          <FormControl fullWidth>
            <InputLabel>Change Direction</InputLabel>
            <Select
              value={formData.global_objective.change_direction}
              onChange={handleChange("global_objective.change_direction")}
              label="Change Direction"
            >
              <MenuItem value="increase">Increase</MenuItem>
              <MenuItem value="decrease">Decrease</MenuItem>
            </Select>
          </FormControl>

          {/* Change Magnitude and Unit */}
          <Box sx={{ display: "flex", gap: 2 }}>
            <TextField
              label="Change Magnitude"
              type="number"
              fullWidth
              value={formData.global_objective.change_magnitude}
              onChange={handleChange("global_objective.change_magnitude")}
              error={!!errors.change_magnitude}
              helperText={errors.change_magnitude}
              inputProps={{ min: 0, step: 0.1 }}
            />
            <TextField
              label="Unit"
              fullWidth
              value={formData.global_objective.change_unit}
              onChange={handleChange("global_objective.change_unit")}
              placeholder="%, USD, tpd, gpm, etc."
            />
          </Box>

          {/* Objective Description */}
          <TextField
            label="Objective Description"
            fullWidth
            multiline
            rows={2}
            value={formData.global_objective.description}
            onChange={handleChange("global_objective.description")}
            helperText="Optional detailed description of the objective"
          />

          {/* Base Case Reference */}
          <TextField
            label="Base Case Reference ID"
            fullWidth
            value={formData.base_case_reference_id}
            onChange={handleChange("base_case_reference_id")}
            helperText="Optional reference to a base case document"
          />

          {/* Status (only in edit mode) */}
          {isEditMode && (
            <FormControl fullWidth>
              <InputLabel>Status</InputLabel>
              <Select
                value={formData.status}
                onChange={handleChange("status")}
                label="Status"
              >
                <MenuItem value="draft">Draft</MenuItem>
                <MenuItem value="analyzing">Analyzing</MenuItem>
                <MenuItem value="ready">Ready</MenuItem>
                <MenuItem value="archived">Archived</MenuItem>
              </Select>
            </FormControl>
          )}
        </Box>
      </DialogContent>
      <DialogActions sx={{ px: 3, pb: 2 }}>
        <Button
          onClick={() => onClose(false)}
          disabled={loading.create || loading.update}
        >
          Cancel
        </Button>
        <Button
          type="submit"
          variant="contained"
          disabled={loading.create || loading.update}
          onClick={handleSubmit}
        >
          {loading.create || loading.update ? (
            <CircularProgress size={20} />
          ) : isEditMode ? (
            "Save Changes"
          ) : (
            "Create Scenario"
          )}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default ScenarioFormDialog;

