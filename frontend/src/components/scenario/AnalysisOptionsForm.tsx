import React from "react";
import {
  Box,
  Card,
  CardContent,
  Typography,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert,
} from "@mui/material";

interface AnalysisOptionsFormProps {
  useV2Workflow: boolean;
  extractSummary: boolean;
  extractionScope?: "exact" | "with_relationships" | "with_context";
  onUseV2WorkflowChange: (value: boolean) => void;
  onExtractSummaryChange: (value: boolean) => void;
  onExtractionScopeChange?: (value: "exact" | "with_relationships" | "with_context") => void;
}

/**
 * Analysis Options Form Component
 * 
 * Displays V2 workflow options including workflow version,
 * extract summary toggle, and extraction scope.
 */
const AnalysisOptionsForm: React.FC<AnalysisOptionsFormProps> = ({
  useV2Workflow,
  extractSummary,
  extractionScope,
  onUseV2WorkflowChange,
  onExtractSummaryChange,
  onExtractionScopeChange,
}) => {
  return (
    <Card sx={{ mt: 3 }}>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Analysis Options
        </Typography>
        <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
          {/* Use V2 Workflow Toggle */}
          <FormControl fullWidth>
            <InputLabel>Workflow Version</InputLabel>
            <Select
              value={useV2Workflow ? "v2" : "v1"}
              onChange={(e) => onUseV2WorkflowChange(e.target.value === "v2")}
              label="Workflow Version"
            >
              <MenuItem value="v1">V1 (Extract all entities first)</MenuItem>
              <MenuItem value="v2">
                V2 (Recommendations-first, targeted extraction)
              </MenuItem>
            </Select>
          </FormControl>

          {/* V2-specific options */}
          {useV2Workflow && (
            <>
              {/* Extract Summary Toggle */}
              <FormControl fullWidth>
                <InputLabel>Extract Summary</InputLabel>
                <Select
                  value={extractSummary ? "true" : "false"}
                  onChange={(e) => onExtractSummaryChange(e.target.value === "true")}
                  label="Extract Summary"
                >
                  <MenuItem value="false">No</MenuItem>
                  <MenuItem value="true">Yes</MenuItem>
                </Select>
              </FormControl>

              <Alert severity="info" sx={{ mt: 1 }}>
                <Typography variant="body2">
                  <strong>V2 Workflow:</strong> First analyzes the document
                  to generate recommendations and identify relevant entities,
                  then extracts only those entities. More targeted and
                  efficient than V1.
                </Typography>
              </Alert>
            </>
          )}
        </Box>
      </CardContent>
    </Card>
  );
};

export default AnalysisOptionsForm;

