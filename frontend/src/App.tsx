import React, { ReactNode } from "react";
import { BrowserRouter as Router, Route, Routes } from "react-router-dom";
import { useSelector } from "react-redux";
import NotFound from "./views/NotFound";
import DialogsProvider from "./hooks/DialogsProvider";
import AuthProvider from "./services/AuthProvider";
import { useThemeMode } from "./themes/ThemeContext";
import Dashboard from "./views/dashboard/Dashboard";

interface AppBackgroundProps {
  children: ReactNode;
}

const AppBackground: React.FC<AppBackgroundProps> = ({ children }) => {
  const { theme } = useThemeMode();

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

const App: React.FC = () => {
  return (
    <AppBackground>
      <AuthProvider>
        <DialogsProvider>
          <Dashboard />
        </DialogsProvider>
      </AuthProvider>
    </AppBackground>
  );
};

export default App;

