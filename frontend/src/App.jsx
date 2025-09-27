import React, { useContext } from "react";
import { useSelector } from "react-redux";
import NotFound from "./views/NotFound";
import { BrowserRouter as Router, Route, Routes } from "react-router-dom";
import DialogsProvider from "./hooks/useDialogs/DialogsProvider";
import MainGrid from "./views/MainGrid";
import AuthProvider from "./services/AuthProvider";
import { useThemeMode } from "./themes/ThemeContext";


// Optional: global background gradient using your custom theme
const AppBackground = ({ children }) => {
  const { theme, mode } = useThemeMode();

  return (
    <div
      style={{
        background: theme.palette.background.default,
        fontFamily: theme.typography.fontFamily,
        minHeight: "100vh",
        color: theme.palette.text.primary,
      }}
    >
      {children}
    </div>
  );
};

const AppContent = () => {
  return (
    <AuthProvider>
      <div style={{ width: "100vw" }}>
        {/* Define Routes - All routes are now protected */}
        <Routes>
          <Route path="/" element={<MainGrid />} />
          <Route path="/dashboard" element={<MainGrid />} />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </div>
    </AuthProvider>
  );
};

const App = () => {
  return (
    <AppBackground>
      <DialogsProvider>
        <AppContent />
      </DialogsProvider>
    </AppBackground>
  );
};

export default App;
