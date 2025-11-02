import React, { useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import {
  Box,
  Typography,
  Paper,
  Grid,
  Divider,
  Button,
  Avatar,
  Chip,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
  Snackbar,
  CircularProgress,
} from "@mui/material";
import {
  Person as PersonIcon,
  AdminPanelSettings as AdminIcon,
  DeleteSweep as ClearDataIcon,
  Warning as WarningIcon,
} from "@mui/icons-material";

// Import from authSlice instead
import {
  selectUser,
  selectFetchingUser,
  selectAuthError,
} from "../../redux/authSlice";

const API_BASE_URL = "http://localhost:8000/api/v1";

const Settings = () => {
  // Use authSlice selectors
  const userInfo = useSelector(selectUser);
  const loading = useSelector(selectFetchingUser);
  const error = useSelector(selectAuthError);
  console.log("User Info:", userInfo);
  // State for clear data functionality
  const [clearDataDialog, setClearDataDialog] = useState(false);
  const [clearingData, setClearingData] = useState(false);
  const [toast, setToast] = useState({
    open: false,
    message: "",
    severity: "success",
  });

  const handleClearAllData = async () => {
    try {
      setClearingData(true);

      const token = localStorage.getItem("access_token");
      if (!token) {
        throw new Error("No authentication token found");
      }

      const response = await fetch(`${API_BASE_URL}/admin/clear_all_data`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(
          errorData.detail || `HTTP error! status: ${response.status}`
        );
      }

      const result = await response.json();

      setToast({
        open: true,
        message: result.message || "All data cleared successfully",
        severity: "success",
      });

      console.log("🗑️ ADMIN ACTION: All data cleared successfully", result);
    } catch (error) {
      console.error("Error clearing data:", error);
      setToast({
        open: true,
        message: `Failed to clear data: ${error.message}`,
        severity: "error",
      });
    } finally {
      setClearingData(false);
      setClearDataDialog(false);
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return "N/A";
    try {
      return new Date(dateString).toLocaleDateString("en-US", {
        year: "numeric",
        month: "long",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      });
    } catch {
      return "Invalid Date";
    }
  };

  if (loading) {
    return (
      <Box
        sx={{
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          minHeight: 400,
        }}
      >
        <CircularProgress />
        <Typography sx={{ ml: 2 }}>Loading user information...</Typography>
      </Box>
    );
  }

  if (error) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error">Error loading settings: {error}</Alert>
      </Box>
    );
  }

  if (!userInfo) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="warning">
          No user information available. Please try refreshing the page.
        </Alert>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom fontWeight="bold">
        Settings
      </Typography>
      <Typography variant="body1" color="text.secondary" paragraph>
        Manage your account settings and preferences.
      </Typography>

      <Grid container spacing={3}>
        {/* User Profile Section */}
        <Grid size={{ xs: 12, md: 4 }}>
          <Paper sx={{ p: 3 }}>
            <Box sx={{ display: "flex", alignItems: "center", mb: 3 }}>
              <Avatar
                sx={{ width: 60, height: 60, mr: 2, bgcolor: "primary.main" }}
              >
                <PersonIcon sx={{ fontSize: 30 }} />
              </Avatar>
              <Box>
                <Typography variant="h5" fontWeight="bold">
                  {userInfo.name || "User"}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {userInfo.email}
                </Typography>
                <Box sx={{ mt: 1 }}>
                  {userInfo.is_admin ? (
                    <Chip
                      icon={<AdminIcon />}
                      label="Administrator"
                      color="error"
                      variant="outlined"
                      size="small"
                    />
                  ) : (
                    <Chip
                      icon={<PersonIcon />}
                      label="User"
                      color="primary"
                      variant="outlined"
                      size="small"
                    />
                  )}
                </Box>
              </Box>
            </Box>

            <Divider sx={{ my: 2 }} />

            <Grid container spacing={2}>
              <Grid size={{ xs: 6 }}>
                <Typography variant="body2" color="text.secondary">
                  Account Created
                </Typography>
                <Typography variant="body1">
                  {formatDate(userInfo.created_at)}
                </Typography>
              </Grid>
              <Grid size={{ xs: 6 }}>
                <Typography variant="body2" color="text.secondary">
                  Account Status
                </Typography>
                <Chip
                  label={userInfo.active ? "Active" : "Inactive"}
                  color={userInfo.active ? "success" : "error"}
                  size="small"
                />
              </Grid>
              <Grid size={{ xs: 6 }}>
                <Typography variant="body2" color="text.secondary">
                  Role
                </Typography>
                <Typography variant="body1">
                  {userInfo.is_admin ? "System Administrator" : "Standard User"}
                </Typography>
              </Grid>
            </Grid>
          </Paper>
        </Grid>

        {/* Admin Actions Section - Only show if user is admin */}
        {userInfo?.is_admin && (
          <Grid size={{ xs: 12, md: 4 }}>
            <Paper sx={{ p: 3, bgcolor: "error.50" }}>
              <Box sx={{ display: "flex", alignItems: "center", mb: 2 }}>
                <AdminIcon sx={{ mr: 1, color: "error.main" }} />
                <Typography variant="h6" color="error.main" fontWeight="bold">
                  Admin Actions
                </Typography>
              </Box>

              <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                Dangerous administrative actions. Use with caution.
              </Typography>

              <Button
                fullWidth
                variant="outlined"
                color="error"
                startIcon={<ClearDataIcon />}
                onClick={() => setClearDataDialog(true)}
                disabled={clearingData}
                sx={{ mb: 2 }}
              >
                {clearingData ? "Clearing..." : "Clear All Data"}
              </Button>
            </Paper>
          </Grid>
        )}
      </Grid>

      {/* Clear Data Confirmation Dialog */}
      <Dialog
        open={clearDataDialog}
        onClose={() => setClearDataDialog(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle sx={{ display: "flex", alignItems: "center" }}>
          <WarningIcon sx={{ mr: 1, color: "error.main" }} />
          Clear All Data
        </DialogTitle>
        <DialogContent>
          <DialogContentText>
            <strong>Warning:</strong> This action will permanently delete ALL
            data including:
          </DialogContentText>
          <Box component="ul" sx={{ mt: 2, mb: 2 }}>
            <li>All projects and documents</li>
            <li>All uploaded files and extracted data</li>
            <li>All user-generated content</li>
            <li>All processing history</li>
          </Box>
          <DialogContentText color="error">
            This action cannot be undone. Are you absolutely sure?
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button
            onClick={() => setClearDataDialog(false)}
            disabled={clearingData}
          >
            Cancel
          </Button>
          <Button
            onClick={handleClearAllData}
            color="error"
            variant="contained"
            disabled={clearingData}
            startIcon={
              clearingData ? <CircularProgress size={16} /> : <ClearDataIcon />
            }
          >
            {clearingData ? "Clearing..." : "Clear All Data"}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Toast Notifications */}
      <Snackbar
        open={toast.open}
        autoHideDuration={6000}
        onClose={() => setToast((prev) => ({ ...prev, open: false }))}
        anchorOrigin={{ vertical: "top", horizontal: "right" }}
      >
        <Alert
          onClose={() => setToast((prev) => ({ ...prev, open: false }))}
          severity={toast.severity}
          sx={{ width: "100%" }}
        >
          {toast.message}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default Settings;
