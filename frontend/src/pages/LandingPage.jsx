import React from "react";
import { Box, Button, Typography, Grid, Card, CardContent, Container, Stack } from "@mui/material";
import { PrecisionManufacturing, Timeline, Security, Engineering, TrendingUp, People } from "@mui/icons-material";
import CustomAppBar from "../widgets/Nav";
import Footer from "../widgets/Footer";
const features = [
    {
        icon: <Timeline color="primary" sx={{ fontSize: 40 }} />,
        title: "AI-Driven Scenario Analysis",
        desc: "Rapidly simulate and compare mining strategies using advanced AI models for robust, data-driven decisions.",
    },
    {
        icon: <PrecisionManufacturing color="primary" sx={{ fontSize: 40 }} />,
        title: "Optimized Mine Planning",
        desc: "Automate complex mine design, scheduling, and resource modeling to maximize efficiency and profitability.",
    },
    {
        icon: <Security color="primary" sx={{ fontSize: 40 }} />,
        title: "Sustainability & Compliance",
        desc: "Continuously monitor environmental impact and ensure regulatory compliance with predictive analytics.",
    },
];

const personas = [
    {
        icon: <Engineering color="secondary" sx={{ fontSize: 36 }} />,
        title: "Mine Planners & Engineers",
        benefits: [
            "Accelerate design iterations",
            "Uncover optimal extraction strategies",
            "Enhance safety and reduce manual workload",
        ],
    },
    {
        icon: <TrendingUp color="secondary" sx={{ fontSize: 36 }} />,
        title: "Executives & Decision-Makers",
        benefits: [
            "Gain strategic flexibility",
            "Make confident, data-backed investments",
            "Mitigate operational and market risks",
        ],
    },
    {
        icon: <People color="secondary" sx={{ fontSize: 36 }} />,
        title: "ESG & Sustainability Teams",
        benefits: [
            "Monitor compliance in real time",
            "Proactively manage environmental risks",
            "Support transparent reporting",
        ],
    },
];

const LandingPage = () => {
    return (
        <>
            <CustomAppBar position="static" />
            {/* Hero Section */}
            <Box
                sx={{
                    bgcolor: "#e3f2fd",
                    py: 8,
                    textAlign: "center",
                    background: "linear-gradient(90deg, #e3f2fd 60%, #f5f5f5 100%)",
                }}
            >
                <Container maxWidth="md">
                    <Typography variant="h3" fontWeight={700} color="primary.main" gutterBottom>
                        Unlock Mining’s Future with AI-Driven Optionality
                    </Typography>
                    <Typography variant="h6" color="text.secondary" mb={4}>
                        Smarter scenario analysis and mine planning for resilient, sustainable, and profitable operations.
                    </Typography>
                    <Button
                        variant="contained"
                        color="primary"
                        size="large"
                        href="/demo"
                        sx={{ px: 5, py: 1.5, fontWeight: 600, borderRadius: 3 }}
                    >
                        Try Our Demo
                    </Button>
                </Container>
            </Box>

            {/* Features Section */}
            <Container maxWidth="lg" sx={{ py: 8 }}>
                <Typography variant="h4" align="center" fontWeight={600} color="primary.main" gutterBottom>
                    Key Features
                </Typography>
                <Grid
                    container
                    spacing={4}
                    justifyContent="center"
                    alignItems="stretch"
                    sx={{
                        flexWrap: { xs: "wrap", md: "nowrap" }, // Prevent wrapping on md+ screens
                    }}
                >
                    {features.map((f, i) => (
                        <Grid
                            item
                            xs={12}
                            sm={6}
                            md={4}
                            key={i}
                            sx={{
                                display: "flex",
                                flexDirection: "column",
                            }}
                        >
                            <Card elevation={4} sx={{ borderRadius: 3, height: "100%", display: "flex", flexDirection: "column", justifyContent: "center" }}>
                                <CardContent sx={{ textAlign: "center", p: 4 }}>
                                    {f.icon}
                                    <Typography variant="h6" fontWeight={600} mt={2} mb={1}>
                                        {f.title}
                                    </Typography>
                                    <Typography color="text.secondary">{f.desc}</Typography>
                                </CardContent>
                            </Card>
                        </Grid>
                    ))}
                </Grid>
            </Container>            {/* Benefits for Personas Section */}
            <Box sx={{ bgcolor: "#f5f5f5", py: 8 }}>
                <Container maxWidth="lg">
                    <Typography variant="h4" align="center" fontWeight={600} color="primary.main" gutterBottom>
                        Benefits for Every Role
                    </Typography>
                    <Grid container spacing={4} justifyContent="center">
                        {personas.map((persona, i) => (
                            <Grid item xs={12} md={4} key={i}>
                                <Card elevation={0} sx={{ p: 4, textAlign: "center", borderRadius: 3, bgcolor: "#fff" }}>
                                    <CardContent>
                                        {persona.icon}
                                        <Typography variant="h6" fontWeight={600} mt={2} mb={1}>
                                            {persona.title}
                                        </Typography>
                                        <Stack spacing={1} mt={2}>
                                            {persona.benefits.map((b, j) => (
                                                <Typography key={j} color="text.secondary" sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                                                    <Security color="success" sx={{ fontSize: 18 }} /> {b}
                                                </Typography>
                                            ))}
                                        </Stack>
                                    </CardContent>
                                </Card>
                            </Grid>
                        ))}
                    </Grid>
                </Container>
            </Box>
            <Footer />
        </>
    );
};

export default LandingPage;