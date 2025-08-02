import React from "react";
import { Box, Paper, Typography } from '@mui/material';
import Footer from "../widgets/Footer"; // Adjust path if needed
import Nav from "../widgets/Nav"; // Ensure this path is correct

const Demo = () => (
  <Box
    sx={{
      minHeight: "100vh",
      display: "flex",
      flexDirection: "column",
      justifyContent: "center",
      bgcolor: "#f5f5f5",
    }}
  >
    <Nav />
    <Box sx={{ flex: 1, display: "flex", alignItems: "center", justifyContent: "center" }}>
      <Paper elevation={1} sx={{ borderRadius: 4, textAlign: "center", p: 4 }}>
        <Box sx={{ py: 0 }}>
          {/* <img
            src={NotFoundSVG}
            alt="404 Not Found"
            style={{ maxWidth: 320, width: "100%", margin: "0 auto", display: "block" }}
          /> */}
        </Box>
        <Typography sx={{ fontSize:{ sm: "0.9rem", md: "1.4rem", lg: "2rem"}, fontWeight: "600"}}>Page Not Found</Typography>
        <p>The page you are looking for does not exist.</p>
      </Paper>
    </Box>
    <Footer />
  </Box>
);

export default Demo;