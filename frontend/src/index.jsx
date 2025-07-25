import React from "react";
import ReactDOM from "react-dom";
import { createRoot } from "react-dom/client";
import App from "./App";
import { Provider } from "react-redux";
import { store } from "./redux/store";
import { ThemeProvider, CssBaseline } from "@mui/material";
import MUITheme from "./themes/MUITheme";
import "./styles.css";

const root = createRoot(document.getElementById("root"));
root.render(
  <React.StrictMode>
    <ThemeProvider theme={MUITheme}>
    <Provider store={store}>
      <CssBaseline />
      <App />
    </Provider>
    </ThemeProvider>
  </React.StrictMode>
);



