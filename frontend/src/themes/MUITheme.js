import { createTheme, responsiveFontSizes } from "@mui/material/styles";

// Function to create theme based on mode
const createAppTheme = (mode = "light") => {
  const isLight = mode === "light";

  let theme = createTheme({
    palette: {
      mode,
      primary: {
        // LIGHT: your existing blue brand
        // DARK: Material-style purple
        main: isLight ? "#587fd1ff" : "#bb86fc",
        light: isLight ? "#60a5fa" : "#cf9bff",
        dark: isLight ? "#1e40af" : "#3700b3",
        veryLight: isLight ? "#E8F1FD" : "#1a1724",
        contrastText: isLight ? "#ffffff" : "#000000",
      },
      secondary: {
        // LIGHT: your green
        // DARK: Material secondary teal
        main: isLight ? "#2E7D32" : "#03dac6",
        light: isLight ? "#5DA65F" : "#66fff9",
        veryLight: isLight ? "#E5F3E7" : "#00332e",
        dark: isLight ? "#1B5220" : "#00a896",
        contrastText: isLight ? "#FFFFFF" : "#000000",
      },
      tertiary: {
        // keep your orange accent in both modes
        main: "#f97316",
        light: "#fba94d",
        dark: "#c0560c",
        veryLight: isLight ? "#FFF3E5" : "#2e1f0c",
        contrastText: "#FFFFFF",
      },
      error: {
        main: isLight ? "#ee3333" : "#cf6679",
        light: isLight ? "#ff6666" : "#ff99a4",
        lighter: isLight ? "#ff9999" : "#ffb3c0",
        veryLight: isLight ? "#ffe5e5" : "#3a1a1a",
        dark: isLight ? "#cc0000" : "#b0003a",
        contrastText: isLight ? "#ffffff" : "#000000",
      },
      background: {
        default: isLight ? "#f6fafd" : "#121212",
        paper: isLight ? "#ffffff" : "#1e1e1e",
      },
      info: {
        main: "#f59e42", // orange accent
      },
      text: {
        primary: isLight ? "#1a2a3a" : "#ffffff",
        secondary: isLight ? "#6b7a90" : "#b0b0b0",
      },
      divider: isLight ? "#e6eaf0" : "#383838",
    },
    typography: {
      fontFamily: [
        "-apple-system",
        "BlinkMacSystemFont",
        '"Segoe UI"',
        "Roboto",
        "Arial",
        "sans-serif",
      ].join(","),
      h1: {
        fontSize: "2.25rem",
        "@media (max-width:600px)": { fontSize: "2.5rem" },
      },
      h2: {
        fontSize: "1.7rem",
        "@media (max-width:600px)": { fontSize: "1.2rem" },
      },
      h3: {
        fontSize: "1.3rem",
        "@media (max-width:600px)": { fontSize: "1.05rem" },
      },
      h4: {
        fontSize: "1.1rem",
        "@media (max-width:600px)": { fontSize: "0.98rem" },
      },
      h5: {
        fontSize: "1rem",
        "@media (max-width:600px)": { fontSize: "0.875rem" },
      },
      h6: {
        fontSize: "0.95rem",
        "@media (max-width:600px)": { fontSize: "0.9rem" },
      },
      body1: {
        fontSize: "0.85rem",
        "@media (max-width:600px)": { fontSize: "0.8rem" },
      },
      body2: {
        fontSize: "0.75rem",
        "@media (max-width:600px)": { fontSize: "0.775rem" },
      },
      // not native MUI variant, but fine if you're using it in sx
      body3: {
        fontSize: "0.6rem",
        lineHeight: 1,
        color: isLight ? "#3a3a3a" : "#c0c0c0",
        "@media (max-width:600px)": { fontSize: "0.6rem" },
      },
    },
    spacing: 8,
    components: {
      MuiToolbar: {
        styleOverrides: {
          root: {
            minHeight: 48,
          },
        },
      },
      MuiContainer: {
        styleOverrides: {
          root: {
            paddingLeft: "8px",
            paddingRight: "8px",
            "@media (min-width:600px)": {
              paddingLeft: "24px",
              paddingRight: "24px",
            },
          },
        },
      },
      MuiPaper: {
        styleOverrides: {
          root: {
            padding: "16px",
            "@media (max-width:600px)": {
              padding: "8px",
            },
          },
        },
      },
      MuiButton: {
        styleOverrides: {
          root: {
            minHeight: "32px",
            fontSize: "1rem",
            "@media (max-width:600px)": {
              minHeight: "28px",
              fontSize: "0.92rem",
              padding: "4px 10px",
            },
          },
          sizeSmall: {
            fontSize: "0.7rem",
            padding: "3px 8px",
            minHeight: "24px",
          },
          sizeMedium: {
            fontSize: "0.8rem",
            padding: "3px 8px",
            minHeight: "30px",
          },
        },
      },
      MuiCssBaseline: {
        styleOverrides: {
          body: {
            background: isLight
              ? "linear-gradient(135deg, #f8f8f8ff 0%, #f8f8f8ff 50%, #f8f8f8ff 100%)"
              : "linear-gradient(135deg, #121212 0%, #1e1e1e 50%, #121212 100%)",
            minHeight: "100vh",
          },
        },
      },
    },
  });

  return responsiveFontSizes(theme);
};

// Export theme creator function
export { createAppTheme };

// Default light theme export for backward compatibility
export default createAppTheme("light");
