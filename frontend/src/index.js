import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css'; // Can contain minimal global styles or be removed
import App from './App';
import theme from './theme'; // Import your custom theme
import { ThemeProvider } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <ThemeProvider theme={theme}>
      <CssBaseline /> {/* Normalizes styles & helps with Roboto loading */}
      <App />
    </ThemeProvider>
  </React.StrictMode>
);