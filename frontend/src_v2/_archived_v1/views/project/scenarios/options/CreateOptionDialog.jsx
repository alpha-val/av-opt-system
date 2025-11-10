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
  Stepper,
  Step,
  StepLabel,
  Divider,
  IconButton,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
} from "@mui/material";
import { Add as AddIcon, Delete as DeleteIcon } from "@mui/icons-material";
import { useDispatch } from "react-redux";
import { createOption } from "../../../../redux/optionSlice";

const CreateOptionDialog = ({ open, onClose, scenarioId, scenario }) => {
  const dispatch = useDispatch();
  const [activeStep, setActiveStep] = useState(0);

  const [formData, setFormData] = useState({
    name: "",
    description: "",
    strategy: "balanced",
    // Estimates
    capex_value: "",
    opex_value: "",
    timeline_value: "",
    timeline_unit: "months",
    risk_level: "medium",
    confidence: 0.75,
    // Changes
    equipment_changes: [],
    process_changes: [],
  });

  const [newEquipmentChange, setNewEquipmentChange] = useState({
    action: "resize",
    ref_id: "",
    from_value: "",
    from_unit: "",
    to_value: "",
    to_unit: "",
    notes: "",
  });

  const steps = ["Basic Info", "Estimates", "Changes", "Review"];

  const handleChange = (field) => (event) => {
    setFormData({ ...formData, [field]: event.target.value });
  };

  const handleAddEquipmentChange = () => {
    if (newEquipmentChange.ref_id) {
      setFormData({
        ...formData,
        equipment_changes: [
          ...formData.equipment_changes,
          { ...newEquipmentChange },
        ],
      });
      setNewEquipmentChange({
        action: "resize",
        ref_id: "",
        from_value: "",
        from_unit: "",
        to_value: "",
        to_unit: "",
        notes: "",
      });
    }
  };

  const handleRemoveEquipmentChange = (index) => {
    setFormData({
      ...formData,
      equipment_changes: formData.equipment_changes.filter(
        (_, i) => i !== index
      ),
    });
  };

  const handleNext = () => {
    setActiveStep((prev) => prev + 1);
  };

  const handleBack = () => {
    setActiveStep((prev) => prev - 1);
  };

  const handleSubmit = () => {
    const option = {
      scenario_id: scenarioId,
      name: formData.name,
      description: formData.description,
      strategy: formData.strategy,
      confidence: parseFloat(formData.confidence),
      specs: {
        equipment_changes: formData.equipment_changes.map((ec) => ({
          action: ec.action,
          ref_id: ec.ref_id,
          from: ec.from_value
            ? { value: parseFloat(ec.from_value), unit: ec.from_unit }
            : undefined,
          to: ec.to_value
            ? { value: parseFloat(ec.to_value), unit: ec.to_unit }
            : undefined,
          notes: ec.notes,
        })),
        process_changes: formData.process_changes,
      },
      estimates: {
        capex: formData.capex_value
          ? {
              value: parseFloat(formData.capex_value),
              currency: "USD",
            }
          : undefined,
        opex_per_year: formData.opex_value
          ? {
              value: parseFloat(formData.opex_value),
              currency: "USD",
            }
          : undefined,
        timeline: formData.timeline_value
          ? {
              value: parseFloat(formData.timeline_value),
              unit: formData.timeline_unit,
            }
          : undefined,
        risk_level: formData.risk_level,
      },
    };

    dispatch(createOption(option));
    onClose();

    // Reset form
    setFormData({
      name: "",
      description: "",
      strategy: "balanced",
      capex_value: "",
      opex_value: "",
      timeline_value: "",
      timeline_unit: "months",
      risk_level: "medium",
      confidence: 0.75,
      equipment_changes: [],
      process_changes: [],
    });
    setActiveStep(0);
  };

  const renderStepContent = (step) => {
    switch (step) {
      case 0:
        return (
          <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
            <TextField
              label="Option Name"
              fullWidth
              required
              value={formData.name}
              onChange={handleChange("name")}
              placeholder="e.g., Upsize Tanks & Mixer"
            />
            <TextField
              label="Description"
              fullWidth
              multiline
              rows={2}
              value={formData.description}
              onChange={handleChange("description")}
              placeholder="Brief description of this option"
            />
            <FormControl fullWidth>
              <InputLabel>Strategy</InputLabel>
              <Select
                value={formData.strategy}
                onChange={handleChange("strategy")}
                label="Strategy"
              >
                <MenuItem value="lowest_capex">Lowest CAPEX</MenuItem>
                <MenuItem value="lowest_opex">Lowest OPEX</MenuItem>
                <MenuItem value="fastest">Fastest Implementation</MenuItem>
                <MenuItem value="balanced">Balanced Approach</MenuItem>
                <MenuItem value="custom">Custom</MenuItem>
              </Select>
            </FormControl>
          </Box>
        );

      case 1:
        return (
          <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
            <Typography variant="subtitle2" gutterBottom>
              Cost Estimates
            </Typography>
            <TextField
              label="CAPEX"
              type="number"
              fullWidth
              value={formData.capex_value}
              onChange={handleChange("capex_value")}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">$</InputAdornment>
                ),
              }}
            />
            <TextField
              label="OPEX per Year"
              type="number"
              fullWidth
              value={formData.opex_value}
              onChange={handleChange("opex_value")}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">$</InputAdornment>
                ),
              }}
            />

            <Divider sx={{ my: 1 }} />

            <Typography variant="subtitle2" gutterBottom>
              Timeline & Risk
            </Typography>
            <Box sx={{ display: "flex", gap: 1 }}>
              <TextField
                label="Timeline"
                type="number"
                value={formData.timeline_value}
                onChange={handleChange("timeline_value")}
                sx={{ flex: 1 }}
              />
              <FormControl sx={{ minWidth: 120 }}>
                <InputLabel>Unit</InputLabel>
                <Select
                  value={formData.timeline_unit}
                  onChange={handleChange("timeline_unit")}
                  label="Unit"
                >
                  <MenuItem value="weeks">Weeks</MenuItem>
                  <MenuItem value="months">Months</MenuItem>
                </Select>
              </FormControl>
            </Box>

            <FormControl fullWidth>
              <InputLabel>Risk Level</InputLabel>
              <Select
                value={formData.risk_level}
                onChange={handleChange("risk_level")}
                label="Risk Level"
              >
                <MenuItem value="low">Low</MenuItem>
                <MenuItem value="medium">Medium</MenuItem>
                <MenuItem value="high">High</MenuItem>
              </Select>
            </FormControl>

            <Box>
              <Typography variant="body2" gutterBottom>
                Confidence: {Math.round(formData.confidence * 100)}%
              </Typography>
              <input
                type="range"
                min="0"
                max="1"
                step="0.05"
                value={formData.confidence}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    confidence: parseFloat(e.target.value),
                  })
                }
                style={{ width: "100%" }}
              />
            </Box>
          </Box>
        );

      case 2:
        return (
          <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
            <Typography variant="subtitle2" gutterBottom>
              Equipment Changes
            </Typography>

            {/* List of added changes */}
            {formData.equipment_changes.length > 0 && (
              <List dense>
                {formData.equipment_changes.map((change, index) => (
                  <ListItem key={index}>
                    <ListItemText
                      primary={`${change.action}: ${change.ref_id}`}
                      secondary={
                        change.from_value && change.to_value
                          ? `${change.from_value}${change.from_unit} → ${change.to_value}${change.to_unit}`
                          : change.notes
                      }
                    />
                    <ListItemSecondaryAction>
                      <IconButton
                        edge="end"
                        onClick={() => handleRemoveEquipmentChange(index)}
                        size="small"
                      >
                        <DeleteIcon />
                      </IconButton>
                    </ListItemSecondaryAction>
                  </ListItem>
                ))}
              </List>
            )}

            {/* Add new change form */}
            <Box
              sx={{
                p: 2,
                border: "1px dashed",
                borderColor: "divider",
                borderRadius: 1,
              }}
            >
              <Typography variant="caption" color="text.secondary" gutterBottom>
                Add Equipment Change
              </Typography>
              <Box
                sx={{ display: "flex", flexDirection: "column", gap: 1, mt: 1 }}
              >
                <FormControl size="small">
                  <InputLabel>Action</InputLabel>
                  <Select
                    value={newEquipmentChange.action}
                    onChange={(e) =>
                      setNewEquipmentChange({
                        ...newEquipmentChange,
                        action: e.target.value,
                      })
                    }
                    label="Action"
                  >
                    <MenuItem value="add">Add</MenuItem>
                    <MenuItem value="resize">Resize</MenuItem>
                    <MenuItem value="replace">Replace</MenuItem>
                    <MenuItem value="retune">Retune</MenuItem>
                  </Select>
                </FormControl>
                <TextField
                  size="small"
                  label="Equipment ID/Name"
                  value={newEquipmentChange.ref_id}
                  onChange={(e) =>
                    setNewEquipmentChange({
                      ...newEquipmentChange,
                      ref_id: e.target.value,
                    })
                  }
                />
                <Box sx={{ display: "flex", gap: 1 }}>
                  <TextField
                    size="small"
                    label="From Value"
                    type="number"
                    value={newEquipmentChange.from_value}
                    onChange={(e) =>
                      setNewEquipmentChange({
                        ...newEquipmentChange,
                        from_value: e.target.value,
                      })
                    }
                  />
                  <TextField
                    size="small"
                    label="Unit"
                    value={newEquipmentChange.from_unit}
                    onChange={(e) =>
                      setNewEquipmentChange({
                        ...newEquipmentChange,
                        from_unit: e.target.value,
                      })
                    }
                  />
                </Box>
                <Box sx={{ display: "flex", gap: 1 }}>
                  <TextField
                    size="small"
                    label="To Value"
                    type="number"
                    value={newEquipmentChange.to_value}
                    onChange={(e) =>
                      setNewEquipmentChange({
                        ...newEquipmentChange,
                        to_value: e.target.value,
                      })
                    }
                  />
                  <TextField
                    size="small"
                    label="Unit"
                    value={newEquipmentChange.to_unit}
                    onChange={(e) =>
                      setNewEquipmentChange({
                        ...newEquipmentChange,
                        to_unit: e.target.value,
                      })
                    }
                  />
                </Box>
                <TextField
                  size="small"
                  label="Notes"
                  value={newEquipmentChange.notes}
                  onChange={(e) =>
                    setNewEquipmentChange({
                      ...newEquipmentChange,
                      notes: e.target.value,
                    })
                  }
                />
                <Button
                  startIcon={<AddIcon />}
                  onClick={handleAddEquipmentChange}
                  disabled={!newEquipmentChange.ref_id}
                  size="small"
                >
                  Add Change
                </Button>
              </Box>
            </Box>
          </Box>
        );

      case 3:
        return (
          <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
            <Typography variant="h6" gutterBottom>
              Review Option
            </Typography>

            <Box>
              <Typography variant="subtitle2" color="text.secondary">
                Name
              </Typography>
              <Typography variant="body1">
                {formData.name || "(no name)"}
              </Typography>
            </Box>

            {formData.description && (
              <Box>
                <Typography variant="subtitle2" color="text.secondary">
                  Description
                </Typography>
                <Typography variant="body1">{formData.description}</Typography>
              </Box>
            )}

            <Divider />

            <Box>
              <Typography variant="subtitle2" color="text.secondary">
                Estimates
              </Typography>
              {formData.capex_value && (
                <Typography variant="body2">
                  CAPEX: ${parseFloat(formData.capex_value).toLocaleString()}
                </Typography>
              )}
              {formData.opex_value && (
                <Typography variant="body2">
                  OPEX/Year: ${parseFloat(formData.opex_value).toLocaleString()}
                </Typography>
              )}
              {formData.timeline_value && (
                <Typography variant="body2">
                  Timeline: {formData.timeline_value} {formData.timeline_unit}
                </Typography>
              )}
              <Typography variant="body2">
                Risk: {formData.risk_level}
              </Typography>
            </Box>

            <Divider />

            <Box>
              <Typography variant="subtitle2" color="text.secondary">
                Changes
              </Typography>
              <Typography variant="body2">
                {formData.equipment_changes.length} equipment change(s)
              </Typography>
            </Box>
          </Box>
        );

      default:
        return null;
    }
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>Create New Option</DialogTitle>
      <DialogContent>
        <Box sx={{ pt: 2 }}>
          <Stepper activeStep={activeStep} sx={{ mb: 3 }}>
            {steps.map((label) => (
              <Step key={label}>
                <StepLabel>{label}</StepLabel>
              </Step>
            ))}
          </Stepper>

          {renderStepContent(activeStep)}
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Box sx={{ flex: 1 }} />
        {activeStep > 0 && <Button onClick={handleBack}>Back</Button>}
        {activeStep < steps.length - 1 ? (
          <Button
            variant="contained"
            onClick={handleNext}
            disabled={activeStep === 0 && !formData.name}
          >
            Next
          </Button>
        ) : (
          <Button
            variant="contained"
            onClick={handleSubmit}
            disabled={!formData.name}
          >
            Create Option
          </Button>
        )}
      </DialogActions>
    </Dialog>
  );
};

export default CreateOptionDialog;
