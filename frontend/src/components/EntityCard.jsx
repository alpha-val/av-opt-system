import React from "react";
import { Card, CardContent, Typography, Box, Chip } from "@mui/material";

const EntityCard = ({ entity }) => {
    const { labels, properties } = entity;

    return (
        <Card elevation={3} sx={{ borderRadius: 2, mb: 2, p: 1}}>
            <CardContent>
                {/* Entity Labels */}
                <Box sx={{ mb: 2 }}>
                    {labels.map((label, index) => (
                        <Chip
                            key={index}
                            label={label}
                            color="primary"
                            sx={{ mr: 1 }}
                        />
                    ))}
                </Box>

                {/* Entity Name */}
                <Typography variant="h6" fontWeight={600} gutterBottom>
                    {properties.name || "Unnamed Entity"}
                </Typography>

                {/* Entity Properties */}
                <Box sx={{ mt: 1 }}>
                    {Object.entries(properties).map(([key, value]) => (
                        key !== "name" && (
                            <Typography
                                key={key}
                                variant="body2"
                                sx={{ mb: 1 }}
                            >
                                <strong>{key.replace(/_/g, " ")}:</strong> {key === "text" ? (value.length > 300 ? `${value.substring(0, 300)}...` : value) : value || "N/A"}
                            </Typography>
                        )
                    ))}
                </Box>
            </CardContent>
        </Card>
    );
};

export default EntityCard;