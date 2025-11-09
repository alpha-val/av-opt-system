import React from "react";
import { Box, Alert } from "@mui/material";
import ReportViewer from "../ReportViewer";

const ReportTab = ({ scenario }) => {
  return (
    <Box>
      <ReportViewer scenario={scenario} />
    </Box>
  );
};

export default ReportTab;

