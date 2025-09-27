import React from "react";
import { Box } from "@mui/material";
import EarthMover from "../media/images/bg-earth-mover-1.jpg"
const BackgroundDesignElements = ({ hero = false }) => (
    <>
        {/* Hero section earth mover image */}
        {hero && (
            <Box
                component="img"
                src={EarthMover}
                alt="Earth Mover"
                sx={{
                    position: "absolute",
                    bottom: { xs: -40, md: 0 },
                    right: { xs: -80, md: 40 },
                    width: { xs: "320px", md: "600px" },
                    opacity: 0.9,
                    zIndex: 1,
                    pointerEvents: "none",
                    userSelect: "none",
                }}
            />
        )}
        {/* Top left blue box */}
        <Box
            sx={{
                position: "fixed",
                top: 40,
                left: 40,
                width: 120,
                height: 120,
                bgcolor: "rgba(33, 150, 243, 0.10)",
                borderRadius: 4,
                zIndex: 0,
                pointerEvents: "none",
            }}
        />
        {/* Top right green circle */}
        <Box
            sx={{
                position: "fixed",
                top: 120,
                right: 120,
                width: 60,
                height: 60,
                bgcolor: "rgba(76, 175, 80, 0.10)",
                borderRadius: "50%",
                zIndex: 0,
                pointerEvents: "none",
            }}
        />
        {/* Bottom left dots grid */}
        <Box
            sx={{
                position: "fixed",
                left: 0,
                bottom: 0,
                width: 200,
                height: 80,
                zIndex: 0,
                opacity: 0.15,
                display: { xs: "none", sm: "block" },
                pointerEvents: "none",
            }}
        >
            <svg width="200" height="80">
                {Array.from({ length: 5 }).map((_, row) =>
                    Array.from({ length: 10 }).map((_, col) => (
                        <circle
                            key={`${row}-${col}`}
                            cx={col * 20 + 8}
                            cy={row * 20 + 8}
                            r="3"
                            fill="#1976d2"
                        />
                    ))
                )}
            </svg>
        </Box>
        {/* Bottom right green circle */}
        <Box
            sx={{
                position: "fixed",
                bottom: 60,
                right: 60,
                width: 80,
                height: 80,
                bgcolor: "rgba(76, 175, 80, 0.10)",
                borderRadius: "50%",
                zIndex: 0,
                pointerEvents: "none",
            }}
        />
        {/* Top center blue box */}
        <Box
            sx={{
                position: "fixed",
                top: 0,
                left: "50%",
                transform: "translateX(-50%)",
                width: 100,
                height: 40,
                bgcolor: "rgba(33, 150, 243, 0.08)",
                borderRadius: 2,
                zIndex: 0,
                pointerEvents: "none",
            }}
        />
    </>
);

export default BackgroundDesignElements;