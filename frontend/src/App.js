// frontend/src/App.js
import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { v4 as uuidv4 } from 'uuid';

// --- MUI Imports ---
import Box from '@mui/material/Box';
import Container from '@mui/material/Container';
import Paper from '@mui/material/Paper';
import CircularProgress from '@mui/material/CircularProgress';
import Alert from '@mui/material/Alert';
// --- End MUI Imports ---

import ChatWindow from './components/ChatWindow';
import MessageInput from './components/MessageInput';
import FileUpload from './components/FileUpload';
import FillFormControls from './components/FillFormControls';

const BACKEND_URL = 'http://localhost:5001';

function App() {
  const [messages, setMessages] = useState([]);
  const [sessionId, setSessionId] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isFillingForm, setIsFillingForm] = useState(false);
  const [error, setError] = useState(null);
  const [availableForms, setAvailableForms] = useState([]);
  const [selectedFormType, setSelectedFormType] = useState('');

  // --- Fetch available forms from the backend ---
  useEffect(() => {
    // Using BACKEND_URL for consistency
    fetch(`${BACKEND_URL}/api/list-forms`)
      .then(response => {
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
      })
      .then(data => {
        setAvailableForms(data);
        if (data && data.length > 0) {
          setSelectedFormType(data[0].id); // Select the first form by default
        }
      })
      .catch(error => {
        console.error("Error fetching available forms:", error);
        setError("Failed to load available forms. Please try refreshing."); // User-friendly error
      });
  }, []);

  // --- Handler function to update the selected form type ---
  const handleFormTypeChange = (event) => {
    setSelectedFormType(event.target.value);
  };
  
  useEffect(() => {
    const newSessionId = uuidv4();
    setSessionId(newSessionId);
    // Updated initial message to be more generic
    setMessages([{ sender: 'bot', type:'text', content: 'Hello! Ask about USCIS info or upload documents to fill a form.' }]);
    console.log("Session Started:", newSessionId);
  }, []);

  const addMessage = useCallback((sender, content, type = 'text') => {
    setMessages(prevMessages => [...prevMessages, { sender, content, type, timestamp: new Date() }]);
    setError(null); 
  }, []);

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
      setError(`Chat Error: ${errorMsg}`);
    } finally {
      setIsLoading(false);
    }
  }, [sessionId, isLoading, addMessage]);

  const handleFileUpload = useCallback(async (file) => {
     if (!sessionId) throw new Error("Session ID not available for upload.");
     const formData = new FormData();
     formData.append('file', file);
     formData.append('session_id', sessionId);

     try {
         const response = await axios.post(`${BACKEND_URL}/api/upload`, formData, {
             headers: { 'Content-Type': 'multipart/form-data' },
         });
         console.log('Upload successful:', response.data);
         addMessage('system', `File uploaded: ${response.data.filename}`, 'info');
         return response.data;
     } catch (err) {
         console.error('Error uploading file:', err);
         const errorMsg = err.response?.data?.error || 'Failed to upload file.';
          addMessage('bot', `Upload Error: ${errorMsg}`, 'error');
         setError(`Upload Error: ${errorMsg}`);
         throw new Error(errorMsg);
     }
  }, [sessionId, addMessage]);

  // --- MODIFIED: Handler for triggering form fill ---
  const handleFillForm = useCallback(async () => {
      // Ensure a form type is selected
      if (!selectedFormType) {
          addMessage('system', 'Please select a form type first.', 'error');
          setError('Please select a form type before filling.');
          return;
      }
      if (!sessionId || isFillingForm) return;

      // Get the name of the selected form for user messages
      const currentForm = availableForms.find(form => form.id === selectedFormType);
      const formDisplayName = currentForm ? currentForm.name : selectedFormType; // Fallback to ID if name not found

      addMessage('system', `Attempting to fill Form ${formDisplayName}...`, 'info');
      setIsFillingForm(true);
      setError(null);

      try {
          const response = await axios.post(`${BACKEND_URL}/api/fill-form`, {
              form_type: selectedFormType, // Use selectedFormType from state
              session_id: sessionId,
          }, { responseType: 'blob' });

          const file = new Blob([response.data], { type: 'application/pdf' });
          const fileURL = URL.createObjectURL(file);
          const link = document.createElement('a');
          link.href = fileURL;
          
          // Use download_filename from backend if available, otherwise create a default
          const contentDisposition = response.headers['content-disposition'];
          let filename = `filled-${selectedFormType.replace(/[^a-zA-Z0-9]/g, '_')}.pdf`; // Default dynamic filename
           if (contentDisposition) {
                const filenameMatch = contentDisposition.match(/filename="?(.+)"?/i);
                if (filenameMatch?.[1]) filename = filenameMatch[1];
            }
          link.setAttribute('download', filename);
          document.body.appendChild(link);
          link.click();
          link.parentNode.removeChild(link);
          URL.revokeObjectURL(fileURL);
          addMessage('system', `Form ${formDisplayName} generated. Download started as ${filename}.`, 'info');

      } catch (err) {
          console.error('Error filling form:', err);
          let errorMsg = `Failed to fill form ${formDisplayName}. Check backend logs.`;
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
  }, [sessionId, isFillingForm, addMessage, selectedFormType, availableForms]); // Added selectedFormType and availableForms to dependencies

  return (
    <Container maxWidth="md" sx={{ height: '100vh', display: 'flex', p: { xs: 0, sm: 2 } }} aria-busy={isLoading || isFillingForm}>
      <Paper
        elevation={4}
        sx={{
          width: '100%', 
          height: { xs: '100%', sm: 'calc(100vh - 32px)' }, 
          maxHeight: '100vh', 
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden', 
          borderRadius: { xs: 0, sm: 2 } 
        }}
      >
        <Box component="main" sx={{ display: 'flex', flexDirection: 'column', flexGrow: 1, overflow: 'hidden' }}>        
          {error && (
            <Alert severity="error" onClose={() => setError(null)} sx={{ borderRadius: 0 }}>
                {error}
            </Alert>
          )}

          <ChatWindow messages={messages} />
          <FileUpload onFileUpload={handleFileUpload} disabled={isLoading || isFillingForm} />

          {/* --- MODIFIED: Pass new props to FillFormControls --- */}
          <FillFormControls
            onFillForm={handleFillForm}
            isLoading={isFillingForm}
            // New props for form selection:
            availableForms={availableForms}
            selectedFormType={selectedFormType}
            onFormTypeChange={handleFormTypeChange}
            // Disable fill button if no form is selected or no forms are available
            disabled={isFillingForm || !selectedFormType || availableForms.length === 0}
          />

          {isLoading && <Box sx={{ display: 'flex', justifyContent: 'center', p: 1 }}><CircularProgress size={24} /></Box> }
          <MessageInput onSendMessage={handleSendMessage} disabled={isLoading || isFillingForm} />
        </Box>
      </Paper>
    </Container>
  );
}

export default App;