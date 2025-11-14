import React, { memo, useState, useEffect, useRef } from "react";
import {
  Box,
  Card,
  CardContent,
  TextField,
  MenuItem,
  Select,
  FormControl,
  InputLabel,
  Button,
  Alert,
} from "@mui/material";

const OBJECTIVE_TYPES = [
  "increase production",
  "reduce capex",
  "reduce wastage",
  "improve efficiency",
  "reduce opex",
  "optimize capacity",
];

interface ObjectiveDetailsFormProps {
  objectiveForm: {
    type: string;
    targetValue: string;
    targetType: "%" | "$";
    description: string;
  };
  extractionScope: "exact" | "with_relationships" | "with_context";
  onChange: (field: string, value: string | number) => void;
  onExtractionScopeChange: (value: "exact" | "with_relationships" | "with_context") => void;
  errors?: string | null;
  updating?: boolean;
  scenarioId: string;
  onSave: (data?: { localDescription: string; objectiveForm: ObjectiveDetailsFormProps['objectiveForm'] }) => void;
}

/**
 * Objective Details Form Component
 * 
 * Displays form fields for objective type, target, and description.
 * Includes save button and error handling.
 */
const ObjectiveDetailsForm: React.FC<ObjectiveDetailsFormProps> = memo(({
  objectiveForm,
  extractionScope,
  onChange,
  onExtractionScopeChange,
  errors,
  updating = false,
  scenarioId,
  onSave,
}) => {
  // Local state for description to prevent re-renders while typing
  const [localDescription, setLocalDescription] = useState(objectiveForm.description);
  const initializedRef = useRef<string | null>(null);
  const lastDescriptionRef = useRef<string>(objectiveForm.description);

  // Initialize local description from props when scenario changes or when data loads
  useEffect(() => {
    // Initialize when scenarioId changes (new scenario loaded)
    if (scenarioId !== initializedRef.current) {
      setLocalDescription(objectiveForm.description);
      initializedRef.current = scenarioId;
      lastDescriptionRef.current = objectiveForm.description;
    }
    // Also sync when objectiveForm.description changes from empty to populated
    // This handles the case where component mounts before scenario data loads
    else if (
      objectiveForm.description !== lastDescriptionRef.current &&
      objectiveForm.description !== localDescription
    ) {
      setLocalDescription(objectiveForm.description);
      lastDescriptionRef.current = objectiveForm.description;
    }
  }, [scenarioId, objectiveForm.description, localDescription]);

  // Handle description change locally (doesn't trigger parent update)
  const handleDescriptionChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setLocalDescription(e.target.value);
  };

  // Handle save - update parent with all values including description
  const handleSave = () => {
    // Update description in parent before saving
    onChange("description", localDescription);
    // Call the parent's save handler with updated data
    onSave({localDescription, objectiveForm: {...objectiveForm, description: localDescription}});
  };

  return (
    <Card>
      <CardContent>
        {/* {errors && (
          <Alert
            severity="error"
            sx={{ mb: 2 }}
          >
            {errors}
          </Alert>
        )} */}

        <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
          {/* Global Objective Type */}
          <FormControl fullWidth required>
            <InputLabel>Global Objective Type</InputLabel>
            <Select
              value={objectiveForm.type}
              onChange={(e) => onChange("type", e.target.value)}
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
          <Box
            sx={{
              display: "flex",
              gap: 1,
              alignItems: "flex-start",
            }}
          >
            <TextField
              label="Global Objective Target"
              required
              type="number"
              value={objectiveForm.targetValue}
              onChange={(e) => onChange("targetValue", e.target.value)}
              sx={{ flex: 1 }}
            />
            <FormControl sx={{ minWidth: 80 }}>
              <Select
                value={objectiveForm.targetType}
                onChange={(e) => onChange("targetType", e.target.value)}
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
            value={localDescription}
            onChange={handleDescriptionChange}
            inputProps={{ maxLength: 500 }}
            helperText={`${localDescription.length}/500 characters`}
          />

          {/* Extraction Scope */}
          <FormControl fullWidth>
            <InputLabel>Extraction Scope</InputLabel>
            <Select
              value={extractionScope}
              onChange={(e) =>
                onExtractionScopeChange(
                  e.target.value as
                    | "exact"
                    | "with_relationships"
                    | "with_context"
                )
              }
              label="Extraction Scope"
            >
              <MenuItem value="exact">
                Exact (only specified entities)
              </MenuItem>
              <MenuItem value="with_relationships">
                With Relationships (entities + direct relationships)
              </MenuItem>
              <MenuItem value="with_context">
                With Context (entities + related context entities)
              </MenuItem>
            </Select>
          </FormControl>

          <Box
            sx={{
              display: "flex",
              justifyContent: "flex-end",
              mt: 2,
            }}
          >
            <Button
              variant="outlined"
              onClick={handleSave}
              disabled={updating}
            >
              {updating ? "Saving..." : "Save Objective Details"}
            </Button>
          </Box>
        </Box>
      </CardContent>
    </Card>
  );
});

ObjectiveDetailsForm.displayName = "ObjectiveDetailsForm";

export default ObjectiveDetailsForm;

