import React, { useEffect, useState, useRef, useCallback } from "react";
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
} from "@mui/material";
import {
  ArrowBack as ArrowBackIcon,
  PlayArrow as PlayArrowIcon,
  Refresh as RefreshIcon,
} from "@mui/icons-material";
import {
  fetchProjectById,
  runAnalysis,
  uploadProjectFiles,
  listProjectFiles,
  downloadProjectFile,
  selectCurrentProject,
  selectProjectsLoading,
  selectProjectsError,
  selectProjectRunningAnalysis,
  selectProjectUploadingFiles,
  selectProjectFiles,
  selectProjectFilesLoading,
  clearError,
} from "../../redux/projectsSlice";
import { ProjectStatus } from "../../types/api";
import SystemBaseDesignContent, {
  SystemBaseDesignContentRef,
} from "../../components/project/SystemBaseDesignContent";
import FileUpload from "../../components/project/FileUpload";
import DocumentList, {
  DocumentMetadata,
} from "../../components/project/DocumentList";
import ScenariosList from "../../components/scenario/ScenariosList";
import ScenarioDetails from "../scenario/ScenarioDetails";

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
 * - Tabbed interface with System Details, Optionality Analysis, and Results tabs
 */
const ProjectDashboard: React.FC = () => {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const project = useSelector(selectCurrentProject);
  const loading = useSelector((state: any) => state.projects.loading.fetchById);
  const runningAnalysis = useSelector(selectProjectRunningAnalysis);
  const uploadingFiles = useSelector(selectProjectUploadingFiles);
  const filesLoading = useSelector(selectProjectFilesLoading);
  const projectFiles = useSelector(selectProjectFiles(projectId || ""));
  const error = useSelector(selectProjectsError);
  const [activeTab, setActiveTab] = useState<number>(0);
  const [analysisError, setAnalysisError] = useState<string | null>(null);
  const systemDesignRef = useRef<SystemBaseDesignContentRef>(null);
  const [filesChanged, setFilesChanged] = useState<number>(0); // Force re-render when files change
  const [selectedScenarioId, setSelectedScenarioId] = useState<string | null>(null); // Selected scenario in Scenarios tab

  // File upload state for Sources tab
  const [baseCaseFiles, setBaseCaseFiles] = useState<File[]>([]);
  const [tabularDataFiles, setTabularDataFiles] = useState<File[]>([]);

  /**
   * Fetch project data and handle URL hash for tab navigation
   */
  useEffect(() => {
    if (projectId) {
      // Only fetch if we don't have the project or it's a different project
      if (!project || project.id !== projectId) {
        dispatch(fetchProjectById(projectId) as any);
      }
      // Fetch project files
      dispatch(listProjectFiles(projectId) as any);
    }

    // Check URL hash to set active tab
    const hash = window.location.hash;
    if (hash === "#scenarios") {
      setActiveTab(1); // Scenarios tab is at index 1
    } else if (hash === "#sources") {
      setActiveTab(0); // Sources tab is at index 0
    } else if (hash === "#system-details") {
      setActiveTab(2); // System Details tab is at index 2
    }
  }, [projectId, project, dispatch]);

  /**
   * Clear selected scenario when switching away from Scenarios tab
   */
  useEffect(() => {
    if (activeTab !== 1) {
      setSelectedScenarioId(null);
    }
  }, [activeTab]);

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
   * Handle files change callback
   */
  const handleFilesChange = useCallback(() => {
    // Force re-render to update canRunAnalysis check
    setFilesChanged((prev) => prev + 1);
  }, []);

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
        // Clear selected files
        setBaseCaseFiles([]);
        setTabularDataFiles([]);
        // Refresh project and files
        await dispatch(fetchProjectById(projectId) as any);
        await dispatch(listProjectFiles(projectId) as any);
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
   * Handle file delete (placeholder - implement when backend supports it)
   */
  const handleDeleteFile = useCallback((fileId: string) => {
    // TODO: Implement file deletion when backend supports it
    console.log("Delete file:", fileId);
  }, []);

  /**
   * Handle running analysis
   */
  const handleRunAnalysis = async (): Promise<void> => {
    if (!projectId) return;

    setAnalysisError(null);
    dispatch(clearError());

    // Validate requirements
    if (!project) {
      setAnalysisError("Project data not loaded");
      return;
    }

    if (!project.global_objective_type || !project.global_objective_target) {
      setAnalysisError(
        "Objective details are required. Please set objective type and target in the System Details tab."
      );
      return;
    }

    // Check if files are selected (not yet uploaded)
    const selectedFiles = systemDesignRef.current?.getFiles();
    const hasSelectedFiles =
      selectedFiles &&
      selectedFiles.baseCaseFiles.length > 0 &&
      selectedFiles.tabularDataFiles.length > 0;

    // Check if files are already uploaded
    const hasUploadedFiles =
      project.base_case_documents &&
      project.base_case_documents.length > 0 &&
      project.tabular_data_documents &&
      project.tabular_data_documents.length > 0;

    // If files are selected but not uploaded, upload them first
    if (hasSelectedFiles && !hasUploadedFiles) {
      // Validate files
      const validation = systemDesignRef.current?.validateFiles();
      if (!validation || !validation.valid) {
        setAnalysisError(validation?.error || "File validation failed");
        return;
      }

      // Upload files
      const uploadSuccess = await systemDesignRef.current?.uploadFiles();
      if (!uploadSuccess) {
        setAnalysisError("Failed to upload files. Please try again.");
        return;
      }

      // Refresh project data to get updated document IDs
      await dispatch(fetchProjectById(projectId) as any);
    } else if (!hasSelectedFiles && !hasUploadedFiles) {
      setAnalysisError(
        "Please select base case documents and tabular data files before running analysis."
      );
      return;
    }

    // Dispatch run analysis action
    dispatch(runAnalysis(projectId) as any).then((result: any) => {
      if (runAnalysis.rejected.match(result)) {
        setAnalysisError(result.payload as string);
      }
    });
  };

  /**
   * Check if analysis can be run
   */
  const canRunAnalysis = (): boolean => {
    if (!project) return false;

    // Check objective details
    if (!project.global_objective_type || !project.global_objective_target) {
      return false;
    }

    // Check if files are selected (not yet uploaded)
    // Reference filesChanged to ensure this function re-evaluates when files change
    const _ = filesChanged; // Force re-evaluation when files change
    const selectedFiles = systemDesignRef.current?.getFiles();
    const hasSelectedFiles =
      selectedFiles &&
      selectedFiles.baseCaseFiles.length > 0 &&
      selectedFiles.tabularDataFiles.length > 0;

    // Analysis can run if we have objective details AND selected files
    return hasSelectedFiles;
  };

  if (!projectId) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error">Invalid project ID</Alert>
      </Box>
    );
  }

  return (
    <Box sx={{ display: "flex", flexDirection: "column", height: "100%" }}>
      {/* Breadcrumb Navigation */}
      <Box
        sx={{
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
                <Typography color="text.secondary">{project.name}</Typography>
                {project && (
                  <Chip
                    label={project.status}
                    size="small"
                    color={getStatusColor(project.status)}
                  />
                )}
              </Box>
            </Box>
          ) : (
            <Typography color="text.secondary">Loading...</Typography>
          )}
        </Breadcrumbs>
        {project && (
          <Typography variant="body2" color="text.secondary">
            Last updated: {formatDate(project.updated_at)}
          </Typography>
        )}
      </Box>

      {/* Top Panel - Project Information */}
      <Paper elevation={0} sx={{ p: 1.5, mb: 2 }}>
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
                {/* <Typography variant="body2" color="text.secondary">
                  Last updated: {formatDate(project.updated_at)}
                </Typography> */}
              </Box>
            ) : (
              <Typography variant="h4">Loading project...</Typography>
            )}
          </Box>
        </Box>
      </Paper>

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
                aria-label="project dashboard tabs"
              >
                <Tab label="Sources" id="project-tab-0" />
                <Tab label="Scenarios" id="project-tab-1" />
                <Tab label="System Details" id="project-tab-2" />
              </Tabs>
            </Box>

            {/* Tab 0: Sources - File Upload */}
            <TabPanel value={activeTab} index={0}>
              <Box sx={{ p: 3 }}>
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

            {/* Tab 1: Scenarios */}
            <TabPanel value={activeTab} index={1}>
              <Box sx={{ p: 3 }}>
                {selectedScenarioId ? (
                  <ScenarioDetails
                    scenarioId={selectedScenarioId}
                    projectId={projectId}
                    onBack={() => setSelectedScenarioId(null)}
                  />
                ) : (
                  <ScenariosList
                    projectId={projectId}
                    onScenarioSelect={(scenarioId) => setSelectedScenarioId(scenarioId)}
                  />
                )}
              </Box>
            </TabPanel>

            {/* Tab 2: System Details */}
            <TabPanel value={activeTab} index={2}>
              <Box sx={{ p: 1 }}>
                <Box
                  sx={{
                    display: "flex",
                    justifyContent: "flex-start",
                    mb: 2,
                    gap: 3,
                  }}
                >
                  <Button
                    variant="contained"
                    color="primary"
                    size="small"
                    startIcon={
                      runningAnalysis ? (
                        <CircularProgress size={20} />
                      ) : (
                        <PlayArrowIcon />
                      )
                    }
                    onClick={handleRunAnalysis}
                    disabled={runningAnalysis || !canRunAnalysis()}
                  >
                    {runningAnalysis
                      ? "Running Analysis..."
                      : project.status === ProjectStatus.PROCESSING ||
                        project.status === ProjectStatus.VALIDATION ||
                        project.status === ProjectStatus.COMPLETED
                      ? "Re-run Analysis"
                      : "Run Analysis"}
                  </Button>
                  {!canRunAnalysis() && (
                    <Alert severity="warning">
                      Please complete objective details and upload all required
                      documents before running analysis.
                    </Alert>
                  )}
                </Box>

                <SystemBaseDesignContent
                  ref={systemDesignRef}
                  projectId={projectId}
                  onFilesChange={handleFilesChange}
                />
              </Box>
            </TabPanel>
          </Paper>
        </>
      ) : (
        <Alert severity="warning">Project not found</Alert>
      )}
    </Box>
  );
};

export default ProjectDashboard;
