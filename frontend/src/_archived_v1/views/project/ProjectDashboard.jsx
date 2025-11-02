import React, { useState, useEffect, useMemo, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useDispatch, useSelector } from "react-redux";
import {
  Box,
  Typography,
  Breadcrumbs,
  Link,
  Tab,
  Tabs,
  Paper,
  CircularProgress,
  Alert,
  IconButton,
  Tooltip,
  Button,
  Chip,
  Menu,
  MenuItem,
  ListItemIcon,
  ListItemText,
  Divider,
} from "@mui/material";
import {
  WarningAmber as AIIcons,
  NavigateNext as NavigateNextIcon,
  ArrowBack as ArrowBackIcon,
  Folder as FolderIcon,
  ViewInAr as DashboardIcon,
  DynamicFeed as ScenariosIcon,
  Analytics as AnalysisIcon,
  Info as InfoIcon,
  Check as CheckIcon,
  MoreHoriz as MoreIcon,
} from "@mui/icons-material";
import {
  fetchProjectSmart,
  selectProjectById,
  selectHasCachedProject,
  selectIsProjectDataStale,
  selectProjectsLoading,
  selectProjectsError,
  clearProjectCache,
  selectAllProjects,
  fetchProjects,
} from "../../redux/projectSlice";
import Sources from "./Sources";
import InspectDataView from "./InspectDataView";
import Scenarios from "./scenarios/ScenarioDashboard";

// Tab configuration
const PROJECT_TABS = [
  {
    id: "sources",
    label: "Sources",
    icon: <FolderIcon />,
    description: "Project documents and data uploads",
  },
  {
    id: "inspect-data",
    label: "Inspect Data",
    icon: <DashboardIcon />,
    description: "Data gleaned from uploaded documents",
  },
  {
    id: "scenarios",
    label: "Scenarios",
    icon: <ScenariosIcon />,
    description: "Create deltas from base case for costing",
  },
  {
    id: "analysis",
    label: "Analysis",
    icon: <AnalysisIcon />,
    description: "Compare and model base cases",
  },
];

const ProjectDashboard = () => {
  const { projectId } = useParams();
  const navigate = useNavigate();
  const dispatch = useDispatch();

  // Use memoized selectors
  const currentProject = useSelector((state) =>
    selectProjectById(state, projectId)
  );
  const allProjects = useSelector(selectAllProjects);
  const hasCachedData = useSelector((state) =>
    selectHasCachedProject(state, projectId)
  );
  const isDataStale = useSelector((state) =>
    selectIsProjectDataStale(state, projectId)
  );
  const loading = useSelector(selectProjectsLoading);
  const error = useSelector(selectProjectsError);

  // Local state
  const [activeTab, setActiveTab] = useState("sources");
  const [projectMenuAnchor, setProjectMenuAnchor] = useState(null);
  const projectMenuOpen = Boolean(projectMenuAnchor);

  // Fetch all projects for the dropdown
  useEffect(() => {
    if (allProjects.length === 0) {
      dispatch(fetchProjects());
    }
  }, [dispatch, allProjects.length]);

  // Get recent projects (excluding current)
  const recentProjects = useMemo(() => {
    return allProjects
      .filter((p) => p.id !== projectId)
      .sort((a, b) => new Date(b.updated_at) - new Date(a.updated_at))
      .slice(0, 5);
  }, [allProjects, projectId]);

  // Memoized function to load project data
  const loadProjectData = useCallback(() => {
    if (projectId) {
      dispatch(
        fetchProjectSmart({
          projectId,
          forceRefresh: false,
        })
      );
    }
  }, [dispatch, projectId]);

  // Load project data when component mounts or projectId changes
  useEffect(() => {
    loadProjectData();
  }, [loadProjectData]);

  // Force refresh function
  const forceRefresh = useCallback(() => {
    if (projectId) {
      console.log("Force refreshing project data");
      dispatch(
        fetchProjectSmart({
          projectId,
          forceRefresh: true,
        })
      );
    }
  }, [dispatch, projectId]);

  // Clear cache function
  const clearCache = useCallback(() => {
    if (projectId) {
      dispatch(clearProjectCache(projectId));
      dispatch(fetchProjectSmart({ projectId, forceRefresh: true }));
    }
  }, [dispatch, projectId]);

  // Handle tab change with memoization
  const handleTabChange = useCallback((event, newValue) => {
    setActiveTab(newValue);
  }, []);

  // Handle breadcrumb navigation
  const handleProjectsClick = useCallback(
    (event) => {
      event.preventDefault();
      navigate("/");
    },
    [navigate]
  );

  // Handle project menu
  const handleProjectMenuOpen = useCallback((event) => {
    event.preventDefault();
    event.stopPropagation();
    setProjectMenuAnchor(event.currentTarget);
  }, []);

  const handleProjectMenuClose = useCallback(() => {
    setProjectMenuAnchor(null);
  }, []);

  const handleProjectSelect = useCallback(
    (selectedProjectId) => {
      handleProjectMenuClose();
      navigate(`/projects/${selectedProjectId}`);
    },
    [navigate, handleProjectMenuClose]
  );

  const handleShowAllProjects = useCallback(() => {
    handleProjectMenuClose();
    navigate("/");
  }, [navigate, handleProjectMenuClose]);

  // Memoized date formatting
  const formattedDate = useMemo(() => {
    if (!currentProject?.updated_at) return "";
    return new Date(currentProject.updated_at).toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
      timeZoneName: "short",
    });
  }, [currentProject?.updated_at]);

  // Show cache status for debugging
  const cacheStatus = useMemo(() => {
    if (!projectId) return "No project ID";
    if (!hasCachedData) return "No cache";
    if (isDataStale) return "Cache stale";
    return "Cache fresh";
  }, [projectId, hasCachedData, isDataStale]);

  // Loading state - only show if we don't have any cached data
  if (loading.fetch && !currentProject) {
    return (
      <Box
        sx={{
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          minHeight: "50vh",
        }}
      >
        <CircularProgress />
        <Typography variant="body1" sx={{ ml: 2 }}>
          Loading project...
        </Typography>
      </Box>
    );
  }

  // Error state
  if (error) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert
          severity="error"
          action={
            <Button color="inherit" size="small" onClick={forceRefresh}>
              Retry
            </Button>
          }
        >
          {error}
        </Alert>
      </Box>
    );
  }

  // Project not found
  if (!currentProject) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert
          severity="warning"
          action={
            <Button color="inherit" size="small" onClick={forceRefresh}>
              Refresh
            </Button>
          }
        >
          Project not found
        </Alert>
      </Box>
    );
  }

  return (
    <Box sx={{ height: "100vh", display: "flex", flexDirection: "column" }}>
      {/* Header with Breadcrumbs and Last Updated */}
      <Box
        sx={{
          p: 3,
          borderBottom: 1,
          borderColor: "divider",
          backgroundColor: "background.paper",
        }}
      >
        <Box
          sx={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
          }}
        >
          {/* Breadcrumbs */}
          <Breadcrumbs
            aria-label="breadcrumb"
            separator={<NavigateNextIcon fontSize="small" />}
            sx={{
              flexGrow: 1,
              padding: 0,
              margin: 0,
              "& .MuiBreadcrumbs-ol": { alignItems: "center", gap: 1 },
            }}
          >
            <Link
              underline="none"
              color={(theme) => theme.palette.primary.main}
              href="/"
              onClick={handleProjectsClick}
              sx={{
                display: "flex",
                alignItems: "center",
                cursor: "pointer",
              }}
            >
              Home
            </Link>
            <Link
              underline="none"
              color={(theme) => theme.palette.primary.main}
              href="/"
              onMouseEnter={handleProjectMenuOpen}
              onClick={handleProjectsClick}
              sx={{
                display: "flex",
                alignItems: "center",
                cursor: "pointer",
                position: "relative",
              }}
            >
              Projects
            </Link>
            <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
              <Typography
                color="text.primary"
                sx={{
                  fontWeight: "medium",
                  maxWidth: "300px",
                  overflow: "hidden",
                  textOverflow: "ellipsis",
                  whiteSpace: "nowrap",
                }}
              >
                {currentProject.name}
              </Typography>
              {currentProject.description && (
                <Tooltip
                  title={currentProject.description}
                  arrow
                  placement="bottom-start"
                >
                  <InfoIcon
                    fontSize="small"
                    sx={{
                      color: "text.secondary",
                      cursor: "help",
                      ml: 0.5,
                    }}
                  />
                </Tooltip>
              )}
            </Box>
          </Breadcrumbs>

          {/* Last Updated */}
          <Box sx={{ textAlign: "right", ml: 2 }}>
            <Typography variant="body2" color="text.secondary">
              Last Updated
            </Typography>
            <Typography variant="body2" fontWeight="medium">
              {formattedDate}
            </Typography>
          </Box>
        </Box>
      </Box>

      {/* Project Dropdown Menu */}
      <Menu
        anchorEl={projectMenuAnchor}
        open={projectMenuOpen}
        onClose={handleProjectMenuClose}
        MenuListProps={{
          onMouseLeave: handleProjectMenuClose,
        }}
        slotProps={{
          paper: {
            sx: {
              mt: 0.5,
              minWidth: 280,
              maxWidth: 400,
            },
          },
        }}
        anchorOrigin={{
          vertical: "bottom",
          horizontal: "left",
        }}
        transformOrigin={{
          vertical: "top",
          horizontal: "left",
        }}
      >
        {/* Current Project */}
        <MenuItem
          selected
          sx={{
            backgroundColor: "action.selected",
            "&:hover": {
              backgroundColor: "action.selected",
            },
          }}
        >
          <ListItemIcon>
            <CheckIcon fontSize="small" />
          </ListItemIcon>
          <ListItemText
            primary={currentProject.name}
            secondary="Current project"
            primaryTypographyProps={{
              fontWeight: "medium",
              noWrap: true,
            }}
            secondaryTypographyProps={{
              variant: "caption",
            }}
          />
        </MenuItem>

        {/* Recent Projects - Remove the wrapping Fragment */}
        {recentProjects.length > 0 && [
          <Divider key="divider-1" sx={{ my: 1 }} />,
          <Box key="header" sx={{ px: 2, py: 1 }}>
            <Typography
              variant="caption"
              color="text.secondary"
              fontWeight="medium"
            >
              RECENT PROJECTS
            </Typography>
          </Box>,
          ...recentProjects.map((project) => (
            <MenuItem
              key={project.project_id}
              onClick={() => handleProjectSelect(project.id)}
            >
              {/* <ListItemIcon>
                <FolderIcon fontSize="small" />
              </ListItemIcon> */}
              <ListItemText
                primary={project.name}
                secondary={new Date(project.updated_at).toLocaleDateString(
                  "en-US",
                  {
                    month: "short",
                    day: "numeric",
                    year: "numeric",
                  }
                )}
                primaryTypographyProps={{
                  noWrap: true,
                }}
                secondaryTypographyProps={{
                  variant: "caption",
                }}
              />
            </MenuItem>
          )),
        ]}

        {/* Show All Projects */}
        <Divider sx={{ my: 1 }} />
        <MenuItem onClick={handleShowAllProjects}>
          <ListItemIcon>
            <MoreIcon fontSize="small" />
          </ListItemIcon>
          <ListItemText
            primary="Show all projects"
            primaryTypographyProps={{
              fontWeight: "medium",
              color: "primary.main",
            }}
          />
        </MenuItem>
      </Menu>

      {/* Show loading indicator when refreshing but we have cached data */}
      {loading.fetch && currentProject && (
        <Box
          sx={{
            position: "fixed",
            top: 0,
            left: 0,
            right: 0,
            zIndex: 1000,
            backgroundColor: "primary.main",
            color: "white",
            textAlign: "center",
            py: 0.5,
          }}
        >
          <Typography variant="caption">Refreshing project data...</Typography>
        </Box>
      )}

      {/* Main Content Area */}
      <Box sx={{ display: "flex", flex: 1, overflow: "hidden" }}>
        {/* Vertical Tabs Sidebar */}
        <Paper
          elevation={0}
          sx={{
            width: 200,
            borderRight: 1,
            borderColor: "divider",
            borderRadius: 0,
            display: "flex",
            flexDirection: "column",
            justifyContent: "space-between",
            backgroundColor: "background.paper",
            p: 2,
          }}
        >
          <Tabs
            orientation="vertical"
            variant="scrollable"
            value={activeTab}
            onChange={handleTabChange}
            sx={{
              "& .MuiTabs-indicator": {
                left: 0,
                width: 3,
              },
            }}
          >
            {PROJECT_TABS.map((tab) => (
              <Tab
                key={tab.id}
                value={tab.id}
                icon={tab.icon}
                iconPosition="start"
                label={
                  <Box sx={{ textAlign: "left" }}>
                    <Typography variant="body2" fontWeight="medium">
                      {tab.label}
                    </Typography>
                  </Box>
                }
                sx={{
                  minHeight: 50,
                  alignItems: "center",
                  justifyContent: "flex-start",
                  textAlign: "left",
                  px: 2,
                  paddingLeft: 2,
                  paddingRight: 0,
                  py: 2,
                  "&.Mui-selected": {
                    backgroundColor: "action.selected",
                  },
                  "& .MuiTab-iconWrapper": {
                    marginBottom: 0,
                    marginRight: 1.5,
                    marginTop: 0,
                  },
                }}
              />
            ))}
          </Tabs>
          <Box
            sx={{
              display: "flex",
              gap: 2,
              alignItems: "center",
              justifyContent: "flex-start",
              color: "text.secondary",
            }}
          >
            <AIIcons sx={{}} />
            <Typography variant="body3" sx={{ color: "text.secondary" }}>
              AI can make mistakes. Please verify all data before making any
              decisions.
            </Typography>
          </Box>
        </Paper>

        {/* Tab Content Area */}
        <Box
          sx={{
            flex: 1,
            p: 3,
            overflow: "auto",
            backgroundColor: "background.default",
          }}
        >
          {/* Tab Content */}
          {activeTab === "sources" && <Sources />}

          {activeTab === "inspect-data" && (
            <Box>
              <Typography variant="h5" gutterBottom fontWeight="bold">
                Inspect Data
              </Typography>
              <Typography variant="body1" color="text.secondary" paragraph>
                Review and validate data extracted from your uploaded documents.
                This forms the foundation for your cost analysis and scenario
                modeling.
              </Typography>
              <Paper sx={{ p: 3 }}>
                <InspectDataView />
              </Paper>
            </Box>
          )}

          {activeTab === "scenarios" && (
            <Box>
              <Typography variant="h5" gutterBottom fontWeight="bold">
                Scenarios
              </Typography>
              <Typography variant="body1" color="text.secondary" paragraph>
                Create and manage different scenarios by applying deltas to your
                base case. Compare various operational parameters and their
                impact on costs.
              </Typography>
              <Paper sx={{ p: 3 }}>
                <Scenarios />
              </Paper>
            </Box>
          )}

          {activeTab === "analysis" && (
            <Box>
              <Typography variant="h5" gutterBottom fontWeight="bold">
                Analysis
              </Typography>
              <Typography variant="body1" color="text.secondary" paragraph>
                Compare scenarios and perform decision modeling. Generate
                reports and visualizations to support your mining investment
                decisions.
              </Typography>
              <Paper sx={{ p: 3 }}>
                <Typography
                  variant="body2"
                  color="text.secondary"
                  sx={{ fontStyle: "italic" }}
                >
                  [Analysis View - To be implemented]
                </Typography>
              </Paper>
            </Box>
          )}
        </Box>
      </Box>
    </Box>
  );
};

export default ProjectDashboard;
