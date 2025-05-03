import React, { useEffect, useRef } from 'react';
import Box from '@mui/material/Box';
import Stack from '@mui/material/Stack';
import Paper from '@mui/material/Paper';
import Typography from '@mui/material/Typography';
import { useTheme } from '@mui/material/styles';
// Optional: Import specific contrast checking functions if needed, or rely on manual check
// import { getContrastRatio } from '@mui/material/styles';

function ChatWindow({ messages }) {
  const theme = useTheme();
  const messagesEndRef = useRef(null);

  // --- UPDATED COLOR LOGIC FOR ACCESSIBILITY ---
  const getMessageStyles = (sender, type) => {
    let bgColor = theme.palette.background.paper; // Default: Bot messages on paper
    let textColor = theme.palette.text.primary;

    if (type === 'error') {
      // Ensure high contrast for errors
      bgColor = theme.palette.error.light; // Often pinkish
      textColor = theme.palette.error.dark; // Dark red text usually contrasts well
      // Verify contrast: console.log('Error Contrast:', getContrastRatio(bgColor, textColor));
    } else if (type === 'info' || sender === 'system') {
       // Use a subtle background for info, ensure text contrasts
      bgColor = theme.palette.grey[100]; // Very light grey
      textColor = theme.palette.info.dark; // Use darker info text color
      // Verify contrast: console.log('Info Contrast:', getContrastRatio(bgColor, textColor));
    } else if (sender === 'user') {
       // Use a different light grey for user, ensure text contrasts
      bgColor = theme.palette.grey[200]; // Slightly darker grey than bot/info
      textColor = theme.palette.text.primary; // Standard dark text
      // Verify contrast: console.log('User Contrast:', getContrastRatio(bgColor, textColor));
    }
    // Bot messages use the default bgColor/textColor defined above

    return { bgColor, textColor };
  };
  // --- END UPDATED COLOR LOGIC ---


  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <Box
      sx={{
        flexGrow: 1,
        overflowY: 'auto',
        p: { xs: 1, sm: 2 },
      }}
    >
      <Stack spacing={1.5}>
        {messages.map((msg, index) => {
          // Get the calculated styles
          const { bgColor, textColor } = getMessageStyles(msg.sender, msg.type);

          return (
            <Box
              key={msg.timestamp?.toISOString() + index || index}
              sx={{
                display: 'flex',
                justifyContent: msg.sender === 'user' ? 'flex-end' : 'flex-start',
              }}
            >
              <Paper
                elevation={1}
                sx={{
                  p: { xs: 1, sm: 1.5 },
                  maxWidth: '80%',
                  bgcolor: bgColor, // Apply calculated background
                  color: textColor, // Apply calculated text color
                  wordBreak: 'break-word',
                  // borderRadius is handled by theme override or MUI default
                }}
              >
                <Typography variant="body1">
                  {typeof msg.content === 'string' && msg.content.startsWith('http') ? (
                     <a href={msg.content} target="_blank" rel="noopener noreferrer" style={{ color: 'inherit', textDecoration: 'underline' }}>{msg.content}</a>
                  ) : (
                    msg.content
                  )}
                </Typography>
              </Paper>
            </Box>
          );
        })}
        <div ref={messagesEndRef} />
      </Stack>
    </Box>
  );
}

export default ChatWindow;