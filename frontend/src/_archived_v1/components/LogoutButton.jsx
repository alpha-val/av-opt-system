import React, { useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import {
    Button,
    IconButton,
    Tooltip,
    Dialog,
    DialogTitle,
    DialogContent,
    DialogContentText,
    DialogActions,
    Box,
    Typography,
    Avatar,
    Divider
} from '@mui/material';
import {
    Logout,
    ExitToApp,
    Person
} from '@mui/icons-material';
import {
    logoutUser,
    selectUser,
    selectAuthLoading
} from '../redux/authSlice';

const LogoutButton = ({ variant = 'text', showConfirmDialog = true, collapsed = false }) => {
    const dispatch = useDispatch();
    const user = useSelector(selectUser);
    const loading = useSelector(selectAuthLoading);
    const [confirmOpen, setConfirmOpen] = useState(false);

    const handleLogoutClick = () => {
        if (showConfirmDialog) {
            setConfirmOpen(true);
        } else {
            handleConfirmLogout();
        }
    };

    const handleConfirmLogout = () => {
        setConfirmOpen(false);
        dispatch(logoutUser());
    };

    const handleCancelLogout = () => {
        setConfirmOpen(false);
    };

    // Icon variant for collapsed sidebar
    if (variant === 'icon' || collapsed) {
        return (
            <>
                <Tooltip title={`Logout${user?.name ? ` (${user.name})` : ''}`}>
                    <IconButton
                        onClick={handleLogoutClick}
                        disabled={loading}
                        sx={{
                            color: 'text.secondary',
                            '&:hover': {
                                color: 'error.main',
                                backgroundColor: 'error.light',
                                '& .MuiSvgIcon-root': {
                                    transform: 'scale(1.1)',
                                },
                            },
                            transition: 'all 0.2s ease-in-out',
                        }}
                    >
                        <ExitToApp />
                    </IconButton>
                </Tooltip>

                {/* Confirmation Dialog */}
                {showConfirmDialog && (
                    <Dialog
                        open={confirmOpen}
                        onClose={handleCancelLogout}
                        aria-labelledby="logout-dialog-title"
                        aria-describedby="logout-dialog-description"
                    >
                        <DialogTitle id="logout-dialog-title">
                            Confirm Logout
                        </DialogTitle>
                        <DialogContent>
                            <DialogContentText id="logout-dialog-description">
                                Are you sure you want to logout? You will need to sign in again to access your account.
                            </DialogContentText>
                            {user && (
                                <Box sx={{ mt: 2, p: 2, bgcolor: 'grey.50', borderRadius: 1 }}>
                                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                        <Avatar sx={{ width: 32, height: 32 }}>
                                            <Person />
                                        </Avatar>
                                        <Box>
                                            <Typography variant="subtitle2">{user.name}</Typography>
                                            <Typography variant="caption" color="text.secondary">
                                                {user.email}
                                            </Typography>
                                        </Box>
                                    </Box>
                                </Box>
                            )}
                        </DialogContent>
                        <DialogActions>
                            <Button onClick={handleCancelLogout} color="inherit">
                                Cancel
                            </Button>
                            <Button
                                onClick={handleConfirmLogout}
                                color="error"
                                variant="contained"
                                disabled={loading}
                            >
                                {loading ? 'Logging out...' : 'Logout'}
                            </Button>
                        </DialogActions>
                    </Dialog>
                )}
            </>
        );
    }

    // Full button variant for expanded sidebar or other uses
    return (
        <>
            <Button
                onClick={handleLogoutClick}
                startIcon={<Logout />}
                variant={variant}
                color="error"
                disabled={loading}
                fullWidth={variant === 'contained'}
                sx={{
                    justifyContent: 'flex-start',
                    textTransform: 'none',
                    '&:hover': {
                        backgroundColor: 'error.light',
                        color: 'error.contrastText',
                    },
                }}
            >
                {loading ? 'Logging out...' : 'Logout'}
            </Button>

            {/* Confirmation Dialog */}
            {showConfirmDialog && (
                <Dialog
                    open={confirmOpen}
                    onClose={handleCancelLogout}
                    aria-labelledby="logout-dialog-title"
                    aria-describedby="logout-dialog-description"
                    maxWidth="sm"
                    fullWidth
                >
                    <DialogTitle id="logout-dialog-title">
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            <ExitToApp color="error" />
                            Confirm Logout
                        </Box>
                    </DialogTitle>

                    <DialogContent>
                        <DialogContentText id="logout-dialog-description" sx={{ mb: 2 }}>
                            Are you sure you want to logout? You will need to sign in again to access your account.
                        </DialogContentText>

                        {user && (
                            <>
                                <Divider sx={{ my: 2 }} />
                                <Box sx={{
                                    p: 2,
                                    bgcolor: 'background.paper',
                                    border: 1,
                                    borderColor: 'divider',
                                    borderRadius: 1
                                }}>
                                    <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                                        Current User:
                                    </Typography>
                                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                                        <Avatar sx={{ width: 40, height: 40, bgcolor: 'primary.main' }}>
                                            <Person />
                                        </Avatar>
                                        <Box>
                                            <Typography variant="subtitle1" fontWeight="medium">
                                                {user.name}
                                            </Typography>
                                            <Typography variant="body2" color="text.secondary">
                                                {user.email}
                                            </Typography>
                                            {user.org_name && (
                                                <Typography variant="caption" color="text.secondary">
                                                    {user.org_name}
                                                </Typography>
                                            )}
                                        </Box>
                                    </Box>
                                </Box>
                            </>
                        )}
                    </DialogContent>

                    <DialogActions sx={{ p: 2 }}>
                        <Button
                            onClick={handleCancelLogout}
                            color="inherit"
                            variant="outlined"
                        >
                            Cancel
                        </Button>
                        <Button
                            onClick={handleConfirmLogout}
                            color="error"
                            variant="contained"
                            disabled={loading}
                            startIcon={<Logout />}
                        >
                            {loading ? 'Logging out...' : 'Logout'}
                        </Button>
                    </DialogActions>
                </Dialog>
            )}
        </>
    );
};

export default LogoutButton;