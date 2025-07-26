// export default theme;
import { createTheme, responsiveFontSizes } from "@mui/material/styles";

let theme = createTheme({
  palette: {
    primary: {
      main: "#2563eb", // vibrant blue (blue-600)
      light: "#60a5fa", // tint for hover or outlines (blue-400)
      dark: "#1e40af", // pressed/active (blue-800)
      veryLight: "#E8F1FD", // 🧊 subtle background blue
      contrastText: "#ffffff",
    },
    secondary: {
      // rich mid–dark green (≈ PANTONE 7736 C)
      main: "#2E7D32",

      // one tint lighter for subtle hovers / outlines
      light: "#5DA65F",

      veryLight: "#E5F3E7", // soft pastel green, very subtle

      // one shade deeper for active / pressed states
      dark: "#1B5220",

      // readable on the darker greens
      contrastText: "#FFFFFF",
    },
    tertiary: {
      main: "#f97316", // vibrant orange
      light: "#fba94d", // hover/outline
      dark: "#c0560c", // pressed/active
      veryLight: "#FFF3E5", // 🌞 soft background
      contrastText: "#FFFFFF",
    },
    error: {
      main: "#ee3333",
    },
    background: {
      default: "#f6fafd",
      paper: "#fff",
    },
    info: {
      main: "#f59e42", // orange accent
    },
    text: {
      primary: "#1a2a3a",
      secondary: "#6b7a90",
    },
    divider: "#e6eaf0",
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
      fontSize: "4.8rem",
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
      fontSize: "1rem",
      "@media (max-width:600px)": { fontSize: "0.92rem" },
    },
    body2: {
      fontSize: "0.825rem",
      "@media (max-width:600px)": { fontSize: "0.78rem" },
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
      },
    },
  },
});

theme = responsiveFontSizes(theme);

export default theme;
