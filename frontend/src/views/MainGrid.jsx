import React, { useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import { getCurrentUser } from "../redux/authSlice";
import { Box, useTheme, useMediaQuery } from "@mui/material";
import Nav from "./Nav";
import { Routes, Route } from "react-router-dom";
import Dashboard from "./Dashboard";
import Settings from "./settings/Settings";

const MainGrid = () => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down("sm"));
  const isAdmin = useSelector((state) => state.auth.isAdmin);

  return (
    <Box sx={{ display: "flex", height: "100vh" }}>
      {/* Nav is already included */}
      <Nav />

      {/* Main Content Area */}
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          width: "100%",
          minHeight: "100vh",
          marginTop: isMobile ? "64px" : 0,
          transition: theme.transitions.create("margin", {
            easing: theme.transitions.easing.sharp,
            duration: theme.transitions.duration.leavingScreen,
          }),
        }}
      >
        {/* Define Routes for Dashboard and Settings */}
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/settings" element={<Settings />} />
        </Routes>
      </Box>
    </Box>
  );
};

export default MainGrid;
