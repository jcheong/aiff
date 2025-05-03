import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { v4 as uuidv4 } from 'uuid';

// --- MUI Imports ---
import Box from '@mui/material/Box';
import Container from '@mui/material/Container';
import Paper from '@mui/material/Paper'; // For overall app structure elevation
import CircularProgress from '@mui/material/CircularProgress'; // For loading state
import Alert from '@mui/material/Alert'; // Optional: For global errors
// --- End MUI Imports ---

import ChatWindow from './components/ChatWindow';
import MessageInput from './components/MessageInput';
import FileUpload from './components/FileUpload';
import FillFormControls from './components/FillFormControls'; // Extract button logic
// Removed: import './App.css'; // We aim to remove reliance on this

const BACKEND_URL = 'http://localhost:5001';

function App() {
  const [messages, setMessages] = useState([]);
  const [sessionId, setSessionId] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isFillingForm, setIsFillingForm] = useState(false); // Separate loading state for form filling
  const [error, setError] = useState(null); // For displaying persistent errors

  // Generate session ID on component mount
  useEffect(() => {
    const newSessionId = uuidv4();
    setSessionId(newSessionId);
    setMessages([{ sender: 'bot', type:'text', content: 'Hello! Ask about USCIS info (I-765) or upload documents to fill Form I-765.' }]);
    console.log("Session Started:", newSessionId);
  }, []);

  // Function to add a new message to the chat
  // Type can be 'text', 'error', 'info'
  const addMessage = useCallback((sender, content, type = 'text') => {
    setMessages(prevMessages => [...prevMessages, { sender, content, type, timestamp: new Date() }]);
    setError(null); // Clear global error when a new message is added/sent
  }, []);

  // Handler for sending chat messages
  const handleSendMessage = useCallback(async (messageText) => {
    if (!sessionId || isLoading) return;
    addMessage('user', messageText);
    setIsLoading(true);
    setError(null);

    try {
      const response = await axios.post(`${BACKEND_URL}/api/chat`, {
        message: messageText,
        session_id: sessionId,
      });
      addMessage('bot', response.data.reply);
    } catch (err) {
      console.error('Error sending message:', err);
      const errorMsg = err.response?.data?.error || 'Failed to get response from server.';
      addMessage('bot', `Chat Error: ${errorMsg}`, 'error');
      setError(`Chat Error: ${errorMsg}`); // Show persistent error if needed
    } finally {
      setIsLoading(false);
    }
  }, [sessionId, isLoading, addMessage]);

  // Handler for file uploads
  const handleFileUpload = useCallback(async (file) => {
     if (!sessionId) throw new Error("Session ID not available for upload.");
     // We don't set global isLoading here, FileUpload component can show its own status
     const formData = new FormData();
     formData.append('file', file);
     formData.append('session_id', sessionId);

     try {
         const response = await axios.post(`${BACKEND_URL}/api/upload`, formData, {
             headers: { 'Content-Type': 'multipart/form-data' },
         });
         console.log('Upload successful:', response.data);
         addMessage('system', `File uploaded: ${response.data.filename}`, 'info'); // Add system message
         return response.data; // Return data for FileUpload component status
     } catch (err) {
         console.error('Error uploading file:', err);
         const errorMsg = err.response?.data?.error || 'Failed to upload file.';
          addMessage('bot', `Upload Error: ${errorMsg}`, 'error');
         setError(`Upload Error: ${errorMsg}`);
         throw new Error(errorMsg); // Re-throw for FileUpload component
     }
  }, [sessionId, addMessage]);

  // Handler for triggering form fill
  const handleFillForm = useCallback(async () => {
      if (!sessionId || isFillingForm) return;
      addMessage('system', 'Attempting to fill Form I-765...', 'info');
      setIsFillingForm(true); // Use specific loading state
      setError(null);

      try {
          const response = await axios.post(`${BACKEND_URL}/api/fill-form`, {
              form_type: 'I-765',
              session_id: sessionId,
          }, { responseType: 'blob' });

          const file = new Blob([response.data], { type: 'application/pdf' });
          const fileURL = URL.createObjectURL(file);
          const link = document.createElement('a');
          link.href = fileURL;
          const contentDisposition = response.headers['content-disposition'];
          let filename = 'filled-i-765.pdf';
           if (contentDisposition) {
                const filenameMatch = contentDisposition.match(/filename="?(.+)"?/i);
                if (filenameMatch?.[1]) filename = filenameMatch[1];
            }
          link.setAttribute('download', filename);
          document.body.appendChild(link);
          link.click();
          link.parentNode.removeChild(link);
          URL.revokeObjectURL(fileURL);
          addMessage('system', `Form I-765 generated. Download started as ${filename}.`, 'info');

      } catch (err) {
          console.error('Error filling form:', err);
          // Attempt to read error from blob
          let errorMsg = 'Failed to fill form. Check backend logs.';
          if (err.response?.data && err.response.data instanceof Blob) {
              try {
                   const errorJson = JSON.parse(await err.response.data.text());
                   errorMsg = errorJson.error || errorMsg;
              } catch (parseError) {
                   console.error("Could not parse error blob:", parseError);
              }
          } else if (err.response?.data?.error) {
               errorMsg = err.response.data.error;
          }
          addMessage('bot', `Form Fill Error: ${errorMsg}`, 'error');
          setError(`Form Fill Error: ${errorMsg}`);
      } finally {
          setIsFillingForm(false);
      }
  }, [sessionId, isFillingForm, addMessage]);

 // Helper removed as logic is inline now

  return (
    // Container centers content and sets max width
    <Container maxWidth="md" sx={{ height: '100vh', display: 'flex', p: { xs: 0, sm: 2 } /* No padding on xs */ }} aria-busy={isLoading || isFillingForm}>
      {/* Paper provides background and elevation for the main app structure */}
      <Paper
        elevation={4}
        sx={{
          width: '100%', // Take full width of Container
          height: { xs: '100%', sm: 'calc(100vh - 32px)' }, // Full height on mobile, slightly less on larger screens
          maxHeight: '100vh', // Ensure it doesn't exceed viewport height
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden', // Prevent content spillover
          borderRadius: { xs: 0, sm: 2 } // No border radius on mobile
        }}
      >
        <Box component="main" sx={{ display: 'flex', flexDirection: 'column', flexGrow: 1, overflow: 'hidden' }}>        
          {/* Global Error Display Area */}
          {error && (
            <Alert severity="error" onClose={() => setError(null)} sx={{ borderRadius: 0 }}>
                {error}
            </Alert>
          )}

          {/* Chat Window takes up available space */}
          <ChatWindow messages={messages} />

          {/* Upload Area */}
          <FileUpload onFileUpload={handleFileUpload} disabled={isLoading || isFillingForm} />

          {/* Fill Form Controls Area */}
          <FillFormControls onFillForm={handleFillForm} isLoading={isFillingForm} />

          {/* Loading indicator for chat */}
          {isLoading && <Box sx={{ display: 'flex', justifyContent: 'center', p: 1 }}><CircularProgress size={24} /></Box> }

          {/* Message Input Area */}
          <MessageInput onSendMessage={handleSendMessage} disabled={isLoading || isFillingForm} />
        </Box>
      </Paper>
    </Container>
  );
}

export default App;