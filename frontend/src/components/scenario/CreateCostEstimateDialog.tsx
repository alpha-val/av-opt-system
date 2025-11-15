import React, { memo, useRef, useEffect, useState } from "react";
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  Box,
} from "@mui/material";
import { CostEstimateCreate } from "../../types/api";

interface CreateCostEstimateDialogProps {
  open: boolean;
  onClose: () => void;
  onCreate: (data: CostEstimateCreate) => void;
  creating: boolean;
  scenarioId: string;
}

/**
 * Create Cost Estimate Dialog Component
 * 
 * Uses useRef for input values to prevent re-renders while typing.
 * Values are read from refs only when the Create button is clicked.
 * Uses minimal state only for character count display (optional).
 */
const CreateCostEstimateDialog: React.FC<CreateCostEstimateDialogProps> = memo(({
  open,
  onClose,
  onCreate,
  creating,
  scenarioId,
}) => {
  const nameInputRef = useRef<HTMLInputElement>(null);
  const descriptionInputRef = useRef<HTMLTextAreaElement>(null);
  
  // Minimal state only for character count display (optional - can be removed)
  const [nameLength, setNameLength] = useState(0);
  const [descriptionLength, setDescriptionLength] = useState(0);

  // Reset inputs when dialog opens/closes
  useEffect(() => {
    if (open) {
      // Clear inputs when dialog opens
      if (nameInputRef.current) {
        nameInputRef.current.value = "";
      }
      if (descriptionInputRef.current) {
        descriptionInputRef.current.value = "";
      }
      setNameLength(0);
      setDescriptionLength(0);
      // Focus on name input when dialog opens
      setTimeout(() => {
        nameInputRef.current?.focus();
      }, 100);
    }
  }, [open]);

  const handleCreate = () => {
    const name = nameInputRef.current?.value.trim() || "";
    const description = descriptionInputRef.current?.value.trim() || "";

    if (!name) {
      return;
    }

    const costEstimateData: CostEstimateCreate = {
      name,
      description: description || undefined,
      scenario_id: scenarioId,
    };

    onCreate(costEstimateData);
  };

  const handleClose = () => {
    // Clear inputs when closing
    if (nameInputRef.current) {
      nameInputRef.current.value = "";
    }
    if (descriptionInputRef.current) {
      descriptionInputRef.current.value = "";
    }
    setNameLength(0);
    setDescriptionLength(0);
    onClose();
  };

  // Handle input changes - only update character count, not the input value
  const handleNameInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value || "";
    setNameLength(value.length);
  };

  const handleDescriptionInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const value = e.target.value || "";
    setDescriptionLength(value.length);
  };

  // Check if name is valid (non-empty) - read from ref
  const isNameValid = () => {
    return (nameInputRef.current?.value.trim().length || 0) > 0;
  };

  return (
    <Dialog
      open={open}
      onClose={handleClose}
      maxWidth="sm"
      fullWidth
    >
      <DialogTitle>Create New Cost Estimate</DialogTitle>
      <DialogContent>
        <Box sx={{ display: "flex", flexDirection: "column", gap: 2, pt: 1 }}>
          <TextField
            inputRef={nameInputRef}
            label="Cost Estimate Name"
            required
            fullWidth
            defaultValue=""
            inputProps={{ maxLength: 200 }}
            helperText={`${nameLength}/200 characters`}
            onChange={handleNameInput}
          />
          <TextField
            inputRef={descriptionInputRef}
            label="Description (optional)"
            fullWidth
            multiline
            rows={3}
            defaultValue=""
            inputProps={{ maxLength: 500 }}
            helperText={`${descriptionLength}/500 characters`}
            onChange={handleDescriptionInput}
          />
        </Box>
      </DialogContent>
      <DialogActions>
        <Button
          onClick={handleClose}
          disabled={creating}
        >
          Cancel
        </Button>
        <Button
          onClick={handleCreate}
          variant="contained"
          disabled={creating || !isNameValid()}
        >
          {creating ? "Creating..." : "Create"}
        </Button>
      </DialogActions>
    </Dialog>
  );
});

CreateCostEstimateDialog.displayName = "CreateCostEstimateDialog";

export default CreateCostEstimateDialog;

