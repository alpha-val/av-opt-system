import { ClassNames } from "@emotion/react";
import React, { createContext, useEffect, useState } from "react";

export const ThemeContext = createContext();

const ThemeProvider = ({ children }) => {
  const [theme, setTheme] = useState("light"); // Default theme is dark

  const toggleTheme = () => {
    setTheme((prevTheme) => (prevTheme === "light" ? "dark" : "light"));
  };

  const themeStyles = {
    palette: {
      primary: {
        main: '#4b2e83',
      },
      background: {
        default: '#f5f7fa',
      },
    },
    typography: {
      fontFamily: 'Poppins, sans-serif',
    },
    light: {
      backgroundColor: "#f9f9f9",
      color: "#6b2d86",
      nav: {
        backgroundColor: "beige",
        color: "#6b2d86",
      },
      button: {
        className: "btn-light",
      },
      link: {
        className: "link-light",
      },
      primerViewOptions: {
        className: "primer-view-options-light",
      },

      popupClass: {
        className: "popup-light",
      },
      ref: {
        className: "ref-light",
      },
    },
    dark: {
      backgroundColor: "#111",
      color: "#fff",
      nav: {
        backgroundColor: "#111",
        color: "#fff",
      },
      button: {
        className: "btn-dark",
      },
      link: {
        className: "link-dark",
      },
      primerViewOptions: {
        className: "primer-view-options-dark",
      },
      popupClass: {
        className: "popup-dark",
      },
      ref: {
        className: "ref-dark",
      },
    },
  };

  // Apply the theme's background color to the body element
  useEffect(() => {
    document.body.style.backgroundColor = themeStyles[theme].backgroundColor;
  }, [theme]);

  return (
    <ThemeContext.Provider value={{ theme, toggleTheme, themeStyles }}>
      {children}
    </ThemeContext.Provider>
  );
};

export default ThemeProvider;
