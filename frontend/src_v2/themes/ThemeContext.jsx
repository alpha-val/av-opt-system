import React, { createContext, useContext, useState, useEffect } from 'react';
import { ThemeProvider } from '@mui/material/styles';
import { createAppTheme } from '../themes/MUITheme'; // Import your custom theme

// Create the context
const ThemeContext = createContext();

// Custom hook to use the theme context
export const useThemeMode = () => {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useThemeMode must be used within a ThemeContextProvider');
  }
  return context;
};

// Theme provider component
export const ThemeContextProvider = ({ children }) => {
  const [mode, setMode] = useState(() => {
    // Get saved theme from localStorage or default to 'light'
    return localStorage.getItem('themeMode') || 'light';
  });

  // Save theme mode to localStorage whenever it changes
  useEffect(() => {
    localStorage.setItem('themeMode', mode);
  }, [mode]);

  const toggleColorMode = () => {
    setMode((prevMode) => (prevMode === 'light' ? 'dark' : 'light'));
  };

  // Use your custom theme creator function
  const theme = createAppTheme(mode);

  const contextValue = {
    mode,
    toggleColorMode,
    theme,
  };

  return (
    <ThemeContext.Provider value={contextValue}>
      <ThemeProvider theme={theme}>
        {children}
      </ThemeProvider>
    </ThemeContext.Provider>
  );
};

export default ThemeContextProvider;