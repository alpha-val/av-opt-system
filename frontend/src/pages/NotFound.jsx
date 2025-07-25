import React from "react";
import { Box, Paper, Typography } from '@mui/material';
// import NotFoundSVG from '../assets/media/not_found.png'; // adjust the path as needed

const NotFound = () => (
  <Box sx={{ m: 0, p: 3 }}>
    <Paper elevation={1} sx={{ borderRadius: 4, textAlign: "center" }}>
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
);

export default NotFound;