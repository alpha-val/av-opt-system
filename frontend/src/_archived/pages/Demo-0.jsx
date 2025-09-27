import React, { useEffect, useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import { Box, Typography, TextField, Checkbox, FormGroup, FormControlLabel, Button, Paper, Radio, Select, MenuItem, InputLabel, FormControl } from "@mui/material";
import EntityCard from "../components/EntityCard";
import FileUpload from "../components/FileUpload";
import { fetchNodes } from "../redux/nodeSlice";
import { memoizedNodesSelector } from "../redux/nodeSlice";
import D3ForceSpringGraph from "../components/vis/D3ForceSpringGraph";
import { fetchFullGraph, userQuery } from "../redux/dataSlice";

const Demo_v0 = () => {
    const [selectedNodeTypes, setSelectedNodeTypes] = React.useState([]);
    const [question, setQuestion] = React.useState("");
    // const nodes = useSelector(memoizedNodesSelector);
    const [nodes, setNodes] = useState([]);
    const dispatch = useDispatch();
    const graph = useSelector((state) => state.data.graph); // Always use Redux state for graph
    const graphStatus = useSelector((state) => state.data.graphStatus);

    useEffect(() => {
        dispatch(fetchFullGraph());
    }, [dispatch]);

    const entityLabels = React.useMemo(() => {
        // if (graphStatus !== "succeeded" || !graph?.graph?.nodes) return [];
        const labelsSet = new Set();
        if (graph.graph) {
            if (graph.graph.nodes) {
                graph.graph.nodes.forEach((node) => {
                    if (node.labels && Array.isArray(node.labels) && node.labels.length === 1) {
                        var label = node.labels[0];
                        labelsSet.add(label);
                    }
                });
            }
        }
        return Array.from(labelsSet);
    }, [graph]);


    const handleNodeTypeChange = (event) => {
        const { checked, value } = event.target;
        setSelectedNodeTypes((prev) =>
            checked ? [...prev, value] : prev.filter((item) => item !== value)
        );
    };

    const [file, setFile] = React.useState(null);
    const [uploadKey, setUploadKey] = React.useState(Date.now()); // Unique key for FileUpload

    const handleFileUpload = (uploadedFile) => {
        setFile(uploadedFile);
        console.log("File uploaded:", uploadedFile, " type of: ,", typeof uploadedFile);

        // Reset file input and button state after upload
        setFile(null);
        setUploadKey(Date.now()); // Change key to force FileUpload re-mount and clear field
    };

    const [selectedParameters, setSelectedParameters] = React.useState([]);
    const handleParameterChange = (event) => {
        const { checked, value } = event.target;
        setSelectedParameters((prev) =>
            checked ? [...prev, value] : prev.filter((item) => item !== value)
        );
    };

    const handleSubmit = () => {
        // Dispatch the fetchNodes thunk with the selected parameters
        if (question?.trim()) {
            dispatch(userQuery(question.trim()));
        }
    };

    return (
        <Box
            sx={{
                bgcolor: "background.default",
                height: "100%",
                display: "flex",
                flexDirection: "column",
                overflow: "hidden",
            }}
        >
            <Box
                sx={{
                    display: "flex",
                    flex: 1,
                    minHeight: 0,
                    bgcolor: "background.default",
                    p: 2,
                    overflow: "hidden",
                }}
            >                {/* Left Panel: Form */}
                <Box
                    sx={{
                        width: "18%",
                        bgcolor: "#fff",
                        borderRadius: 2,
                        p: 2,
                        boxShadow: 1,
                        overflowY: "auto", // Enable scrolling for the form if content exceeds height
                    }}
                >
                    <FileUpload key={uploadKey} onFileUpload={handleFileUpload} />

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

                    <Button
                        variant="contained"
                        color="primary"
                        fullWidth
                        sx={{ mt: 2, fontSize: "0.75rem" }}
                        size="small"
                        onClick={handleSubmit} // Call handleSubmit on click
                    >
                        Submit
                    </Button>
                </Box>

                {/* Right Panel: Results */}
                <Box
                    sx={{
                        display: "flex",
                        flexDirection: "row",
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
                            Knowledge Graph {graphStatus === "loading" ? "(Loading...)" : graphStatus === "succeeded" ? "" : graphStatus === "failed" ? "(Failed to load)" : ""}
                            {graphStatus === "succeeded" && graph ? ` (${graph.graph?.nodes?.length} nodes, ${graph.graph?.links?.length} links)` : ""}
                        </Typography>

                        <Box sx={{ display: "flex", flexWrap: "wrap", gap: 2, width: "100%" }}>
                            <D3ForceSpringGraph
                                data={graph}
                                height={900}
                                width={950}
                            />
                        </Box>
                    </Paper>
                    <Paper elevation={0} sx={{ p: 1 }}>
                        <Typography variant="subtitle1" gutterBottom>
                            View Entities ({Array.isArray(nodes) ? nodes.length : 0} found)
                        </Typography>
                        <FormControl fullWidth sx={{ mb: 2 }}>
                            <InputLabel id="entity-select-label">Select Entity Type</InputLabel>
                            <Select
                                labelId="entity-select-label"
                                value={selectedNodeTypes.length > 0 ? selectedNodeTypes[0] : ""}
                                onChange={(event) => {
                                    const selectedType = event.target.value;
                                    setSelectedNodeTypes([selectedType]);
                                    dispatch(fetchNodes(selectedType))
                                        .then((data) => {
                                            setNodes(data.payload);
                                        })
                                        .catch((error) => {
                                            console.error(error);
                                            setNodes([]);
                                        });
                                }}
                                label="Select Entity Type"
                            >
                                {entityLabels.map((label) => (
                                    <MenuItem key={label} value={label}>
                                        {label}
                                    </MenuItem>
                                ))}
                            </Select>
                        </FormControl>
                        <Box sx={{ bgcolor: "#f5f5f5", borderRadius: 1, overflow: "wrap", p: 1 }}>
                            {Array.isArray(nodes) && nodes.length > 0 ? (
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
        </Box>
    );
};

export default Demo_v0;