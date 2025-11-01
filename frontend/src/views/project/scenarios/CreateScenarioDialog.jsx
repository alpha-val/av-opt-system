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
  CircularProgress,
} from "@mui/material";
import { useDispatch } from "react-redux";
import { createScenario } from "../../../redux/scenarioSlice";

const CreateScenarioDialog = ({ open, onClose, projectId, scenarioName }) => {
  const dispatch = useDispatch();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [formData, setFormData] = useState({
    name: scenarioName || "",
    description: "Increase production by 3%",
    goal: "increase_production",
    change_type: "capacity",
    file: null, // Add file field to form data
  });

  const handleChange = (field) => (event) => {
    if (field === "file") {
      setFormData({ ...formData, file: event.target.files[0] }); // Handle file upload
    } else {
      setFormData({ ...formData, [field]: event.target.value });
    }
  };

  const handleSubmit = async () => {
    // if (!formData.file) {
    //   alert("Please upload a file."); // Alert user if file is missing
    //   return;
    // }

    const scenarioData = {
      project_id: projectId,
      name: formData.name || scenarioName || "New Scenario",
      description: formData.description,
      goal: formData.goal,
      change_type: formData.change_type,
      // file: formData.file, // Include the file
    };

    console.log("Submitting new scenario:", scenarioData);
    setIsSubmitting(true);

    try {
      await dispatch(createScenario(scenarioData)).unwrap();

      setFormData({
        name: "",
        description: "",
        goal: "increase_production",
        change_type: "capacity",
        // file: null,
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
          {/* Name */}
          <TextField
            label="Scenario Name"
            fullWidth
            required
            value={formData.name || scenarioName || ""}
            onChange={handleChange("name")}
            placeholder="e.g., Increase production by 10%"
          />
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
              <MenuItem value="reduce_capex">Reduce Cost</MenuItem>
              <MenuItem value="improve_quality">Improve Quality</MenuItem>
              {/* 
              <MenuItem value="change_technology">Change Technology</MenuItem>
              <MenuItem value="other">Other</MenuItem>
              */}
            </Select>
          </FormControl>

          {/* Description */}
          <TextField
            label="Description"
            fullWidth
            multiline
            rows={2}
            value={
              formData.description ||
              "Increase production of the unit by 5%; analyze all impacts."
            }
            onChange={handleChange("description")}
            placeholder="Optional description"
            disabled={isSubmitting}
          />

          {/* Change Type */}
          {/* <FormControl fullWidth>
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
          </FormControl> */}

          {/* File Upload */}
          {/* <TextField
            type="file"
            label="Upload File"
            fullWidth
            InputLabelProps={{ shrink: true }}
            onChange={handleChange("file")}
            disabled={isSubmitting}
            required // Mark the file field as required
          /> */}
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} disabled={isSubmitting}>
          Cancel
        </Button>
        <Button
          variant="contained"
          onClick={handleSubmit}
          disabled={formData.name === "" || isSubmitting} // Ensure file is required
          startIcon={isSubmitting ? <CircularProgress size={20} /> : null}
        >
          {isSubmitting ? "Creating..." : "Create Scenario"}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default CreateScenarioDialog;
