import React from "react";
import ReactDOM from "react-dom/client";
import { Provider } from "react-redux";
import { BrowserRouter as Router } from "react-router-dom";
import { CssBaseline } from "@mui/material";
import App from "./App";
import { store } from "./redux/store";
import { ThemeContextProvider } from "./themes/ThemeContext";

const root = ReactDOM.createRoot(document.getElementById("root"));

root.render(
  <React.StrictMode>
    <Provider store={store}>
      <ThemeContextProvider>
        <Router>
          <CssBaseline />
          <App />
        </Router>
      </ThemeContextProvider>
    </Provider>
  </React.StrictMode>
);



