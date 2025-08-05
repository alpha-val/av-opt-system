import React, { useContext } from "react";
import { useSelector } from "react-redux";
import LandingPage from "./pages/LandingPage";
import NotFound from "./pages/NotFound";
import { BrowserRouter as Router, Route, Routes } from "react-router-dom";
import ThemeProvider from "./themes/ThemeProvider";
import Nav from "./widgets/Nav";
import Footer from "./widgets/Footer";
import Demo_v0 from "./pages/Demo-0"; // Adjust path if needed
import { Box } from "@mui/material";
const Test = () => {
  return <div>Test Component</div>;
};
const AppContent = () => {
  const { user } = useSelector((state) => state.users || {});
  return (
    <div style={{
      width: "100vw",
    }}>
      {/* Define Routes */}
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/demo" element={<Demo_v0 />} />
        <Route path="*" element={<NotFound />} />
      </Routes>
    </div>
  );
};

// Optional: global background gradient
const AppBackground = ({ children }) => (
  <div
    style={{
      // background: "linear-gradient(135deg, #e0e7ff 0%, #60a5fa 50%, #5f91fdff 100%)",
      fontFamily: "Inter, Roboto, Helvetica Neue, Arial, sans-serif",
    }}
  >
    {children}
  </div>
);

const App = () => {
  return (
    <AppBackground>
      <ThemeProvider>
        <Router>
          <Box sx={{ display: "flex", flexDirection: "column", minHeight: "100vh", overflow: "scroll"}}>
            <Nav />
            <Box sx={{ flex: 1, minHeight: 0, display: "flex", flexDirection: "column" }}>
              <AppContent />
            </Box>
            <Footer />
          </Box>
        </Router>
      </ThemeProvider>
    </AppBackground>
  );
};

export default App;
