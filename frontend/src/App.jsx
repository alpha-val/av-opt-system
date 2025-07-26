import React, { useContext } from "react";
import { useSelector } from "react-redux";
import LandingPage from "./pages/LandingPage";
import NotFound from "./pages/NotFound";
import { BrowserRouter as Router, Route, Routes } from "react-router-dom";
import ThemeProvider from "./themes/ThemeProvider";
const Test = () => {
  return <div>Test Component</div>;
};
const AppContent = () => {
  const { user } = useSelector((state) => state.users || {});
  return (
    <div style={{
      width: "100vw",
    }}>
      {/* Theme Toggle Widget */}
      {/* <div
        style={{
          position: "absolute",
          top: "10px",
          right: "30px",
          display: "flex",
          alignItems: "center",
          gap: "10px",
          cursor: "pointer",
        }}
        onClick={toggleTheme}
      >
        <span>{theme === "light" ? "🌞" : "🌙"}</span>
        <div
          style={{
            width: "40px",
            height: "15px",
            backgroundColor: theme === "light" ? "#ccc" : "#333",
            borderRadius: "10px",
            position: "relative",
            transition: "background-color 0.3s ease",
          }}
        >
          <div
            style={{
              width: "13px",
              height: "13px",
              backgroundColor: "#fff",
              borderRadius: "50%",
              position: "absolute",
              top: "1px",
              left: theme === "light" ? "2px" : "25px",
              transition: "left 0.3s ease",
            }}
          ></div>
        </div>
      </div> */}
      {/* Define Routes */}
      <Routes>
        <Route path="/" element={<LandingPage />} />
        {/* <Route path="/signup" element={<SignupWithOnboarding />} /> */}
        {/* <Route path="/signup_coach" element={<CoachSignup />} />
        <Route path="/signup" element={<UserSignup />} />
        <Route path="/onboard" element={<ProtectedRoute>
          <Onboarding />
        </ProtectedRoute>} /> */}
        <Route path="*" element={<NotFound />} />
      </Routes>
    </div>
  );
};

// Optional: global background gradient
const AppBackground = ({ children }) => (
  <div
    style={{
      minHeight: "100vh",
      width: "100vw",
      background: "linear-gradient(135deg, #f6fafd 0%, #faf8e6ff 50%,rgba(245, 224, 155, 1) 100%)",
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
          {/* <Nav /> */}
          <AppContent />
        </Router>
      </ThemeProvider>
    </AppBackground>
  );
};

export default App;
