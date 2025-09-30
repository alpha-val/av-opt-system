import { createTheme, responsiveFontSizes } from "@mui/material/styles";

// Function to create theme based on mode
const createAppTheme = (mode = "light") => {
  let theme = createTheme({
    palette: {
      mode,
      primary: {
        // main: "#e7b41cff", // vibrant blue (blue-600)
        // light: "#fbd064ff", // tint for hover or outlines (blue-400)
        // dark: "#d69316ff", // pressed/active (blue-800)
        // Alternative blue shades:
        main: "#587fd1ff", // vibrant blue (blue-600)
        light: "#60a5fa", // tint for hover or outlines (blue-400)
        dark: "#1e40af", // pressed/active (blue-800)
        veryLight: mode === "light" ? "#E8F1FD" : "#1a2332", // subtle background blue
        contrastText: "#ffffff",
      },
      secondary: {
        // rich mid–dark green (≈ PANTONE 7736 C)
        main: "#2E7D32",
        // one tint lighter for subtle hovers / outlines
        light: "#5DA65F",
        veryLight: mode === "light" ? "#E5F3E7" : "#1a2e1c", // soft pastel green, very subtle
        // one shade deeper for active / pressed states
        dark: "#1B5220",
        // readable on the darker greens
        contrastText: "#FFFFFF",
      },
      tertiary: {
        main: "#f97316", // vibrant orange
        light: "#fba94d", // hover/outline
        dark: "#c0560c", // pressed/active
        veryLight: mode === "light" ? "#FFF3E5" : "#2e1f0c", // soft background
        contrastText: "#FFFFFF",
      },
      error: {
        main: "#ee3333",
      },
      background: {
        default: mode === "light" ? "#f6fafd" : "#121212",
        paper: mode === "light" ? "#fff" : "#1e1e1e",
      },
      info: {
        main: "#f59e42", // orange accent
      },
      text: {
        primary: mode === "light" ? "#1a2a3a" : "#ffffff",
        secondary: mode === "light" ? "#6b7a90" : "#b0b0b0",
      },
      divider: mode === "light" ? "#e6eaf0" : "#2e2e2e",
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
            background:
              mode === "light"
                ? "linear-gradient(135deg, #f8f8f8ff 0%, #f8f8f8ff 50%, #f8f8f8ff 100%)"
                : "linear-gradient(135deg, #292929ff 0%, #292929ff 50%, #292929ff 100%)",
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
