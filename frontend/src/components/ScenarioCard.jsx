import React from "react";
import {
  Card,
  CardContent,
  CardActions,
  Typography,
  Chip,
  IconButton,
  Box,
  Button,
} from "@mui/material";
import {
  MoreVert as MoreVertIcon,
  TrendingUp,
  AttachMoney,
  Speed,
} from "@mui/icons-material";

const ScenarioCard = ({ scenario, onClick, onMenuClick }) => {
  const getGoalIcon = (goal) => {
    switch (goal) {
      case "increase_production":
        return <TrendingUp />;
      case "reduce_cost":
        return <AttachMoney />;
      default:
        return <Speed />;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case "ready":
        return "success";
      case "analyzing":
        return "warning";
      case "draft":
        return "default";
      case "archived":
        return "error";
      default:
        return "default";
    }
  };

  return (
    <Card
      sx={{
        cursor: "pointer",
        "&:hover": { boxShadow: 4 },
        transition: "box-shadow 0.3s",
        height: "100%",
        display: "flex",
        flexDirection: "column",
        maxWidth: 400,
        mx: "auto",
      }}
      onClick={() => onClick(scenario.id)}
    >
      <CardContent sx={{ flexGrow: 1 }}>
        <Box
          sx={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "flex-start",
            mb: 2,
          }}
        >
          <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
            {getGoalIcon(scenario.goal)}
            <Typography variant="h6" component="div">
              {scenario.name}
            </Typography>
          </Box>
          <IconButton size="small" onClick={(e) => onMenuClick(e, scenario)}>
            <MoreVertIcon />
          </IconButton>
        </Box>

        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          {scenario.description || "No description"}
        </Typography>

        <Box sx={{ mb: 2 }}>
          <Chip
            label={scenario.status}
            color={getStatusColor(scenario.status)}
            size="small"
            sx={{ mr: 1 }}
          />
          <Chip label={scenario.change_type} variant="outlined" size="small" />
        </Box>
      </CardContent>

      <CardActions>
        <Button
          size="small"
          onClick={(e) => {
            e.stopPropagation();
            onClick(scenario.id);
          }}
        >
          View Details
        </Button>
      </CardActions>
    </Card>
  );
};

export default ScenarioCard;
