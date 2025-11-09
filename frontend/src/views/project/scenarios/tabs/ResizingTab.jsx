import React from "react";
import { Box, Alert } from "@mui/material";
import ResizingStatusCard from "../ResizingStatusCard";
import ResizedParametersTable from "../ResizedParametersTable";
import UserConstraintsForm from "../UserConstraintsForm";

const ResizingTab = ({ scenario }) => {
  return (
    <Box>
      <ResizingStatusCard scenario={scenario} />
      {scenario.resizing ? (
        <>
          <Box sx={{ mt: 3 }}>
            <ResizedParametersTable resizing={scenario.resizing} />
          </Box>
          <Box sx={{ mt: 3 }}>
            <UserConstraintsForm scenario={scenario} />
          </Box>
        </>
      ) : (
        <Alert severity="info" sx={{ mt: 2 }}>
          No resizing data available. Apply resizing to see results.
        </Alert>
      )}
    </Box>
  );
};

export default ResizingTab;

