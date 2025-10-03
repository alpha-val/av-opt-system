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
} from "@mui/material";
import { useDispatch } from "react-redux";
import { createScenario } from "../../../redux/scenarioSlice";

const CreateScenarioDialog = ({ open, onClose, projectId }) => {
  const dispatch = useDispatch();

  const [formData, setFormData] = useState({
    name: "",
    description: "",
    goal: "increase_production",
    change_type: "capacity",
    target_metric: "throughput",
    target_value: "",
    target_unit: "%",
    budget_capex: "",
    use_existing_equipment_only: false,
  });

  const handleChange = (field) => (event) => {
    setFormData({ ...formData, [field]: event.target.value });
  };

  const handleSubmit = () => {
    const scenario = {
      project_id: projectId,
      name: formData.name,
      description: formData.description,
      goal: formData.goal,
      change_type: formData.change_type,
      target: {
        metric: formData.target_metric,
        value: parseFloat(formData.target_value),
        unit: formData.target_unit,
      },
      constraints: {
        budget_capex: formData.budget_capex
          ? parseFloat(formData.budget_capex)
          : undefined,
        use_existing_equipment_only: formData.use_existing_equipment_only,
      },
      status: "draft",
    };

    dispatch(createScenario(scenario));
    onClose();

    // Reset form
    setFormData({
      name: "",
      description: "",
      goal: "increase_production",
      change_type: "capacity",
      target_metric: "throughput",
      target_value: "",
      target_unit: "%",
      budget_capex: "",
      use_existing_equipment_only: false,
    });
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
          />

          {/* Change Type */}
          <FormControl fullWidth>
            <InputLabel>Type of Change</InputLabel>
            <Select
              value={formData.change_type}
              onChange={handleChange("change_type")}
              label="Type of Change"
            >
              <MenuItem value="equipment">Equipment</MenuItem>
              <MenuItem value="process">Process</MenuItem>
              <MenuItem value="capacity">Capacity</MenuItem>
              <MenuItem value="location">Location</MenuItem>
              <MenuItem value="technology">Technology</MenuItem>
            </Select>
          </FormControl>

          {/* Target */}
          <Box>
            <Typography variant="subtitle2" gutterBottom>
              Target
            </Typography>
            <Box sx={{ display: "flex", gap: 1 }}>
              <FormControl sx={{ minWidth: 150 }}>
                <InputLabel>Metric</InputLabel>
                <Select
                  value={formData.target_metric}
                  onChange={handleChange("target_metric")}
                  label="Metric"
                  size="small"
                >
                  <MenuItem value="throughput">Throughput</MenuItem>
                  <MenuItem value="cost">Cost</MenuItem>
                  <MenuItem value="quality_score">Quality Score</MenuItem>
                  <MenuItem value="efficiency">Efficiency</MenuItem>
                </Select>
              </FormControl>

              <TextField
                label="Value"
                type="number"
                value={formData.target_value}
                onChange={handleChange("target_value")}
                size="small"
                sx={{ width: 100 }}
              />

              <FormControl sx={{ width: 100 }}>
                <InputLabel>Unit</InputLabel>
                <Select
                  value={formData.target_unit}
                  onChange={handleChange("target_unit")}
                  label="Unit"
                  size="small"
                >
                  <MenuItem value="%">%</MenuItem>
                  <MenuItem value="units">units</MenuItem>
                  <MenuItem value="USD">USD</MenuItem>
                  <MenuItem value="units/day">units/day</MenuItem>
                </Select>
              </FormControl>
            </Box>
          </Box>

          {/* Constraints */}
          <Box>
            <Typography variant="subtitle2" gutterBottom>
              Constraints (Optional)
            </Typography>

            <TextField
              label="Budget (CAPEX)"
              type="number"
              fullWidth
              value={formData.budget_capex}
              onChange={handleChange("budget_capex")}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">$</InputAdornment>
                ),
              }}
              sx={{ mb: 2 }}
            />

            <FormControl component="fieldset">
              <Typography variant="body2" gutterBottom>
                Use existing equipment only?
              </Typography>
              <RadioGroup
                row
                value={formData.use_existing_equipment_only}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    use_existing_equipment_only: e.target.value === "true",
                  })
                }
              >
                <FormControlLabel
                  value={false}
                  control={<Radio />}
                  label="No"
                />
                <FormControlLabel
                  value={true}
                  control={<Radio />}
                  label="Yes"
                />
              </RadioGroup>
            </FormControl>
          </Box>
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button
          variant="contained"
          onClick={handleSubmit}
          disabled={!formData.name || !formData.target_value}
        >
          Create Scenario
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default CreateScenarioDialog;
