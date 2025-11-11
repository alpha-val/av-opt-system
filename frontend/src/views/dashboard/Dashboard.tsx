import React, { ReactNode } from "react";
import { Box, useTheme, useMediaQuery } from "@mui/material";
import { Routes, Route } from "react-router-dom";
import Nav from "../../components/Nav";
import ProjectList from "../project/ProjectList";
import ProjectDashboard from "../project/ProjectDashboard";
import SystemBaseDesign from "../project/SystemBaseDesign";
import ReportPreview from "../../components/project/ReportPreview";
import ScenarioDetails from "../scenario/ScenarioDetails";
import Settings from "../Settings/Settings";

interface DashboardProps {
  children?: ReactNode;
}

const Dashboard: React.FC<DashboardProps> = ({ children }) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down("sm"));

  return (
    <Box sx={{ display: "flex", height: "100vh", overflow: "hidden" }}>
      {/* Navigation Drawer */}
      <Nav />

      {/* Main Content Area */}
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          width: "100%",
          minHeight: "100vh",
          marginTop: isMobile ? "64px" : 0,
          padding: 3,
          overflow: "auto",
          transition: theme.transitions.create("margin", {
            easing: theme.transitions.easing.sharp,
            duration: theme.transitions.duration.leavingScreen,
          }),
        }}
      >
        {children || (
          <Routes>
            <Route path="/" element={<ProjectList />} />
            <Route path="/projects" element={<ProjectList />} />
            <Route
              path="/projects/:projectId"
              element={<ProjectDashboard />}
            />
            <Route
              path="/projects/:projectId/scenarios/:scenarioId"
              element={<ScenarioDetails />}
            />
            <Route
              path="/projects/:projectId/system-design"
              element={<SystemBaseDesign />}
            />
            <Route
              path="/projects/:projectId/report"
              element={<ReportPreview />}
            />
            <Route path="/settings" element={<Settings />} />
          </Routes>
        )}
      </Box>
    </Box>
  );
};

export default Dashboard;

