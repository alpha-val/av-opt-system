import React from "react";
import { Box, Typography } from "@mui/material";

const Footer = () => (
    <Box
        component="footer"
        sx={{
            bgcolor: "primary.main",
            color: "primary.contrastText",
            py: 3,
            textAlign: "center",
        }}
    >
        <Typography variant="body2">
            © {new Date().getFullYear()} OptPro — AI-Driven Mining Optionality Platform
        </Typography>
    </Box>
);

export default Footer;