import React from "react";
import { Box, Typography, useTheme, alpha } from "@mui/material";
import logoLight from "../media/logo-light.png";
import logoDark from "../media/logo-dark.png";
import { useThemeMode } from "../themes/ThemeContext";

/**
 * Banner component with AlphaVal branding and punchline.
 * 
 * Displays at the top of the main content area with:
 * - AlphaVal Pro logo
 * - Company name
 * - Tagline/punchline
 */
const Banner: React.FC = () => {
  const theme = useTheme();
  const { mode } = useThemeMode();
  const logo = mode === "dark" ? logoDark : logoLight;

  return (
    <Box
      sx={{
        background: `linear-gradient(135deg, ${alpha(theme.palette.primary.main, 0.1)} 0%, ${alpha(theme.palette.secondary.main, 0.05)} 100%)`,
        borderBottom: `1px solid ${alpha(theme.palette.divider, 0.25)}`,
        py: 2,
        px: 2,
        mb: 2,
        borderRadius: 0,
        boxShadow: `0 2px 8px ${alpha(theme.palette.primary.main, 0.08)}`,
        width: "100%",
      }}
    >
      {/* Logo */}
      {/* <Box
        sx={{
          display: "flex",
          alignItems: "center",
          flexShrink: 0,
        }}
      >
        <img
          src={logo}
          alt="AlphaVal Pro Logo"
          style={{
            width: 56,
            height: 56,
            objectFit: "contain",
            filter: "drop-shadow(0px 2px 4px rgba(0, 0, 0, 0.1))",
          }}
        />
      </Box> */}

      {/* Branding and Punchline */}
      <Box sx={{ flexGrow: 1, minWidth: 0, display: "flex", flexDirection: "row", alignItems: "center", gap: 2, justifyContent: "space-between"  }}>
        <Box sx={{ display: "flex", flexDirection: "row", alignItems: "center", gap: 2 }}>
        <Typography
          variant="h5"
          sx={{
            fontWeight: 600,
            color: theme.palette.primary.main,
            letterSpacing: "-0.02em",
            textAlign: "center",
          }}
        >
          AlphaVal Pro
        </Typography>
        <Typography
          variant="body2"
          sx={{
            color: theme.palette.text.secondary,
            fontStyle: "italic",
            opacity: 0.85,
            textAlign: "center",
          }}
        >
            Mining optionality through intelligent scenario analysis
          </Typography>
        </Box>
        <Box>
          <Typography variant="body2" color="text.secondary">
            {/* Today's date */}
            {new Date().toLocaleDateString()}
          </Typography>
        </Box>
      </Box>
    </Box>
  );
};

export default Banner;

