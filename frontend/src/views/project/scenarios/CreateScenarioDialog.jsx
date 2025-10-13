import React, { useState } from "react";
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
  InputAdornment,
  RadioGroup,
  FormControlLabel,
  Radio,
  CircularProgress,
} from "@mui/material";
import { useDispatch } from "react-redux";
import { createScenario } from "../../../redux/scenarioSlice";

const CreateScenarioDialog = ({ open, onClose, projectId }) => {
  const dispatch = useDispatch();
  const [isSubmitting, setIsSubmitting] = useState(false);

  const [formData, setFormData] = useState({
    name: "",
    description: "",
    goal: "increase_production",
    change_type: "capacity",
  });

  const handleChange = (field) => (event) => {
    setFormData({ ...formData, [field]: event.target.value });
  };

  const handleSubmit = async () => {
    const scenario = {
      project_id: projectId,
      name: formData.name,
      description: formData.description,
      goal: formData.goal,
      change_type: formData.change_type,
      status: "draft",
    };

    console.log("Submitting new scenario:", scenario);
    setIsSubmitting(true);

    try {
      await dispatch(createScenario(scenario)).unwrap();

      setFormData({
        name: "",
        description: "",
        goal: "increase_production",
        change_type: "capacity",
      });

      onClose();
    } catch (error) {
      console.error("Failed to create scenario:", error);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>Create New Scenario</DialogTitle>
      <DialogContent>
        <Box sx={{ pt: 2, display: "flex", flexDirection: "column", gap: 2 }}>
          {/* Goal Selection */}
          <FormControl fullWidth>
            <InputLabel>What are you trying to achieve?</InputLabel>
            <Select
              value={formData.goal}
              onChange={handleChange("goal")}
              label="What are you trying to achieve?"
              disabled={isSubmitting}
            >
              <MenuItem value="increase_production">
                Increase Production
              </MenuItem>
              <MenuItem value="reduce_cost">Reduce Cost</MenuItem>
              <MenuItem value="improve_quality">Improve Quality</MenuItem>
              <MenuItem value="change_technology">Change Technology</MenuItem>
              <MenuItem value="other">Other</MenuItem>
            </Select>
          </FormControl>

          {/* Name */}
          <TextField
            label="Scenario Name"
            fullWidth
            required
            value={formData.name}
            onChange={handleChange("name")}
            placeholder="e.g., Increase production by 10%"
            disabled={isSubmitting}
          />

          {/* Description */}
          <TextField
            label="Description"
            fullWidth
            multiline
            rows={2}
            value={formData.description}
            onChange={handleChange("description")}
            placeholder="Optional description"
            disabled={isSubmitting}
          />

          {/* Change Type */}
          <FormControl fullWidth>
            <InputLabel>Type of Change</InputLabel>
            <Select
              value={formData.change_type}
              onChange={handleChange("change_type")}
              label="Type of Change"
              disabled={isSubmitting}
            >
              <MenuItem value="equipment">Equipment</MenuItem>
              <MenuItem value="process">Process</MenuItem>
              <MenuItem value="capacity">Capacity</MenuItem>
              <MenuItem value="location">Location</MenuItem>
              <MenuItem value="technology">Technology</MenuItem>
            </Select>
          </FormControl>
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} disabled={isSubmitting}>
          Cancel
        </Button>
        <Button
          variant="contained"
          onClick={handleSubmit}
          disabled={!formData.name || isSubmitting}
          startIcon={isSubmitting ? <CircularProgress size={20} /> : null}
        >
          {isSubmitting ? "Creating..." : "Create Scenario"}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default CreateScenarioDialog;
