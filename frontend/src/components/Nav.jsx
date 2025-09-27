import React, { useState } from 'react';
import {
    Drawer,
    List,
    ListItem,
    ListItemButton,
    ListItemIcon,
    ListItemText,
    IconButton,
    AppBar,
    Toolbar,
    Typography,
    Box,
    useTheme,
    useMediaQuery,
    Collapse,
    Divider,
} from '@mui/material';
import {
    Menu as MenuIcon,
    Home as HomeIcon,
    FolderOpen as ProjectsIcon,
    Settings as SettingsIcon,
    ChevronLeft as ChevronLeftIcon,
    ChevronRight as ChevronRightIcon,
    Brightness4,
    Brightness7,
} from '@mui/icons-material';
import { useThemeMode } from '../themes/ThemeContext';
import logo from '../media/logo.png'; // Import the logo
import logoLight from '../media/logo-light.png'; // Import the logo
import logoDark from '../media/logo-dark.png'; // Import the logo
import LogoutButton from './LogoutButton';

const Nav = () => {
    const theme = useTheme();
    const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
    const { mode, toggleColorMode } = useThemeMode();

    // State for mobile drawer
    const [mobileOpen, setMobileOpen] = useState(false);

    // State for desktop drawer collapse (user preference)
    const [desktopCollapsed, setDesktopCollapsed] = useState(true);

    const drawerWidth = 240;
    const collapsedWidth = 72;

    const menuItems = [
        { text: 'Home', icon: <HomeIcon />, path: '/' },
        { text: 'Projects', icon: <ProjectsIcon />, path: '/projects' },
        { text: 'Settings', icon: <SettingsIcon />, path: '/settings' },
    ];

    const handleDrawerToggle = () => {
        setMobileOpen(!mobileOpen);
    };

    const handleDesktopToggle = () => {
        setDesktopCollapsed(!desktopCollapsed);
    };

    const DrawerContent = ({ collapsed = true }) => (
        <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
            {/* Header */}
            <Box
                sx={{
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    p: 2,
                    minHeight: 64,
                }}
            >
                {/* Logo/Title at top */}
                <Box sx={{ mb: collapsed ? 1 : 2, display: 'flex', alignItems: 'center', gap: collapsed ? 0 : 1 }}>
                    {collapsed ? (
                        <img
                            src={mode === 'dark' ? logoDark : logoLight}
                            alt="AlphaVal Pro Logo"
                            style={{
                                width: 48,
                                height: 48,
                                objectFit: 'contain',
                                filter: 'drop-shadow(0px 3px 3px rgba(0, 0, 0, 0.1))'
                            }}
                        />
                    ) : (
                        <img src={mode === 'dark' ? logoDark : logoLight} alt="AlphaVal Pro Logo" style={{ width: 48, height: 48, objectFit: 'contain' }} />
                    )}
                    {!collapsed && (
                        <Typography variant="h6" sx={{ fontWeight: 'light' }} noWrap>
                            AlphaVal Pro
                        </Typography>
                    )}
                </Box>

                {/* Collapse Toggle Button below logo/title */}
                {!isMobile && (
                    <IconButton onClick={handleDesktopToggle} size="small">
                        {collapsed ? <ChevronRightIcon /> : <ChevronLeftIcon />}
                    </IconButton>
                )}
            </Box>

            {/* Menu Items */}
            <List sx={{ flexGrow: 1 }}>
                {menuItems.map((item) => (
                    <ListItem key={item.text} disablePadding>
                        <ListItemButton
                            sx={{
                                justifyContent: collapsed ? 'center' : 'flex-start',
                                px: 2.5,
                                py: 1.5,
                            }}
                        >
                            <ListItemIcon
                                sx={{
                                    minWidth: collapsed ? 0 : 56,
                                    justifyContent: 'center',
                                }}
                            >
                                {item.icon}
                            </ListItemIcon>
                            {!collapsed && <ListItemText primary={item.text} />}
                        </ListItemButton>
                    </ListItem>
                ))}
            </List>

            {/* Bottom Actions */}
            <Box sx={{ mt: 'auto' }}>
                <Divider sx={{ mx: 1 }} />
                
                {/* Action buttons container */}
                <Box sx={{ 
                    display: 'flex', 
                    flexDirection: collapsed ? 'column' : 'row',
                    alignItems: 'center',
                    justifyContent: collapsed ? 'center' : 'space-between',
                    gap: collapsed ? 1 : 2,
                    p: 2 
                }}>
                    {/* Theme Toggle Button */}
                    <IconButton
                        onClick={toggleColorMode}
                        sx={{
                            width: 40,
                            height: 40,
                            borderRadius: '50%',
                            '&:hover': {
                                backgroundColor: 'action.hover',
                            },
                        }}
                        title={`Switch to ${mode === 'dark' ? 'light' : 'dark'} mode`}
                    >
                        {mode === 'dark' ? <Brightness7 /> : <Brightness4 />}
                    </IconButton>

                    {/* Logout Button */}
                    {collapsed ? (
                        <LogoutButton variant="icon" collapsed={collapsed} />
                    ) : (
                        <LogoutButton variant="text" />
                    )}
                </Box>
            </Box>
        </Box>
    );

    return (
        <>
            {/* Mobile AppBar */}
            {isMobile && (
                <AppBar
                    position="fixed"
                    sx={{
                        width: '100%',
                        zIndex: theme.zIndex.drawer + 1,
                    }}
                >
                    <Toolbar>
                        <IconButton
                            color="inherit"
                            aria-label="open drawer"
                            edge="start"
                            onClick={handleDrawerToggle}
                            sx={{ mr: 2 }}
                        >
                            <MenuIcon />
                        </IconButton>
                        <Typography variant="h6" noWrap component="div" sx={{ flexGrow: 1 }}>
                            AlphaVal Pro
                        </Typography>
                        
                        {/* Mobile header actions */}
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            <IconButton
                                color="inherit"
                                onClick={toggleColorMode}
                                title={`Switch to ${mode === 'dark' ? 'light' : 'dark'} mode`}
                            >
                                {mode === 'dark' ? <Brightness7 /> : <Brightness4 />}
                            </IconButton>
                            <LogoutButton variant="icon" showConfirmDialog={true} />
                        </Box>
                    </Toolbar>
                </AppBar>
            )}

            {/* Mobile Drawer */}
            {isMobile && (
                <Drawer
                    variant="temporary"
                    open={mobileOpen}
                    onClose={handleDrawerToggle}
                    ModalProps={{
                        keepMounted: true, // Better open performance on mobile
                    }}
                    sx={{
                        '& .MuiDrawer-paper': {
                            boxSizing: 'border-box',
                            width: drawerWidth,
                        },
                    }}
                >
                    <DrawerContent collapsed={false} />
                </Drawer>
            )}

            {/* Desktop Drawer */}
            {!isMobile && (
                <Drawer
                    variant="permanent"
                    sx={{
                        width: desktopCollapsed ? collapsedWidth : drawerWidth,
                        flexShrink: 0,
                        '& .MuiDrawer-paper': {
                            width: desktopCollapsed ? collapsedWidth : drawerWidth,
                            boxSizing: 'border-box',
                            transition: theme.transitions.create('width', {
                                easing: theme.transitions.easing.sharp,
                                duration: theme.transitions.duration.enteringScreen,
                            }),
                            overflowX: 'hidden',
                        },
                    }}
                >
                    <DrawerContent collapsed={desktopCollapsed} />
                </Drawer>
            )}
        </>
    );
};

export default Nav;