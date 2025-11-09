import React, { useState } from "react";
import { Box, Alert } from "@mui/material";
import ScenarioList from "../scenarios/ScenarioList";
import ScenarioFormDialog from "../scenarios/ScenarioFormDialog";
import ScenarioDetails from "../scenarios/ScenarioDetails";
import ScenarioWorkflow from "../scenarios/ScenarioWorkflow";

const ScenariosTab = ({ projectId }) => {
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showEditDialog, setShowEditDialog] = useState(false);
  const [editingScenario, setEditingScenario] = useState(null);
  const [viewingScenario, setViewingScenario] = useState(null);

  const handleCreateScenario = () => {
    setShowCreateDialog(true);
  };

  const handleEditScenario = (scenario) => {
    setEditingScenario(scenario);
    setShowEditDialog(true);
  };

  const handleViewScenario = (scenario) => {
    setViewingScenario(scenario);
  };

  const handleBackToList = () => {
    setViewingScenario(null);
  };

  const handleDialogClose = (success) => {
    setShowCreateDialog(false);
    setShowEditDialog(false);
    setEditingScenario(null);
    if (success) {
      // Refresh scenario list would happen automatically via Redux
    }
  };

  if (!projectId) {
    return (
      <Alert severity="error">Project ID is required</Alert>
    );
  }

  // Show scenario details view if viewing a scenario
  if (viewingScenario) {
    return (
      <Box sx={{ p: 3 }}>
        <ScenarioDetails
          scenarioId={viewingScenario.id}
          onBack={handleBackToList}
          onEdit={handleEditScenario}
        />
        <Box sx={{ mt: 3 }}>
          <ScenarioWorkflow scenario={viewingScenario} />
        </Box>
      </Box>
    );
  }

  // Show scenario list view
  return (
    <Box sx={{ p: 3 }}>
      <ScenarioList
        projectId={projectId}
        onViewScenario={handleViewScenario}
        onCreateScenario={handleCreateScenario}
        onEditScenario={handleEditScenario}
      />

      {/* Create Scenario Dialog */}
      <ScenarioFormDialog
        open={showCreateDialog}
        onClose={handleDialogClose}
        projectId={projectId}
      />

      {/* Edit Scenario Dialog */}
      <ScenarioFormDialog
        open={showEditDialog}
        onClose={handleDialogClose}
        projectId={projectId}
        scenario={editingScenario}
      />
    </Box>
  );
};

export default ScenariosTab;
