import React, { useCallback, useEffect, useState, useMemo } from "react";
import { Box } from "@mui/material";
import Header from "../components/widgets/Header.jsx";
import ProjectList from "./project/ProjectList.jsx";


const Dashboard = ({ onOpenProject }) => {
  return (
    <Box sx={{ p: 3, maxWidth: "100%", width: "100%" }}>
      <Header userName="Sid" />
      <ProjectList />
    </Box>
  );
};

export default Dashboard;
