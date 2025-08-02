import React, { useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import { Box, Typography, TextField, Checkbox, FormGroup, FormControlLabel, Button, Paper, Radio } from "@mui/material";
import Nav from "../widgets/Nav";
import Footer from "../widgets/Footer";
import EntityCard from "../components/EntityCard";
import { fetchNodes } from "../redux/nodeSlice"; // Import the thunk action
import { memoizedNodesSelector } from "../redux/nodeSlice"; // Import the memoized selector

const Demo_v0 = () => {
    const [selectedNodeTypes, setSelectedNodeTypes] = useState([]);
    const [selectedParameters, setSelectedParameters] = useState([]);
    const [question, setQuestion] = useState("");
    const nodes = useSelector(memoizedNodesSelector); // Use the memoized selector to get nodes
    const dispatch = useDispatch(); // Initialize the dispatch hook

    const handleNodeTypeChange = (event) => {
        const { checked, value } = event.target;
        setSelectedNodeTypes((prev) =>
            checked ? [...prev, value] : prev.filter((item) => item !== value)
        );
    };

    const handleParameterChange = (event) => {
        const { checked, value } = event.target;
        setSelectedParameters((prev) =>
            checked ? [...prev, value] : prev.filter((item) => item !== value)
        );
    };

    const handleSubmit = () => {
        // Dispatch the fetchNodes thunk with the selected parameters
        const type = selectedNodeTypes.length > 0 ? selectedNodeTypes[0] : null; // Use the first selected node type
        dispatch(fetchNodes(type)); // Dispatch the action
    };

    return (
        <Box sx={{ height: "100vh", bgcolor: "#f5f5f5", display: "flex", flexDirection: "column", overflow: "hidden" }}>
            <Nav />
            <Box sx={{ display: "flex", flex: 1, bgcolor: "#f5f5f5", p: 2, overflow: "hidden" }}>
                {/* Left Panel: Form */}
                <Box
                    sx={{
                        width: "25%",
                        bgcolor: "#fff",
                        borderRadius: 2,
                        p: 2,
                        boxShadow: 1,
                        overflowY: "auto", // Enable scrolling for the form if content exceeds height
                    }}
                >
                    <Typography gutterBottom>
                        Type your question, followed by optional selections
                    </Typography>
                    <TextField
                        label="Question"
                        multiline
                        rows={4}
                        fullWidth
                        variant="outlined"
                        value={question}
                        onChange={(e) => setQuestion(e.target.value)}
                        sx={{ mb: 2 }}
                    />
                    <Typography variant="subtitle1" gutterBottom>
                        Select NodeTypes (optional)
                    </Typography>
                    <FormGroup>
                        {["Equipment", "Process", "Material", "Document"].map((equipment) => (
                            <FormControlLabel
                                key={equipment}
                                control={
                                    <Radio
                                        value={equipment}
                                        onChange={(event) => setSelectedNodeTypes([event.target.value])} // Update state with the selected equipment
                                        checked={selectedNodeTypes.includes(equipment)}
                                    />
                                }
                                label={equipment}
                            />
                        ))}
                    </FormGroup>
                    {/* <Typography variant="subtitle1" gutterBottom>
                        Parameters (optional)
                    </Typography>
                    <FormGroup>
                        {["Location", "Cost", "Quantity", "Value"].map((parameter) => (
                            <FormControlLabel
                                key={parameter}
                                control={
                                    <Checkbox
                                        value={parameter}
                                        onChange={handleParameterChange}
                                        checked={selectedParameters.includes(parameter)}
                                    />
                                }
                                label={parameter}
                            />
                        ))}
                    </FormGroup> */}
                    <Button
                        variant="contained"
                        color="primary"
                        fullWidth
                        sx={{ mt: 2 }}
                        onClick={handleSubmit} // Call handleSubmit on click
                    >
                        Submit
                    </Button>
                </Box>

                {/* Right Panel: Results */}
                <Box
                    sx={{
                        flex: 1,
                        ml: 2,
                        bgcolor: "#fff",
                        borderRadius: 2,
                        p: 2,
                        boxShadow: 1,
                        height: "100%",
                        overflowY: "auto", // Enable scrolling for the response box
                    }}
                >
                    <Paper elevation={1} sx={{ p: 2, mb: 2 }}>
                        <Typography variant="subtitle1" gutterBottom>
                            Result ({nodes.length > 0 ? `${nodes.length} nodes found` : "No nodes found"})
                        </Typography>
                        <Box sx={{ bgcolor: "#f5f5f5", borderRadius: 1, overflow: "wrap", p: 2 }}>
                            {nodes.length > 0 ? (
                                nodes.map((node, index) => (
                                    <EntityCard key={index} entity={node} />
                                ))
                            ) : (
                                <Typography variant="body2">No nodes found.</Typography>
                            )}
                        </Box>
                    </Paper>
                </Box>
            </Box>
            <Footer />
        </Box>
    );
};

export default Demo_v0;