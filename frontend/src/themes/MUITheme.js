import { createTheme, responsiveFontSizes } from "@mui/material/styles";

// Function to create theme based on mode
const createAppTheme = (mode = "light") => {
  const isLight = mode === "light";

  let theme = createTheme({
    palette: {
      mode,
      primary: {
        // LIGHT: your existing blue brand
        // DARK: Golden yellow (muted, less pronounced)
        main: isLight ? "#587fd1ff" : "#D4AF37",
        light: isLight ? "#60a5fa" : "#E6C89A",
        dark: isLight ? "#1e40af" : "#B8941A",
        veryLight: isLight ? "#E8F1FD" : "#2a2418",
        contrastText: isLight ? "#ffffff" : "#000000",
      },
      secondary: {
        // LIGHT: your green
        // DARK: Muted teal (less pronounced)
        main: isLight ? "#2E7D32" : "#4a9b8e",
        light: isLight ? "#5DA65F" : "#6bb3a8",
        veryLight: isLight ? "#E5F3E7" : "#1a2d2a",
        dark: isLight ? "#1B5220" : "#3a7a6f",
        contrastText: isLight ? "#FFFFFF" : "#ffffff",
      },
      tertiary: {
        // DARK: Muted orange (less pronounced)
        main: isLight ? "#f97316" : "#c97d4a",
        light: isLight ? "#fba94d" : "#d99a6b",
        dark: isLight ? "#c0560c" : "#a8653a",
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
        // Additional consistent background shades for dark mode
        ...(isLight
          ? {}
            : {
              elevated: "#252526", // Sidebar, navigation
              surface: "#2d2d30", // Main content area
              card: "#252526", // Card backgrounds (darker than surface)
              cardHover: "#2d2d30", // Card hover state (lighter than card, same as surface)
              tableHeader: "#2d2d30", // Table headers
              tableRow: "#252526", // Table row base
              tableRowAlt: "#2d2d30", // Table row alternate
            }),
      },
      info: {
        main: "#f59e42", // orange accent
      },
      text: {
        primary: isLight ? "#1a2a3a" : "#e5e5e5",
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
        fontSize: "2.25rem", // ~36px
        "@media (max-width:600px)": { fontSize: "1.875rem" },
      },
      h2: {
        fontSize: "1.875rem", // ~30px
        "@media (max-width:600px)": { fontSize: "1.5rem" },
      },
      h3: {
        fontSize: "1.5rem", // ~24px
        "@media (max-width:600px)": { fontSize: "1.25rem" },
      },
      h4: {
        fontSize: "1.25rem", // ~20px
        "@media (max-width:600px)": { fontSize: "1.125rem" },
      },
      h5: {
        fontSize: "1.125rem", // ~18px
        "@media (max-width:600px)": { fontSize: "1rem" },
      },
      h6: {
        fontSize: "1rem", // ~16px
        "@media (max-width:600px)": { fontSize: "0.9375rem" },
      },
      body1: {
        fontSize: "1rem", // ~16px - increased from 0.75rem
        "@media (max-width:600px)": { fontSize: "0.875rem" },
      },
      body2: {
        fontSize: "0.875rem", // ~14px - increased from 0.7rem
        "@media (max-width:600px)": { fontSize: "0.8125rem" },
      },
      // not native MUI variant, but fine if you're using it in sx
      body3: {
        fontSize: "0.75rem", // ~12px - increased from 0.6rem
        lineHeight: 1,
        color: isLight ? "#3a3a3a" : "#c0c0c0",
        "@media (max-width:600px)": { fontSize: "0.6875rem" },
      },
      subtitle1: {
        fontSize: "1rem", // ~16px - increased from 0.8rem
        "@media (max-width:600px)": { fontSize: "0.875rem" },
      },
      subtitle2: {
        fontSize: "0.875rem", // ~14px - increased from 0.7rem
        "@media (max-width:600px)": { fontSize: "0.75rem" },
      },
      caption: {
        fontSize: "0.75rem", // ~12px - increased from 0.6rem
        "@media (max-width:600px)": { fontSize: "0.6875rem" },
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
      MuiCard: {
        styleOverrides: {
          root: {
            ...(isLight
              ? {}
              : {
                  backgroundColor: "#2d2d30",
                  "&:hover": {
                    backgroundColor: "#3c3c3c",
                  },
                }),
          },
        },
      },
      MuiTableHead: {
        styleOverrides: {
          root: {
            ...(isLight
              ? {}
              : {
                  backgroundColor: "#2d2d30",
                }),
          },
        },
      },
      MuiTableRow: {
        styleOverrides: {
          root: {
            ...(isLight
              ? {}
              : {
                  "&:nth-of-type(even)": {
                    backgroundColor: "#252526",
                  },
                  "&:nth-of-type(odd)": {
                    backgroundColor: "#2d2d30",
                  },
                  "&:hover": {
                    backgroundColor: "#3c3c3c",
                  },
                }),
          },
        },
      },
      MuiPaper: {
        styleOverrides: {
          root: {
            ...(isLight
              ? {}
              : {
                  backgroundColor: "#1e1e1e",
                }),
          },
          elevation1: {
            ...(isLight
              ? {}
              : {
                  backgroundColor: "#2d2d30",
                }),
          },
          elevation2: {
            ...(isLight
              ? {}
              : {
                  backgroundColor: "#2d2d30",
                }),
          },
          elevation3: {
            ...(isLight
              ? {}
              : {
                  backgroundColor: "#3c3c3c",
                }),
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
