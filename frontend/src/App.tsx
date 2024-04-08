import VectorAnalogySolver from "./components/VectorAnalogySolver";
import Footer from "./components/Footer";
import "./App.css";

import { createTheme, ThemeProvider } from "@mui/material/styles";
import { Box, CssBaseline } from "@mui/material";

const theme = createTheme({
  palette: {
    primary: {
      main: "#7FEE64",
      contrastText: "#FF0ECA",
    },
    secondary: {
      main: "#FF0ECA",
      contrastText: "#7FEE64",
    },
    text: {
      primary: "#cccccc",
      secondary: "#FF0ECA",
    },
    background: {
      default: "#000000",
      paper: "#333733",
    },
    divider: "#FF0ECA",
  },
  typography: {
    allVariants: {
      color: "#cccccc",
    },
  },
  components: {
    MuiOutlinedInput: {
      styleOverrides: {
        root: {
          "& .MuiOutlinedInput-notchedOutline": {
            borderColor: "#cccccc",
          },
        },
      },
    },
  },
});

function App() {
  return (
    <ThemeProvider theme={theme}>
      <Box display="flex" flexDirection="column" minHeight="100vh">
        <Box component="main" flexGrow={1}>
          <CssBaseline />
          <VectorAnalogySolver />
        </Box>
        <Footer />
      </Box>
    </ThemeProvider>
  );
}

export default App;
