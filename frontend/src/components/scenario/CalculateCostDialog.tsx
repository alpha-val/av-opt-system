import React, { useState } from "react";
import {
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions,
    Button,
    TextField,
    CircularProgress,
    Box,
    } from "@mui/material";

    interface CalculateCostDialogProps {
        open: boolean;
        onClose: () => void;
            onCalculate: (data: {
                name: string;
                description?: string;
                topK: number;
        }) => void;
        calculating: boolean;
        defaultName?: string;
}

/**
 * Dialog for initiating cost calculation
 * Allows user to name the cost estimate and configure parameters
 */
const CalculateCostDialog: React.FC<CalculateCostDialogProps> = ({
    open,
    onClose,
    onCalculate,
    calculating,
    defaultName = "",
    }) => {
    const [name, setName] = useState<string>(defaultName);
    const [description, setDescription] = useState<string>("");
    const [topK, setTopK] = useState<number>(3);

    // Reset form when dialog opens
    React.useEffect(() => {
    if (open) {
        setName(defaultName);
        setDescription("");
        setTopK(3);
    }
    }, [open, defaultName]);

    const handleSubmit = () => {
        if (!name.trim()) {
            return;
        }

        console.log('! ! ! ! ! \n\n Handling submit:', name, description, topK);
        onCalculate({
            name: name.trim(),
            description: description.trim() || undefined,
            topK,
        });
    };

    return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
        <DialogTitle>Calculate Cost Estimate</DialogTitle>
        <DialogContent>
        <Box sx={{ pt: 2, display: "flex", flexDirection: "column", gap: 2 }}>
            <TextField
            label="Name"
            fullWidth
            required
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Enter a name for this cost estimate"
            disabled={calculating}
            />
            <TextField
            label="Description (Optional)"
            fullWidth
            multiline
            rows={3}
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Optional description"
            disabled={calculating}
            />
            <TextField
            label="Top K Matches"
            type="number"
            fullWidth
            value={topK}
            onChange={(e) =>
                setTopK(Math.max(1, parseInt(e.target.value) || 3))
            }
            helperText="Number of top matching tabular entities to return per base entity (default: 3)"
            disabled={calculating}
            inputProps={{ min: 1, max: 10 }}
            />
        </Box>
        </DialogContent>
        <DialogActions>
        <Button onClick={onClose} disabled={calculating}>
            Cancel
        </Button>
        <Button
            onClick={handleSubmit}
            variant="contained"
            disabled={!name.trim() || calculating}
            startIcon={calculating && <CircularProgress size={20} />}
        >
            {calculating ? "Calculating..." : "Calculate"}
        </Button>
        </DialogActions>
    </Dialog>
    );
};

export default CalculateCostDialog;
