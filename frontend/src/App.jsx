import React, { useContext } from "react";
import { useNavigate } from "react-router-dom";

import { useSelector } from "react-redux";
import NotFound from "./views/NotFound";
import { BrowserRouter as Router, Route, Routes } from "react-router-dom";
import DialogsProvider from "./hooks/useDialogs/DialogsProvider";
import MainGrid from "./views/MainGrid";
import AuthProvider from "./services/AuthProvider";
import { useThemeMode } from "./themes/ThemeContext";

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

const App = () => {
  return (
    <AppBackground>
      <AuthProvider>
        <DialogsProvider>
          <MainGrid />
        </DialogsProvider>
      </AuthProvider>
    </AppBackground>
  );
};

export default App;
