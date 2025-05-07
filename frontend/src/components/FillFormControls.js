import React from 'react';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import CircularProgress from '@mui/material/CircularProgress';
import DescriptionIcon from '@mui/icons-material/Description'; // Icon for PDF/Form
import Select from '@mui/material/Select';
import MenuItem from '@mui/material/MenuItem';
import FormControl from '@mui/material/FormControl';
import InputLabel from '@mui/material/InputLabel';

function FillFormControls({
  onFillForm,
  isLoading,
  availableForms = [], // Default to empty array to prevent errors if undefined
  selectedFormType = '', // Default to empty string
  onFormTypeChange,
  disabled // This prop comes from App.js and considers isLoading, selectedFormType, and availableForms.length
}) {
  const selectedFormName = availableForms.find(f => f.id === selectedFormType)?.name || 'selected form';
  const buttonText = isLoading ? 'Processing...' : `Fill ${selectedFormName}`;
  const buttonTitle = selectedFormType ? `Fill ${selectedFormName}` : "Select a form type first";

  return (
    <Box
      sx={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        p: 1.5,
        borderTop: 1,
        borderColor: 'divider',
        bgcolor: 'grey.50', // Match upload area background
      }}
    >
      <FormControl 
        sx={{ mr: 2, minWidth: 250, flexGrow: 1 }} 
        size="small" 
        disabled={isLoading || availableForms.length === 0}
      >
        <InputLabel id="form-type-select-label">Form Type</InputLabel>
        <Select
          labelId="form-type-select-label"
          value={selectedFormType}
          label="Form Type"
          onChange={onFormTypeChange}
        >
          {availableForms.length === 0 && (
            <MenuItem value="" disabled>
              No forms available
            </MenuItem>
          )}
          {availableForms.map((form) => (
            <MenuItem key={form.id} value={form.id}>
              {form.name} ({form.id})
            </MenuItem>
          ))}
        </Select>
      </FormControl>

      <Button
        variant="contained"
        color="secondary"
        onClick={onFillForm}
        disabled={disabled}
        startIcon={isLoading ? <CircularProgress size={20} color="inherit" /> : <DescriptionIcon />}
        title={buttonTitle}
        sx={{ minWidth: '180px' }} // Ensure button has enough space for dynamic text
      >
        {buttonText}
      </Button>
    </Box>
  );
}

export default FillFormControls;
