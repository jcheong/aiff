import React, { useState } from 'react';
import Box from '@mui/material/Box';
import TextField from '@mui/material/TextField';
import IconButton from '@mui/material/IconButton';
import SendIcon from '@mui/icons-material/Send'; // Import Send icon

function MessageInput({ onSendMessage, disabled }) {
  const [message, setMessage] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (message.trim() && !disabled) {
      onSendMessage(message);
      setMessage('');
    }
  };

  return (
    <Box
      component="form"
      onSubmit={handleSubmit}
      sx={{
        display: 'flex',
        alignItems: 'center',
        p: 1.5, // Padding around input area
        borderTop: 1, // Use theme border size
        borderColor: 'divider', // Use theme divider color
        bgcolor: 'background.default' // Match app background potentially
      }}
    >
      <TextField
        fullWidth
        // variant="outlined" // Set by theme defaultProps
        // size="small" // Set by theme defaultProps
        placeholder="Type your message..."
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        disabled={disabled}
        onKeyPress={(e) => { // Optional: Send on Enter press
          if (e.key === 'Enter' && !e.shiftKey) {
            handleSubmit(e);
          }
        }}
        sx={{ mr: 1 }} // Margin to the right before the button
      />
      <IconButton
        type="submit"
        color="primary" // Use theme primary color
        disabled={disabled || !message.trim()}
        aria-label="send message"
      >
        <SendIcon />
      </IconButton>
    </Box>
  );
}

export default MessageInput;