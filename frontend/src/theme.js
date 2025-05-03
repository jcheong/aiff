import { createTheme } from '@mui/material/styles';
import { blue, grey } from '@mui/material/colors'; // Import colors for easy use

// You can customize the primary color, or use MUI defaults
const PRIMARY_COLOR = blue[700]; // A standard MUI blue
const BACKGROUND_COLOR = grey[50]; // A very light grey background

const theme = createTheme({
  palette: {
    primary: {
      main: PRIMARY_COLOR,
    },
    // secondary: { // Define if needed, e.g., for secondary actions
    //   main: green[500],
    // },
    background: {
      default: BACKGROUND_COLOR, // Light grey background
      paper: '#ffffff', // White background for Cards, Paper, etc.
    },
    text: {
      primary: grey[900], // Dark grey for primary text
      secondary: grey[700], // Lighter grey for secondary text
    },
  },
  typography: {
    // Default font family is Roboto if loaded via link/CssBaseline
    // We generally don't need to specify fontFamily here if using Roboto
    // Optionally adjust default sizes or weights if desired
    // h1: { fontSize: '2.5rem' },
    // button: { textTransform: 'none' } // Common preference
  },
  // Use default spacing (8px)
  // Add subtle component overrides if needed for consistency
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 8, // Slightly rounder buttons
          textTransform: 'none', // No uppercase buttons
        }
      }
    },
    MuiPaper: { // Style Paper components (used for messages)
      styleOverrides: {
         root: {
             borderRadius: 8, // Consistent rounding
         }
      }
    },
    MuiTextField: { // Use outlined variant by default maybe
        defaultProps: {
            variant: 'outlined',
            size: 'small', // Smaller text fields often look cleaner
        }
    }
  }
});

export default theme;