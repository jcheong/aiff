import React, { useState, useRef, useCallback } from 'react';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Typography from '@mui/material/Typography';
import Chip from '@mui/material/Chip';
import CircularProgress from '@mui/material/CircularProgress';
import CloudUploadIcon from '@mui/icons-material/CloudUpload'; // Import icon
import Stack from '@mui/material/Stack';

function FileUpload({ onFileUpload, disabled }) {
  const [uploadStatus, setUploadStatus] = useState('');
  const [isUploading, setIsUploading] = useState(false);
  const [isError, setIsError] = useState(false);
  const fileInputRef = useRef(null);

  const handleFileChange = useCallback(async (event) => {
    const file = event.target.files?.[0];
    if (file && !disabled) {
      setIsUploading(true);
      setIsError(false);
      setUploadStatus(`Uploading ${file.name}...`);
      try {
        const result = await onFileUpload(file); // Call the actual upload logic from App.js
        setUploadStatus(`Uploaded: ${result.filename}`);
        setIsError(false);
        if (fileInputRef.current) {
            fileInputRef.current.value = ""; // Clear input
        }
      } catch (error) {
        console.error("Upload failed:", error);
        setUploadStatus(`Upload failed: ${error.message || 'Unknown error'}`);
        setIsError(true);
      } finally {
        setIsUploading(false);
      }
    }
  }, [onFileUpload, disabled]); // Include dependencies

  const getChipColor = () => {
    if (isError) return "error";
    if (isUploading) return "info";
    if (uploadStatus.startsWith("Uploaded")) return "success";
    return "default";
  };

  return (
    <Box
      sx={{
        display: 'flex',
        alignItems: 'center',
        gap: 2, // Spacing between elements
        p: 1.5, // Padding
        borderTop: 1,
        borderColor: 'divider',
        bgcolor: 'grey.50', // Slightly different background
      }}
    >
      <Stack
        direction={{ xs: 'column', sm: 'row' }} // Stack vertically on xs, row on sm+
        spacing={1} // Consistent spacing
        alignItems={{ xs: 'stretch', sm: 'center' }} // Stretch items on xs, center on sm+
      >
        <Button
          variant="outlined" // Or contained
          component="label" // Makes the button act as a label for the hidden input
          disabled={disabled || isUploading}
          startIcon={isUploading ? <CircularProgress size={20} /> : <CloudUploadIcon />}
        >
          Choose File
          <input
            type="file"
            hidden // Hide the default browser input
            ref={fileInputRef}
            onChange={handleFileChange}
            // Consider adding 'accept' attribute
            accept=".pdf,.txt,.jpg,.jpeg,.png,.tiff,.bmp,.gif,.webp"
          />
        </Button>

        {/* Display status using Chip or Typography */}
        {uploadStatus && (
          <Box component="span" aria-live="polite">
            <Chip
                label={uploadStatus}
                color={getChipColor()}
                size="small"
                // Optionally add onDelete if you want a clear status button
            />
          </Box>
          // Or:
          // <Typography variant="caption" color={isError ? 'error' : 'text.secondary'}>
          //     {uploadStatus}
          // </Typography>
        )}
      </Stack>
    </Box>
  );
}

export default FileUpload;