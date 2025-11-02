import React from "react";
import { Box, Typography } from "@mui/material";

const Header = ({ userName = "User" }) => {
  return (
    <Box
      sx={{
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        mb: 4,
        borderBottom: 1,
        borderColor: "divider",
        pb: 2,
      }}
    >
      <Typography variant="h4" fontWeight="bold">
        Welcome, {userName}
      </Typography>
      <Box sx={{ display: "flex", gap: 2, justifyContent: "flex-start" }}>
        <Typography variant="body2" color="text.secondary" align="right">
          AI can make mistakes. Please review outputs carefully.
        </Typography>
        <Typography variant="body2" color="text.secondary">
          {new Date().toLocaleDateString("en-US", {
            year: "numeric",
            month: "short",
            day: "2-digit",
            hour: "2-digit",
            minute: "2-digit",
            timeZoneName: "short",
          })}
        </Typography>
      </Box>
    </Box>
  );
};

export default Header;
