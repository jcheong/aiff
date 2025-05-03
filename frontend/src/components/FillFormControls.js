import React from 'react';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import CircularProgress from '@mui/material/CircularProgress';
import DescriptionIcon from '@mui/icons-material/Description'; // Icon for PDF/Form

function FillFormControls({ onFillForm, isLoading }) {
  return (
    <Box
      sx={{
        display: 'flex',
        justifyContent: 'flex-end', // Align button to the right
        p: 1.5,
        borderTop: 1,
        borderColor: 'divider',
        bgcolor: 'grey.50', // Match upload area background
      }}
    >
      <Button
        variant="contained"
        color="secondary" // Use secondary color for distinction
        onClick={onFillForm}
        disabled={isLoading}
        startIcon={isLoading ? <CircularProgress size={20} color="inherit" /> : <DescriptionIcon />}
        title="Fill I-765 based on uploaded documents for this session"
      >
        Fill Form I-765
      </Button>
    </Box>
  );
}

export default FillFormControls;