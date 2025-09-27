import React, { useState, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useNavigate } from 'react-router-dom';
import {
    Box,
    Card,
    CardContent,
    TextField,
    Button,
    Typography,
    Tabs,
    Tab,
    Alert,
    CircularProgress,
    InputAdornment,
    IconButton,
    Divider,
    useTheme,
    alpha,
} from '@mui/material';
import {
    Visibility,
    VisibilityOff,
    PersonAdd,
    Login,
    Email,
    Person,
    Business,
} from '@mui/icons-material';
import {
    registerUser,
    loginUser,
    selectRegistering,
    selectLoggingIn,
    selectAuthError,
    selectIsAuthenticated,
    clearError,
} from '../redux/authSlice';

function TabPanel({ children, value, index, ...other }) {
    return (
        <div
            role="tabpanel"
            hidden={value !== index}
            id={`auth-tabpanel-${index}`}
            aria-labelledby={`auth-tab-${index}`}
            {...other}
        >
            {value === index && <Box sx={{ pt: 3 }}>{children}</Box>}
        </div>
    );
}

const UserAuth = () => {
    const theme = useTheme();
    const dispatch = useDispatch();
    const navigate = useNavigate();

    // Redux state
    const registering = useSelector(selectRegistering);
    const loggingIn = useSelector(selectLoggingIn);
    const error = useSelector(selectAuthError);
    const isAuthenticated = useSelector(selectIsAuthenticated);

    // Local state
    const [tabValue, setTabValue] = useState(0);
    const [showPassword, setShowPassword] = useState(false);
    const [showConfirmPassword, setShowConfirmPassword] = useState(false);

    // Form state
    const [loginForm, setLoginForm] = useState({
        email: '',
        password: '',
    });

    const [registerForm, setRegisterForm] = useState({
        name: '',
        email: '',
        password: '',
        confirmPassword: '',
        org_name: 'alphaval',
        org_id: 'org_12345',
    });

    // Validation state
    const [formErrors, setFormErrors] = useState({});

    // Redirect if authenticated
    useEffect(() => {
        if (isAuthenticated) {
            navigate('/dashboard'); // Adjust route as needed
        }
    }, [isAuthenticated, navigate]);

    // Clear errors when switching tabs
    useEffect(() => {
        dispatch(clearError());
        setFormErrors({});
    }, [tabValue, dispatch]);

    const handleTabChange = (event, newValue) => {
        setTabValue(newValue);
    };

    const handleTogglePasswordVisibility = () => {
        setShowPassword(!showPassword);
    };

    const handleToggleConfirmPasswordVisibility = () => {
        setShowConfirmPassword(!showConfirmPassword);
    };

    // Validation functions
    const validateEmail = (email) => {
        const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return re.test(email);
    };

    const validateLoginForm = () => {
        const errors = {};

        if (!loginForm.email) {
            errors.email = 'Email is required';
        } else if (!validateEmail(loginForm.email)) {
            errors.email = 'Please enter a valid email';
        }

        if (!loginForm.password) {
            errors.password = 'Password is required';
        }

        setFormErrors(errors);
        return Object.keys(errors).length === 0;
    };

    const validateRegisterForm = () => {
        const errors = {};

        if (!registerForm.name) {
            errors.name = 'Name is required';
        }

        if (!registerForm.email) {
            errors.email = 'Email is required';
        } else if (!validateEmail(registerForm.email)) {
            errors.email = 'Please enter a valid email';
        }

        if (!registerForm.password) {
            errors.password = 'Password is required';
        } else if (registerForm.password.length < 6) {
            errors.password = 'Password must be at least 6 characters';
        }

        if (!registerForm.confirmPassword) {
            errors.confirmPassword = 'Please confirm your password';
        } else if (registerForm.password !== registerForm.confirmPassword) {
            errors.confirmPassword = 'Passwords do not match';
        }

        if (!registerForm.org_name) {
            errors.org_name = 'Organization name is required';
        }

        setFormErrors(errors);
        return Object.keys(errors).length === 0;
    };

    const handleLogin = async (e) => {
        e.preventDefault();

        if (!validateLoginForm()) {
            return;
        }

        try {
            await dispatch(loginUser(loginForm)).unwrap();
            // Navigation will be handled by useEffect
        } catch (error) {
            // Error is handled by Redux
            console.error('Login failed:', error);
        }
    };

    const handleRegister = async (e) => {
        e.preventDefault();

        if (!validateRegisterForm()) {
            return;
        }

        const { confirmPassword, ...userData } = registerForm;

        try {
            await dispatch(registerUser(userData)).unwrap();
            // Navigation will be handled by useEffect
        } catch (error) {
            // Error is handled by Redux
            console.error('Registration failed:', error);
        }
    };

    const handleLoginFormChange = (field) => (event) => {
        setLoginForm({
            ...loginForm,
            [field]: event.target.value,
        });

        // Clear field-specific errors
        if (formErrors[field]) {
            setFormErrors({
                ...formErrors,
                [field]: null,
            });
        }
    };

    const handleRegisterFormChange = (field) => (event) => {
        setRegisterForm({
            ...registerForm,
            [field]: event.target.value,
        });

        // Clear field-specific errors
        if (formErrors[field]) {
            setFormErrors({
                ...formErrors,
                [field]: null,
            });
        }
    };

    return (
        <Box
            sx={{
                minHeight: '100vh',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                background: `linear-gradient(135deg, ${alpha(theme.palette.primary.main, 0.1)} 0%, ${alpha(theme.palette.secondary.main, 0.1)} 100%)`,
                p: 2,
            }}
        >
            <Card
                elevation={24}
                sx={{
                    width: '100%',
                    maxWidth: 480,
                    borderRadius: 3,
                    overflow: 'hidden',
                }}
            >
                <Box
                    sx={{
                        background: `linear-gradient(135deg, ${theme.palette.primary.main} 0%, ${theme.palette.primary.dark} 100%)`,
                        color: 'white',
                        p: 3,
                        textAlign: 'center',
                    }}
                >
                    <Typography variant="h4" fontWeight="bold" gutterBottom>
                        AlphaVal Pro
                    </Typography>
                    <Typography variant="subtitle1" sx={{ opacity: 0.9 }}>
                        Welcome to your mining analytics platform
                    </Typography>
                </Box>

                <CardContent sx={{ p: 0 }}>
                    <Tabs
                        value={tabValue}
                        onChange={handleTabChange}
                        variant="fullWidth"
                        sx={{
                            borderBottom: 1,
                            borderColor: 'divider',
                            '& .MuiTab-root': {
                                py: 2,
                            },
                        }}
                    >
                        <Tab
                            icon={<Login />}
                            label="Sign In"
                            iconPosition="start"
                            sx={{ gap: 1 }}
                        />
                        <Tab
                            icon={<PersonAdd />}
                            label="Sign Up"
                            iconPosition="start"
                            sx={{ gap: 1 }}
                        />
                    </Tabs>

                    {error && (
                        <Alert severity="error" sx={{ m: 3, mb: 0 }}>
                            {error}
                        </Alert>
                    )}

                    <TabPanel value={tabValue} index={0}>
                        <Box component="form" onSubmit={handleLogin} sx={{ p: 3 }}>
                            <TextField
                                fullWidth
                                label="Email Address"
                                type="email"
                                value={loginForm.email}
                                onChange={handleLoginFormChange('email')}
                                error={!!formErrors.email}
                                helperText={formErrors.email}
                                margin="normal"
                                InputProps={{
                                    startAdornment: (
                                        <InputAdornment position="start">
                                            <Email color="action" />
                                        </InputAdornment>
                                    ),
                                }}
                                disabled={loggingIn}
                            />

                            <TextField
                                fullWidth
                                label="Password"
                                type={showPassword ? 'text' : 'password'}
                                value={loginForm.password}
                                onChange={handleLoginFormChange('password')}
                                error={!!formErrors.password}
                                helperText={formErrors.password}
                                margin="normal"
                                InputProps={{
                                    endAdornment: (
                                        <InputAdornment position="end">
                                            <IconButton
                                                onClick={handleTogglePasswordVisibility}
                                                edge="end"
                                                disabled={loggingIn}
                                            >
                                                {showPassword ? <VisibilityOff /> : <Visibility />}
                                            </IconButton>
                                        </InputAdornment>
                                    ),
                                }}
                                disabled={loggingIn}
                            />

                            <Button
                                type="submit"
                                fullWidth
                                variant="contained"
                                size="large"
                                disabled={loggingIn}
                                sx={{
                                    mt: 3,
                                    mb: 2,
                                    py: 1.5,
                                    borderRadius: 2,
                                }}
                            >
                                {loggingIn ? (
                                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                        <CircularProgress size={20} color="inherit" />
                                        Signing In...
                                    </Box>
                                ) : (
                                    'Sign In'
                                )}
                            </Button>
                        </Box>
                    </TabPanel>

                    <TabPanel value={tabValue} index={1}>
                        <Box component="form" onSubmit={handleRegister} sx={{ p: 3 }}>
                            <TextField
                                fullWidth
                                label="Full Name"
                                value={registerForm.name}
                                onChange={handleRegisterFormChange('name')}
                                error={!!formErrors.name}
                                helperText={formErrors.name}
                                margin="normal"
                                InputProps={{
                                    startAdornment: (
                                        <InputAdornment position="start">
                                            <Person color="action" />
                                        </InputAdornment>
                                    ),
                                }}
                                disabled={registering}
                            />

                            <TextField
                                fullWidth
                                label="Email Address"
                                type="email"
                                value={registerForm.email}
                                onChange={handleRegisterFormChange('email')}
                                error={!!formErrors.email}
                                helperText={formErrors.email}
                                margin="normal"
                                InputProps={{
                                    startAdornment: (
                                        <InputAdornment position="start">
                                            <Email color="action" />
                                        </InputAdornment>
                                    ),
                                }}
                                disabled={registering}
                            />

                            <TextField
                                fullWidth
                                label="Password"
                                type={showPassword ? 'text' : 'password'}
                                value={registerForm.password}
                                onChange={handleRegisterFormChange('password')}
                                error={!!formErrors.password}
                                helperText={formErrors.password || 'Must be at least 6 characters'}
                                margin="normal"
                                InputProps={{
                                    endAdornment: (
                                        <InputAdornment position="end">
                                            <IconButton
                                                onClick={handleTogglePasswordVisibility}
                                                edge="end"
                                                disabled={registering}
                                            >
                                                {showPassword ? <VisibilityOff /> : <Visibility />}
                                            </IconButton>
                                        </InputAdornment>
                                    ),
                                }}
                                disabled={registering}
                            />

                            <TextField
                                fullWidth
                                label="Confirm Password"
                                type={showConfirmPassword ? 'text' : 'password'}
                                value={registerForm.confirmPassword}
                                onChange={handleRegisterFormChange('confirmPassword')}
                                error={!!formErrors.confirmPassword}
                                helperText={formErrors.confirmPassword}
                                margin="normal"
                                InputProps={{
                                    endAdornment: (
                                        <InputAdornment position="end">
                                            <IconButton
                                                onClick={handleToggleConfirmPasswordVisibility}
                                                edge="end"
                                                disabled={registering}
                                            >
                                                {showConfirmPassword ? <VisibilityOff /> : <Visibility />}
                                            </IconButton>
                                        </InputAdornment>
                                    ),
                                }}
                                disabled={registering}
                            />

                            <Divider sx={{ my: 2 }}>
                                <Typography variant="caption" color="text.secondary">
                                    Organization Details
                                </Typography>
                            </Divider>

                            <TextField
                                fullWidth
                                label="Organization Name"
                                value={registerForm.org_name}
                                onChange={handleRegisterFormChange('org_name')}
                                error={!!formErrors.org_name}
                                helperText={formErrors.org_name}
                                margin="normal"
                                InputProps={{
                                    startAdornment: (
                                        <InputAdornment position="start">
                                            <Business color="action" />
                                        </InputAdornment>
                                    ),
                                }}
                                disabled={registering}
                            />

                            <TextField
                                fullWidth
                                label="Organization ID"
                                value={registerForm.org_id}
                                onChange={handleRegisterFormChange('org_id')}
                                margin="normal"
                                disabled={registering}
                                helperText="Auto-generated organization identifier"
                            />

                            <Button
                                type="submit"
                                fullWidth
                                variant="contained"
                                size="large"
                                disabled={registering}
                                sx={{
                                    mt: 3,
                                    mb: 2,
                                    py: 1.5,
                                    borderRadius: 2,
                                }}
                            >
                                {registering ? (
                                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                        <CircularProgress size={20} color="inherit" />
                                        Creating Account...
                                    </Box>
                                ) : (
                                    'Create Account'
                                )}
                            </Button>
                        </Box>
                    </TabPanel>
                </CardContent>
            </Card>
        </Box>
    );
};

export default UserAuth;