import React, { useEffect, useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import {
  Box,
  Typography,
  Paper,
  Divider,
  Button,
  Alert,
  CircularProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
  TextField,
} from "@mui/material";
import {
  Delete as DeleteIcon,
  Person as PersonIcon,
  Warning as WarningIcon,
} from "@mui/icons-material";
import { selectUser } from "../../redux/authSlice";
import { deleteAllUserData } from "../../redux/projectsSlice";

/**
 * Settings page component.
 * 
 * Displays user information and provides option to delete all user data.
 */
const Settings: React.FC = () => {
  const dispatch = useDispatch();
  const user = useSelector(selectUser);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [confirmationText, setConfirmationText] = useState("");
  const [deleting, setDeleting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const requiredConfirmationText = "DELETE ALL DATA";

  /**
   * Handle opening delete dialog
   */
  const handleOpenDeleteDialog = () => {
    setDeleteDialogOpen(true);
    setConfirmationText("");
    setError(null);
    setSuccess(false);
  };

  /**
   * Handle closing delete dialog
   */
  const handleCloseDeleteDialog = () => {
    if (!deleting) {
      setDeleteDialogOpen(false);
      setConfirmationText("");
      setError(null);
    }
  };

  /**
   * Handle deleting all user data
   */
  const handleDeleteAllData = async () => {
    if (confirmationText !== requiredConfirmationText) {
      setError(`Please type "${requiredConfirmationText}" to confirm`);
      return;
    }

    setDeleting(true);
    setError(null);
    setSuccess(false);

    try {
      const result = await dispatch(deleteAllUserData() as any);
      if (deleteAllUserData.fulfilled.match(result)) {
        setSuccess(true);
        setDeleteDialogOpen(false);
        // Optionally redirect to login or home page
        // navigate("/");
      } else if (deleteAllUserData.rejected.match(result)) {
        setError(result.payload as string || "Failed to delete all data");
      }
    } catch (err) {
      setError("An unexpected error occurred");
    } finally {
      setDeleting(false);
    }
  };

  return (
    <Box sx={{ maxWidth: 800, mx: "auto" }}>
      <Typography variant="h4" component="h1" gutterBottom>
        Settings
      </Typography>

      {/* User Information Section */}
      <Paper elevation={1} sx={{ p: 3, mb: 3 }}>
        <Box sx={{ display: "flex", alignItems: "center", mb: 2 }}>
          <PersonIcon sx={{ mr: 1, color: "primary.main" }} />
          <Typography variant="h6">User Information</Typography>
        </Box>
        <Divider sx={{ mb: 2 }} />
        {user ? (
          <Box>
            <Box sx={{ mb: 2 }}>
              <Typography variant="body2" color="text.secondary">
                Name
              </Typography>
              <Typography variant="body1">{user.name || "N/A"}</Typography>
            </Box>
            <Box sx={{ mb: 2 }}>
              <Typography variant="body2" color="text.secondary">
                Email
              </Typography>
              <Typography variant="body1">{user.email || "N/A"}</Typography>
            </Box>
            {user.org_name && (
              <Box sx={{ mb: 2 }}>
                <Typography variant="body2" color="text.secondary">
                  Organization
                </Typography>
                <Typography variant="body1">{user.org_name}</Typography>
              </Box>
            )}
            {user.user_id && (
              <Box>
                <Typography variant="body2" color="text.secondary">
                  User ID
                </Typography>
                <Typography variant="body1" sx={{ fontFamily: "monospace" }}>
                  {user.user_id}
                </Typography>
              </Box>
            )}
          </Box>
        ) : (
          <Typography variant="body2" color="text.secondary">
            Loading user information...
          </Typography>
        )}
      </Paper>

      {/* Delete All Data Section */}
      <Paper elevation={1} sx={{ p: 3 }}>
        <Box sx={{ display: "flex", alignItems: "center", mb: 2 }}>
          <WarningIcon sx={{ mr: 1, color: "error.main" }} />
          <Typography variant="h6" color="error">
            Danger Zone
          </Typography>
        </Box>
        <Divider sx={{ mb: 2 }} />
        <Box>
          <Typography variant="body1" gutterBottom>
            Delete All Your Data
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            This action will permanently delete all your projects, scenarios, and
            uploaded files. This action cannot be undone.
          </Typography>
          <Button
            variant="outlined"
            color="error"
            startIcon={<DeleteIcon />}
            onClick={handleOpenDeleteDialog}
          >
            Delete All Data
          </Button>
        </Box>
      </Paper>

      {/* Delete Confirmation Dialog */}
      <Dialog
        open={deleteDialogOpen}
        onClose={handleCloseDeleteDialog}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Delete All Your Data</DialogTitle>
        <DialogContent>
          <Alert severity="warning" sx={{ mb: 2 }}>
            <Typography variant="body2" fontWeight="bold">
              Warning: This action cannot be undone!
            </Typography>
            <Typography variant="body2">
              This will permanently delete:
            </Typography>
            <Box component="ul" sx={{ pl: 2, mt: 1, mb: 0 }}>
              <li>All your projects</li>
              <li>All your scenarios</li>
              <li>All derived data</li>
              <li>All uploaded files</li>
              <li>All cost estimate reports</li>
            </Box>
          </Alert>
          <DialogContentText>
            To confirm, please type <strong>{requiredConfirmationText}</strong> in
            the field below:
          </DialogContentText>
          <TextField
            autoFocus
            margin="dense"
            label="Confirmation"
            type="text"
            fullWidth
            variant="outlined"
            value={confirmationText}
            onChange={(e) => setConfirmationText(e.target.value)}
            disabled={deleting}
            error={!!error && confirmationText !== requiredConfirmationText}
            helperText={
              error && confirmationText !== requiredConfirmationText
                ? error
                : undefined
            }
            sx={{ mt: 2 }}
          />
          {success && (
            <Alert severity="success" sx={{ mt: 2 }}>
              All data has been deleted successfully.
            </Alert>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDeleteDialog} disabled={deleting}>
            Cancel
          </Button>
          <Button
            onClick={handleDeleteAllData}
            color="error"
            variant="contained"
            disabled={
              deleting ||
              confirmationText !== requiredConfirmationText ||
              success
            }
            startIcon={deleting ? <CircularProgress size={20} /> : <DeleteIcon />}
          >
            {deleting ? "Deleting..." : "Delete All Data"}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default Settings;

