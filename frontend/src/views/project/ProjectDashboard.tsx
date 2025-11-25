import React, { useEffect, useState, useCallback, useMemo } from "react";
import { useParams, useNavigate, Link as RouterLink } from "react-router-dom";
import { useDispatch, useSelector } from "react-redux";
import {
  Box,
  Typography,
  Button,
  CircularProgress,
  Alert,
  Paper,
  Card,
  CardContent,
  Chip,
  Grid,
  Tabs,
  Tab,
  Divider,
  Breadcrumbs,
  Link,
  IconButton,
  Tooltip,
} from "@mui/material";
import {
  Description as DescriptionIcon,
  FolderSpecial as FolderSpecialIcon,
  Storage as StorageIcon,
  CalendarToday as CalendarTodayIcon,
  Update as UpdateIcon,
  Edit as EditIcon,
} from "@mui/icons-material";
import {
  fetchProjectById,
  uploadProjectFiles,
  listProjectFiles,
  downloadProjectFile,
  deleteProjectFile,
  clearProjectData,
  selectCurrentProject,
  selectProjectsLoading,
  selectProjectsError,
  selectProjectUploadingFiles,
  selectProjectFiles,
  selectProjectFilesLoading,
  clearError,
} from "../../redux/projectsSlice";
import {
  fetchScenarios,
  selectScenariosByProject,
  selectScenariosLoading,
} from "../../redux/scenariosSlice";
import { useDialogs } from "../../hooks/useDialogs";
import { ProjectStatus } from "../../types/api";
import FileUpload from "../../components/project/FileUpload";
import DocumentList, {
  DocumentMetadata,
} from "../../components/project/DocumentList";
import ScenariosList from "../../components/scenario/ScenariosList";
import ScenarioDetails from "../scenario/ScenarioDetails";
import ProgressWidget from "../../components/common/ProgressWidget";
import InspectDataView from "../../components/data/InspectDataView";
import CreateProjectDialog from "../../components/project/CreateProjectDialog";

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

const TabPanel: React.FC<TabPanelProps> = ({ children, value, index }) => {
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`project-tabpanel-${index}`}
      aria-labelledby={`project-tab-${index}`}
    >
      {value === index && <Box sx={{ pt: 3 }}>{children}</Box>}
    </div>
  );
};

/**
 * Project Dashboard - Main landing page for a project.
 *
 * Contains:
 * - Top panel with project information
 * - Navigation back to projects list
 * - Tabbed interface with Sources and Scenarios tabs
 */
const ProjectDashboard: React.FC = () => {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const dialogs = useDialogs();
  const project = useSelector(selectCurrentProject);
  const loading = useSelector((state: any) => state.projects.loading.fetchById);
  const uploadingFiles = useSelector(selectProjectUploadingFiles);
  const filesLoading = useSelector(selectProjectFilesLoading);
  const projectFiles = useSelector(selectProjectFiles(projectId || ""));
  const error = useSelector(selectProjectsError);
  const [activeTab, setActiveTab] = useState<number>(0);
  const [analysisError, setAnalysisError] = useState<string | null>(null);
  const [selectedScenarioId, setSelectedScenarioId] = useState<string | null>(
    null
  ); // Selected scenario in Scenarios tab

  // Scenarios data for Overview tab
  const scenariosLoading = useSelector(selectScenariosLoading);
  const scenariosSelector = useMemo(
    () => (projectId ? selectScenariosByProject(projectId) : undefined),
    [projectId]
  );
  const scenarios = useSelector((state: any) =>
    scenariosSelector ? scenariosSelector(state) : []
  );

  // File upload state for Sources tab
  const [baseCaseFiles, setBaseCaseFiles] = useState<File[]>([]);
  const [tabularDataFiles, setTabularDataFiles] = useState<File[]>([]);
  const [clearFileUploadTrigger, setClearFileUploadTrigger] =
    useState<number>(0);
  const [uploadJobId, setUploadJobId] = useState<string | null>(null);
  const [editProjectDialogOpen, setEditProjectDialogOpen] = useState(false);

  /**
   * Fetch project data and handle URL hash for tab navigation
   */
  useEffect(() => {
    if (projectId) {
      // Only fetch if we don't have the project or it's a different project
      if (!project || project.id !== projectId) {
        dispatch(fetchProjectById(projectId) as any);
        dispatch(listProjectFiles(projectId) as any);
        dispatch(fetchScenarios(projectId) as any);
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projectId, dispatch]); // Removed 'project' to prevent cascade re-renders

  /**
   * Handle URL hash for tab navigation (only on mount or projectId change)
   */
  useEffect(() => {
    // Check URL hash to set active tab
    // Only set tab from hash, don't reset to default when no hash
    // This prevents overriding user's current tab selection
    const hash = window.location.hash;
    if (hash === "#scenarios") {
      setActiveTab(2); // Scenarios tab is at index 2
    } else if (hash === "#sources") {
      setActiveTab(1); // Sources tab is at index 1
    }
    // If no hash, don't change the tab - let it stay on current tab
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projectId]); // Only run when projectId changes, not when project updates

  /**
   * Clear selected scenario when switching away from Scenarios tab
   */
  useEffect(() => {
    if (activeTab !== 3) {
      setSelectedScenarioId(null);
    }
  }, [activeTab]);

  /**
   * Format file size for display
   */
  const formatFileSize = (bytes: number): string => {
    if (!bytes || bytes === 0) return "0 Bytes";
    const k = 1024;
    const sizes = ["Bytes", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
  };

  /**
   * Calculate total document size
   */
  const calculateTotalDocumentSize = (): number => {
    if (!projectFiles) return 0;
    const allFiles = [
      ...(projectFiles.base_case_files || []),
      ...(projectFiles.tabular_data_files || []),
    ];
    return allFiles.reduce((total, file) => total + (file.length || 0), 0);
  };

  /**
   * Get number of documents
   */
  const getDocumentCount = (): number => {
    if (!projectFiles) return 0;
    return (
      (projectFiles.base_case_files?.length || 0) +
      (projectFiles.tabular_data_files?.length || 0)
    );
  };

  /**
   * Format date for display
   */
  const formatDate = (dateString: string): string => {
    try {
      return new Date(dateString).toLocaleDateString("en-US", {
        year: "numeric",
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      });
    } catch {
      return dateString;
    }
  };

  /**
   * Get status color for chip
   */
  const getStatusColor = (
    status: ProjectStatus
  ):
    | "default"
    | "primary"
    | "secondary"
    | "error"
    | "info"
    | "success"
    | "warning" => {
    switch (status) {
      case ProjectStatus.DRAFT:
        return "default";
      case ProjectStatus.PROCESSING:
        return "info";
      case ProjectStatus.VALIDATION:
        return "warning";
      case ProjectStatus.COMPLETED:
        return "success";
      default:
        return "default";
    }
  };

  /**
   * Handle base case files selected
   */
  const handleBaseCaseFilesSelected = useCallback((files: File[]) => {
    setBaseCaseFiles(files);
  }, []);

  /**
   * Handle tabular data files selected
   */
  const handleTabularDataFilesSelected = useCallback((files: File[]) => {
    setTabularDataFiles(files);
  }, []);

  /**
   * Handle file upload in Sources tab
   */
  const handleUploadFiles = useCallback(async () => {
    if (!projectId) return;

    if (baseCaseFiles.length === 0 && tabularDataFiles.length === 0) {
      setAnalysisError("Please select at least one file to upload");
      return;
    }

    setAnalysisError(null);
    dispatch(clearError());

    try {
      const result = await dispatch(
        uploadProjectFiles({
          projectId,
          baseCaseFiles,
          tabularDataFiles,
        }) as any
      );

      if (uploadProjectFiles.fulfilled.match(result)) {
        const response = result.payload;
        // console.log("Upload response:", response);

        // job_id is nested in uploadData
        const jobId = response.uploadData?.job_id || response.job_id;
        // console.log("job_id from response:", jobId);

        // If job_id is present, processing is happening in background
        if (jobId) {
          // console.log("Setting uploadJobId to:", jobId);
          setUploadJobId(jobId);
        } else {
          // console.log("No job_id in response, immediate processing");
        }

        // Clear selected files
        setBaseCaseFiles([]);
        setTabularDataFiles([]);
        // Trigger FileUpload components to clear their internal selected files
        setClearFileUploadTrigger((prev) => prev + 1);

        // Only refresh immediately if no background processing
        if (!jobId) {
          await dispatch(fetchProjectById(projectId) as any);
          await dispatch(listProjectFiles(projectId) as any);
        }
      } else {
        setAnalysisError("Failed to upload files");
      }
    } catch (error) {
      setAnalysisError("Failed to upload files");
    }
  }, [projectId, baseCaseFiles, tabularDataFiles, dispatch]);

  /**
   * Handle file download
   */
  const handleDownloadFile = useCallback(
    (fileId: string, filename: string) => {
      if (!projectId) return;
      dispatch(downloadProjectFile({ projectId, fileId, filename }) as any);
    },
    [projectId, dispatch]
  );

  /**
   * Handle progress widget dismiss
   */
  const handleProgressDismiss = useCallback(() => {
    setUploadJobId(null);
  }, []);

  /**
   * Handle progress complete
   */
  const handleProgressComplete = useCallback(() => {
    if (projectId) {
      dispatch(fetchProjectById(projectId) as any);
      dispatch(listProjectFiles(projectId) as any);
    }
    setUploadJobId(null);
  }, [projectId, dispatch]);

  /**
   * Handle clear all project data with confirmation dialog
   */
  const handleClearProjectData = useCallback(async () => {
    if (!projectId || !project) return;

    // Show warning dialog
    const confirmed = await dialogs.clearData(
      "This action cannot be undone. Are you absolutely sure?",
      {
        title: "Clear All Project Data",
        warningMsg: `This will permanently delete ALL data associated with "${project.name}", including:
        
• All scenarios and cost estimates
• All uploaded files and documents
• All extracted entities, tables, and analysis results
• All processing history

The project itself will remain, but all its data will be cleared.`,
        okText: "Clear All Data",
        cancelText: "Cancel",
      }
    );

    if (!confirmed) {
      return; // User cancelled
    }

    setAnalysisError(null);
    dispatch(clearError());

    try {
      const result = await dispatch(clearProjectData(projectId) as any);

      if (clearProjectData.fulfilled.match(result)) {
        // Refresh project and files list
        await dispatch(fetchProjectById(projectId) as any);
        await dispatch(listProjectFiles(projectId) as any);
        await dispatch(fetchScenarios(projectId) as any);
      } else if (clearProjectData.rejected.match(result)) {
        setAnalysisError(result.payload as string);
      }
    } catch (error) {
      setAnalysisError("Failed to clear project data. Please try again.");
    }
  }, [projectId, project, dispatch, dialogs]);

  /**
   * Handle file delete with confirmation dialog
   */
  const handleDeleteFile = useCallback(
    async (fileId: string) => {
      if (!projectId) return;

      // Find file metadata to show filename in warning
      const allFiles = [
        ...(projectFiles?.base_case_files || []),
        ...(projectFiles?.tabular_data_files || []),
      ];
      const fileToDelete = allFiles.find((f) => f.file_id === fileId);
      const filename = fileToDelete?.filename || "this file";

      // Show confirmation dialog with warning
      const confirmed = await dialogs.confirm(
        `Deleting "${filename}" will permanently remove the file and all associated data. This includes:
        
• Related scenarios that depend on this file
• All ingested and extracted data from this file
• Any analysis results based on this file

This action cannot be undone. Are you sure you want to delete this file?`,
        {
          title: "Delete File",
          severity: "error",
          okText: "Delete",
          cancelText: "Cancel",
        }
      );

      if (!confirmed) {
        return; // User cancelled
      }

      setAnalysisError(null);
      dispatch(clearError());

      try {
        const result = await dispatch(
          deleteProjectFile({ projectId, fileId }) as any
        );

        if (deleteProjectFile.fulfilled.match(result)) {
          // Refresh project files list and project data
          await dispatch(listProjectFiles(projectId) as any);
          await dispatch(fetchProjectById(projectId) as any);
          // Ensure we stay on Sources tab after deletion (set after refresh to prevent override)
          setActiveTab(1);
        } else if (deleteProjectFile.rejected.match(result)) {
          setAnalysisError(result.payload as string);
        }
      } catch (error) {
        setAnalysisError("Failed to delete file. Please try again.");
      }
    },
    [projectId, projectFiles, dispatch, dialogs]
  );

  if (!projectId) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error">Invalid project ID</Alert>
      </Box>
    );
  }

  return (
    <Box
      sx={{ display: "flex", flexDirection: "column", height: "100%", p: 2 }}
    >
      {/* Breadcrumb Navigation */}
      <Box
        sx={{
          mt: "2px",
          mb: 2,
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
        }}
      >
        <Breadcrumbs aria-label="breadcrumb">
          <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
            <Link
              component={RouterLink}
              to="/projects"
              color="primary"
              underline="hover"
            >
              All Projects
            </Link>
          </Box>
          {project ? (
            <Box
              sx={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
              }}
            >
              <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                <Typography color="secondary" sx={{ fontWeight: 600 }}>
                  {project.name}
                </Typography>
                {/* {project && (
                  <Chip
                    label={project.status}
                    size="small"
                    color={getStatusColor(project.status)}
                  />
                )} */}
              </Box>
            </Box>
          ) : (
            <Typography color="text.secondary">Loading...</Typography>
          )}
        </Breadcrumbs>
        {/* {project && (
          <Typography variant="body2" color="text.secondary">
            Last updated: {formatDate(project.updated_at)}
          </Typography>
        )} */}
      </Box>

      {/* Top Panel - Project Information */}
      {/* <Paper elevation={0} sx={{ p: 1.5, mb: 2 }}>
        <Box
          sx={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "flex-start",
            mb: 1,
          }}
        >
          <Box sx={{ flex: 1 }}>
            {project ? (
              <Box
                sx={{
                  display: "flex",
                  flexDirection: "row",
                  gap: 2,
                  alignItems: "top",
                  justifyContent: "space-between",
                }}
              >
                <Box sx={{ display: "flex", flexDirection: "column", gap: 1 }}>
                  <Typography variant="h4" component="h1" gutterBottom>
                    {project.name}
                  </Typography>
                  {project.description && (
                    <Typography
                      variant="body1"
                      color="text.secondary"
                      gutterBottom
                    >
                      {project.description}
                    </Typography>
                  )}
                </Box>
                <Typography variant="body2" color="text.secondary">
                  Last updated: {formatDate(project.updated_at)}
                </Typography>
              </Box>
            ) : (
              <Typography variant="h4">Loading project...</Typography>
            )}
          </Box>
        </Box>
      </Paper> */}

      {/* Error Alert */}
      {(error || analysisError) && (
        <Alert
          severity="error"
          sx={{ mb: 2 }}
          onClose={() => {
            dispatch(clearError());
            setAnalysisError(null);
          }}
        >
          {error || analysisError}
        </Alert>
      )}

      {/* Progress Widget for File Processing */}
      {uploadJobId && (
        <ProgressWidget
          jobId={uploadJobId}
          title="File Processing"
          onDismiss={handleProgressDismiss}
          onComplete={handleProgressComplete}
        />
      )}

      {/* Loading State */}
      {loading && !project ? (
        <Box
          sx={{
            display: "flex",
            justifyContent: "center",
            alignItems: "center",
            minHeight: "400px",
          }}
        >
          <CircularProgress />
        </Box>
      ) : project ? (
        <>
          {/* Tabbed Interface */}
          <Paper sx={{ flex: 1, display: "flex", flexDirection: "column" }}>
            <Box sx={{ borderBottom: 1, borderColor: "divider" }}>
              <Tabs
                value={activeTab}
                onChange={(_, newValue) => setActiveTab(newValue)}
                sx={{
                  "& .MuiTab-root": {
                    color: "text.primary",
                  },
                }}
                aria-label="project dashboard tabs"
              >
                <Tab label="Overview" id="project-tab-0" />
                <Tab label="Sources" id="project-tab-1" />
                <Tab label="Inspect Data" id="project-tab-2" />
                <Tab label="Scenarios" id="project-tab-3" />
              </Tabs>
            </Box>

            {/* Tab 0: Overview */}
            <TabPanel value={activeTab} index={0}>
              <Box sx={{ p: 2 }}>
                <Typography variant="h6" gutterBottom>
                  Project Overview
                </Typography>

                {/* Project Description and Dates */}
                <Card
                  sx={{
                    mb: 3,
                    bgcolor: (theme) =>
                      theme.palette.mode === "dark"
                        ? "rgba(25, 118, 210, 0.08)"
                        : "rgba(25, 118, 210, 0.04)",
                  }}
                >
                  <CardContent>
                    <Box sx={{ display: "flex", alignItems: "center", mb: 2 }}>
                      <DescriptionIcon
                        sx={{
                          mr: 1.5,
                          fontSize: 24,
                          color: "primary.main",
                        }}
                      />
                      <Typography
                        variant="h6"
                        sx={{ fontWeight: 600, flex: 1 }}
                      >
                        {project.name}
                      </Typography>
                      <Tooltip title="Edit Project">
                        <IconButton
                          size="small"
                          onClick={() => setEditProjectDialogOpen(true)}
                          sx={{ ml: 1 }}
                        >
                          <EditIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                    </Box>
                    <Typography variant="body1" sx={{ mb: 3 }}>
                      {project.description || "No description provided."}
                    </Typography>
                    <Divider sx={{ my: 2 }} />
                    <Grid container spacing={3}>
                      <Grid item xs={12} md={6}>
                        <Box
                          sx={{ display: "flex", alignItems: "center", mb: 1 }}
                        >
                          <CalendarTodayIcon
                            sx={{
                              mr: 1,
                              fontSize: 18,
                              color: "text.secondary",
                            }}
                          />
                          <Typography
                            variant="subtitle2"
                            color="text.secondary"
                            sx={{ fontWeight: 500 }}
                          >
                            Date Created
                          </Typography>
                        </Box>
                        <Typography variant="body1">
                          {formatDate(project.created_at)}
                        </Typography>
                      </Grid>
                      <Grid item xs={12} md={6}>
                        <Box
                          sx={{ display: "flex", alignItems: "center", mb: 1 }}
                        >
                          <UpdateIcon
                            sx={{
                              mr: 1,
                              fontSize: 18,
                              color: "text.secondary",
                            }}
                          />
                          <Typography
                            variant="subtitle2"
                            color="text.secondary"
                            sx={{ fontWeight: 500 }}
                          >
                            Last Updated
                          </Typography>
                        </Box>
                        <Typography variant="body1">
                          {formatDate(project.updated_at)}
                        </Typography>
                      </Grid>
                    </Grid>
                  </CardContent>
                </Card>

                {/* Summary Section */}
                <Typography variant="h6" gutterBottom sx={{ mt: 3, mb: 2 }}>
                  Summary
                </Typography>
                <Grid container spacing={3}>
                  <Grid item xs={12} md={4}>
                    <Card
                      sx={{
                        height: "100%",
                        bgcolor: (theme) =>
                          theme.palette.mode === "dark"
                            ? "rgba(25, 118, 210, 0.08)"
                            : "rgba(25, 118, 210, 0.04)",
                        transition: "transform 0.2s, box-shadow 0.2s",
                        "&:hover": {
                          transform: "translateY(-2px)",
                          boxShadow: 3,
                        },
                      }}
                    >
                      <CardContent>
                        <Box
                          sx={{
                            display: "flex",
                            alignItems: "center",
                            mb: 2,
                          }}
                        >
                          <DescriptionIcon
                            sx={{
                              mr: 1.5,
                              fontSize: 24,
                              color: "primary.main",
                            }}
                          />
                          <Typography
                            variant="subtitle2"
                            color="text.secondary"
                            sx={{ fontWeight: 500 }}
                          >
                            Number of Documents
                          </Typography>
                        </Box>
                        {filesLoading ? (
                          <CircularProgress size={24} />
                        ) : (
                          <Typography
                            variant="h3"
                            sx={{ fontWeight: 700, mb: 1, textAlign: "center" }}
                          >
                            {getDocumentCount()}
                          </Typography>
                        )}
                        <Typography
                          variant="body2"
                          color="text.secondary"
                          sx={{ mt: 1 }}
                        >
                          Base Case:{" "}
                          {projectFiles?.base_case_files?.length || 0} | Tabular
                          Data: {projectFiles?.tabular_data_files?.length || 0}
                        </Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                  <Grid item xs={12} md={4}>
                    <Card
                      sx={{
                        height: "100%",
                        bgcolor: (theme) =>
                          theme.palette.mode === "dark"
                            ? "rgba(156, 39, 176, 0.08)"
                            : "rgba(156, 39, 176, 0.04)",
                        transition: "transform 0.2s, box-shadow 0.2s",
                        "&:hover": {
                          transform: "translateY(-2px)",
                          boxShadow: 3,
                        },
                      }}
                    >
                      <CardContent>
                        <Box
                          sx={{
                            display: "flex",
                            alignItems: "center",
                            mb: 2,
                          }}
                        >
                          <FolderSpecialIcon
                            sx={{
                              mr: 1.5,
                              fontSize: 24,
                              color: "secondary.main",
                            }}
                          />
                          <Typography
                            variant="subtitle2"
                            color="text.secondary"
                            sx={{ fontWeight: 500 }}
                          >
                            Number of Scenarios
                          </Typography>
                        </Box>
                        {scenariosLoading ? (
                          <CircularProgress size={24} />
                        ) : (
                          <Typography
                            variant="h3"
                            sx={{ fontWeight: 700, mb: 1, textAlign: "center" }}
                          >
                            {scenarios.length}
                          </Typography>
                        )}
                        <Typography
                          variant="body2"
                          color="text.secondary"
                          sx={{ mt: 1 }}
                        >
                          Total scenarios created for this project
                        </Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                  <Grid item xs={12} md={4}>
                    <Card
                      sx={{
                        height: "100%",
                        bgcolor: (theme) =>
                          theme.palette.mode === "dark"
                            ? "rgba(0, 150, 136, 0.08)"
                            : "rgba(0, 150, 136, 0.04)",
                        transition: "transform 0.2s, box-shadow 0.2s",
                        "&:hover": {
                          transform: "translateY(-2px)",
                          boxShadow: 3,
                        },
                      }}
                    >
                      <CardContent>
                        <Box
                          sx={{
                            display: "flex",
                            alignItems: "center",
                            mb: 2,
                          }}
                        >
                          <StorageIcon
                            sx={{
                              mr: 1.5,
                              fontSize: 24,
                              color: "success.main",
                            }}
                          />
                          <Typography
                            variant="subtitle2"
                            color="text.secondary"
                            sx={{ fontWeight: 500 }}
                          >
                            Total Size of Documents
                          </Typography>
                        </Box>
                        {filesLoading ? (
                          <CircularProgress size={24} />
                        ) : (
                          <Typography
                            variant="h3"
                            sx={{ fontWeight: 700, mb: 1, textAlign: "center" }}
                          >
                            {formatFileSize(calculateTotalDocumentSize())}
                          </Typography>
                        )}
                        <Typography
                          variant="body2"
                          color="text.secondary"
                          sx={{ mt: 1 }}
                        >
                          Combined size of all uploaded files
                        </Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                </Grid>

                {/* Clear All Project Data Button */}
                {(projectFiles?.base_case_files.length > 0 ||
                  projectFiles?.tabular_data_files.length > 0 ||
                  scenarios.length > 0) && (
                  <Box
                    sx={{ mt: 4, pt: 3, borderTop: 1, borderColor: "divider" }}
                  >
                    <Alert severity="warning" sx={{ mb: 2 }}>
                      <Typography
                        variant="body2"
                        sx={{ fontWeight: 600, mb: 1 }}
                      >
                        Danger Zone
                      </Typography>
                      <Typography variant="body2">
                        Clearing all project data will permanently delete all
                        scenarios, files, and extracted data. This action cannot
                        be undone.
                      </Typography>
                    </Alert>
                    <Button
                      variant="outlined"
                      color="error"
                      onClick={handleClearProjectData}
                      disabled={uploadingFiles}
                    >
                      Clear All Project Data
                    </Button>
                  </Box>
                )}
              </Box>
            </TabPanel>

            {/* Tab 1: Sources - File Upload */}
            <TabPanel value={activeTab} index={1}>
              <Box sx={{ p: 2 }}>
                <Typography variant="h6" gutterBottom>
                  Upload Source Documents
                </Typography>
                <Typography
                  variant="body2"
                  color="text.secondary"
                  sx={{ mb: 3 }}
                >
                  Upload base case reports and tabular data files. These
                  documents will be used to develop scenarios and perform
                  optionality analysis.
                </Typography>

                <Grid container spacing={3}>
                  {/* Base Case Documents Upload */}
                  <Grid item xs={12} md={6}>
                    <Card>
                      <CardContent>
                        <FileUpload
                          title="Base Case Reports"
                          description="Upload PDF documents containing base case reports"
                          supportedTypes={["PDF"]}
                          multiple={true}
                          maxFiles={10}
                          maxSizeInMB={25}
                          onFilesSelected={handleBaseCaseFilesSelected}
                          disabled={uploadingFiles}
                          showSelectedFiles={true}
                          numberOfFiles={baseCaseFiles.length}
                          clearTrigger={clearFileUploadTrigger}
                        />
                      </CardContent>
                    </Card>
                  </Grid>

                  {/* Tabular Data Files Upload */}
                  <Grid item xs={12} md={6}>
                    <Card>
                      <CardContent>
                        <FileUpload
                          title="Tabular Data Files"
                          description="Upload PDF, Excel, or CSV files containing tabular data"
                          supportedTypes={["PDF", "XLS", "CSV"]}
                          multiple={true}
                          maxFiles={10}
                          maxSizeInMB={25}
                          onFilesSelected={handleTabularDataFilesSelected}
                          disabled={uploadingFiles}
                          showSelectedFiles={true}
                          numberOfFiles={tabularDataFiles.length}
                          clearTrigger={clearFileUploadTrigger}
                        />
                      </CardContent>
                    </Card>
                  </Grid>
                </Grid>

                {/* Upload Button */}
                {(baseCaseFiles.length > 0 || tabularDataFiles.length > 0) && (
                  <Box
                    sx={{ mt: 3, display: "flex", justifyContent: "flex-end" }}
                  >
                    <Button
                      variant="contained"
                      onClick={handleUploadFiles}
                      disabled={
                        uploadingFiles ||
                        (baseCaseFiles.length === 0 &&
                          tabularDataFiles.length === 0)
                      }
                    >
                      {uploadingFiles ? "Uploading..." : "Upload Files"}
                    </Button>
                  </Box>
                )}

                {/* Document List */}
                <Box sx={{ mt: 4 }}>
                  {filesLoading ? (
                    <Box
                      sx={{ display: "flex", justifyContent: "center", p: 3 }}
                    >
                      <CircularProgress />
                    </Box>
                  ) : (
                    <DocumentList
                      baseCaseDocuments={
                        projectFiles?.base_case_files.map((f) => ({
                          file_id: f.file_id,
                          filename: f.filename,
                          length: f.length,
                          upload_date: f.upload_date,
                          content_type: f.content_type,
                          artifact_type: f.artifact_type,
                          sha256: f.sha256,
                        })) || []
                      }
                      tabularDataDocuments={
                        projectFiles?.tabular_data_files.map((f) => ({
                          file_id: f.file_id,
                          filename: f.filename,
                          length: f.length,
                          upload_date: f.upload_date,
                          content_type: f.content_type,
                          artifact_type: f.artifact_type,
                          sha256: f.sha256,
                        })) || []
                      }
                      onDownload={handleDownloadFile}
                      onDelete={handleDeleteFile}
                    />
                  )}
                </Box>
              </Box>
            </TabPanel>

            {/* Tab 2: Inspect Data */}
            <TabPanel value={activeTab} index={2}>
              <Box sx={{ p: 2 }}>
                <InspectDataView projectId={projectId} />
              </Box>
            </TabPanel>

            {/* Tab 3: Scenarios */}
            <TabPanel value={activeTab} index={3}>
              <Box sx={{ p: 1 }}>
                {selectedScenarioId ? (
                  <ScenarioDetails
                    scenarioId={selectedScenarioId}
                    projectId={projectId}
                    onBack={() => setSelectedScenarioId(null)}
                  />
                ) : (
                  <ScenariosList
                    projectId={projectId}
                    onScenarioSelect={(scenarioId) =>
                      setSelectedScenarioId(scenarioId)
                    }
                  />
                )}
              </Box>
            </TabPanel>
          </Paper>
        </>
      ) : (
        <Alert severity="warning">Project not found</Alert>
      )}

      {/* Edit Project Dialog */}
      {project && (
        <CreateProjectDialog
          open={editProjectDialogOpen}
          onClose={() => setEditProjectDialogOpen(false)}
          onSuccess={(updatedProjectId) => {
            // Refresh project data after successful update
            if (projectId) {
              dispatch(fetchProjectById(projectId) as any);
            }
          }}
          projectId={project.id}
          initialName={project.name}
          initialDescription={project.description || undefined}
        />
      )}
    </Box>
  );
};

export default ProjectDashboard;
