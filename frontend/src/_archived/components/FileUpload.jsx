import React, { useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import { Box, Button, Typography, Input } from "@mui/material";
import { uploadFileAndParseText } from "../redux/dataSlice"; // Import the thunk action

const FileUpload = () => {
    const [selectedFile, setSelectedFile] = useState(null);
    const [errorMessage, setErrorMessage] = useState("");
    const dispatch = useDispatch(); // Initialize the dispatch hook
    const { status, error, parsedText } = useSelector((state) => state.data); // Access Redux state

    const handleFileChange = (event) => {
        const file = event.target.files[0];
        if (file && file.type === "application/pdf") {
            setSelectedFile(file);
            setErrorMessage(""); // Clear any previous error message
        } else {
            setSelectedFile(null);
            setErrorMessage("Please upload a valid PDF file.");
        }
    };

    const handleUploadClick = async () => {
        if (selectedFile) {
            const formData = new FormData();
            formData.append("files", selectedFile); // Add the file to FormData

            try {
                const result = await dispatch(uploadFileAndParseText(formData)); // Dispatch the thunk action and await the result

                if (uploadFileAndParseText.fulfilled.match(result)) {
                    console.log("File uploaded successfully:", result.payload);
                } else if (uploadFileAndParseText.rejected.match(result)) {
                    console.error("File upload failed:", result.error.message || "Unknown error");
                }
            } catch (error) {
                console.error("Unexpected error during file upload:", error);
            }
        } else {
            console.log("No file selected");
        }
    };

    return (
        <Box sx={{ display: "flex", flexDirection: "column", alignItems: "center", p: 2, border: "1px solid #ccc", borderRadius: 2 }}>
            <Typography variant="body1" gutterBottom>
                Upload a PDF File
            </Typography>
            <Input
                type="file"
                accept="application/pdf" // Restrict file type to PDF
                onChange={handleFileChange}
                sx={{ mb: 2 }}
            />
            {errorMessage && (
                <Typography variant="body2" color="error" sx={{ mb: 2 }}>
                    {errorMessage}
                </Typography>
            )}
            {selectedFile && (
                <Typography variant="body2" sx={{ mb: 2 }}>
                    Selected File: {selectedFile.name}
                </Typography>
            )}
            <Button
                variant="contained"
                color="secondary"
                onClick={handleUploadClick}
                disabled={!selectedFile || status === "loading"}
                sx={{ fontSize: "0.75rem" }}
                size="small"
            >
                Upload
            </Button>
            {status === "loading" && <Typography variant="body2">Uploading...</Typography>}
            {/* {status === "succeeded" && (
                <Typography variant="body2" sx={{ mt: 2 }}>
                    Parsed Text: {parsedText.extracted_text.substring(0, 100) || "No text extracted"}
                </Typography>
            )} */}
            {status === "failed" && (
                <Typography variant="body2" color="error" sx={{ mt: 2 }}>
                    Error: {error?.message || "An error occurred"}
                </Typography>
            )}
        </Box>
    );
};

export default FileUpload;