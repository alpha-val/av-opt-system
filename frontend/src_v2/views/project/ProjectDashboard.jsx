import React, { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useDispatch, useSelector } from "react-redux";
import {
  Box,
  Tabs,
  Tab,
  Paper,
  Breadcrumbs,
  Link,
  Typography,
} from "@mui/material";
import ProjectDetails from "./ProjectDetails";
import DocumentsTab from "./tabs/DocumentsTab";
import ScenariosTab from "./tabs/ScenariosTab";
import CostEstimatesTab from "./tabs/CostEstimatesTab";
import ViewDataTab from "./tabs/ViewDataTab";
import {
  fetchProjectById,
  selectCurrentProject,
} from "../../redux/projectSlice";

const ProjectDashboard = () => {
  const { projectId } = useParams();
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const project = useSelector(selectCurrentProject);
  const [activeTab, setActiveTab] = useState(0);

  // Fetch project details on mount
  useEffect(() => {
    if (projectId) {
      dispatch(fetchProjectById(projectId));
    }
  }, [dispatch, projectId]);

  const handleBack = () => {
    navigate("/");
  };

  const handleTabChange = (event, newValue) => {
    setActiveTab(newValue);
  };

  return (
    <Box sx={{ width: "100%", height: "100%", p: 3 }}>
      {/* Breadcrumbs */}
      <Breadcrumbs sx={{ mb: 3 }}>
        <Link
          component="button"
          variant="body1"
          onClick={handleBack}
          sx={{
            textDecoration: "none",
            "&:hover": { textDecoration: "underline" },
            cursor: "pointer",
          }}
        >
          Dashboard
        </Link>
        <Typography variant="body1" color="text.primary">
          {project?.name || "Loading..."}
        </Typography>
      </Breadcrumbs>

      {/* Tabs Navigation */}
      <Paper elevation={0} sx={{ borderBottom: 1, borderColor: "divider" }}>
        <Tabs
          value={activeTab}
          onChange={handleTabChange}
          aria-label="project dashboard tabs"
          sx={{
            px: 3,
            "& .MuiTab-root": {
              textTransform: "none",
              minHeight: 64,
              fontWeight: 500,
            },
          }}
        >
          <Tab label="Project Details" />
          <Tab label="Documents" />
          <Tab label="Inspect Data" />
          <Tab label="Scenarios" />
          <Tab label="Cost Estimates" />
        </Tabs>
      </Paper>

      {/* Tab Content */}
      <Box sx={{ width: "100%" }}>
        {activeTab === 0 && <ProjectDetails />}
        {activeTab === 1 && <DocumentsTab projectId={projectId} />}
        {activeTab === 2 && <ViewDataTab projectId={projectId} />}
        {activeTab === 3 && <ScenariosTab projectId={projectId} />}
        {activeTab === 4 && <CostEstimatesTab projectId={projectId} />}
      </Box>
    </Box>
  );
};

export default ProjectDashboard;
