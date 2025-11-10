import React from "react";
import {
  Box,
  Paper,
  Stepper,
  Step,
  StepLabel,
  StepContent,
  Button,
  Typography,
  Chip,
} from "@mui/material";
import { useDispatch, useSelector } from "react-redux";
import {
  analyzeScenario,
  resizeSystem,
  buildRecommendation,
  prepareCostEstimation,
  generateReport,
  selectAnalysisLoading,
  selectResizingLoading,
  selectRecommendationLoading,
  selectCostEstimationLoading,
  selectReportLoading,
} from "../../../redux/scenarioSlice";

const ScenarioWorkflow = ({ scenario }) => {
  const dispatch = useDispatch();
  const analysisLoading = useSelector((state) =>
    selectAnalysisLoading(state, scenario.id)
  );
  const resizingLoading = useSelector((state) =>
    selectResizingLoading(state, scenario.id)
  );
  const recommendationLoading = useSelector((state) =>
    selectRecommendationLoading(state, scenario.id)
  );
  const costEstimationLoading = useSelector((state) =>
    selectCostEstimationLoading(state, scenario.id)
  );
  const reportLoading = useSelector((state) =>
    selectReportLoading(state, scenario.id)
  );

  const steps = [
    {
      label: "Create Scenario",
      description: "Scenario has been created",
      completed: !!scenario,
      action: null,
    },
    {
      label: "Analyze",
      description: "Analyze entities and identify local objectives",
      completed: !!scenario.analysis,
      loading: analysisLoading,
      action: () => dispatch(analyzeScenario(scenario.id)),
    },
    {
      label: "Resize System",
      description: "Apply system resizing based on global objective",
      completed: !!scenario.resizing,
      loading: resizingLoading,
      disabled: !scenario.analysis,
      action: () =>
        dispatch(resizeSystem({ scenarioId: scenario.id, userConstraints: [] })),
    },
    {
      label: "Build Recommendations",
      description: "Generate approach options and recommendations",
      completed: !!scenario.recommendation,
      loading: recommendationLoading,
      disabled: !scenario.analysis,
      action: () => dispatch(buildRecommendation(scenario.id)),
    },
    {
      label: "Cost Estimation",
      description: "Prepare cost estimation data",
      completed: !!scenario.cost_estimation,
      loading: costEstimationLoading,
      disabled: !scenario.analysis,
      action: () =>
        dispatch(
          prepareCostEstimation({ scenarioId: scenario.id, generateEstimates: false })
        ),
    },
    {
      label: "Generate Report",
      description: "Generate final report",
      completed: false, // Reports are generated on-demand
      loading: reportLoading,
      action: () =>
        dispatch(generateReport({ scenarioId: scenario.id, format: "markdown" })),
    },
  ];

  const activeStep = steps.findIndex(
    (step, index) => !step.completed && index > 0
  );

  return (
    <Paper sx={{ p: 3 }}>
      <Typography variant="h6" gutterBottom>
        Scenario Workflow
      </Typography>
      <Stepper activeStep={activeStep} orientation="vertical">
        {steps.map((step, index) => (
          <Step key={step.label} completed={step.completed}>
            <StepLabel
              optional={
                step.completed ? (
                  <Chip label="Completed" size="small" color="success" />
                ) : null
              }
            >
              {step.label}
            </StepLabel>
            <StepContent>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                {step.description}
              </Typography>
              {step.action && (
                <Button
                  variant="contained"
                  onClick={step.action}
                  disabled={step.loading || step.disabled}
                  size="small"
                >
                  {step.loading
                    ? "Running..."
                    : step.completed
                    ? "Re-run"
                    : "Run"}
                </Button>
              )}
            </StepContent>
          </Step>
        ))}
      </Stepper>
    </Paper>
  );
};

export default ScenarioWorkflow;

