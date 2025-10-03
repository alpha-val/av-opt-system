const REACT_APP_CONFIG_PROD = {
  url: {
    API_URL: "" // TBD example "https://alpha-val.onrender.com/api/v1",
  },
  allow_guest: true,
  dev: false,
  debug_log: false,
};
const REACT_APP_CONFIG_DEV = {
  url: {
    API_URL: "http://localhost:8000/api/v1",
  },
  allow_guest: true,
  dev: true,
  debug_log: true,
  dummy: "hello_world",
};

const REACT_APP_CONFIG =
  process.env.NODE_ENV === "production"
    ? REACT_APP_CONFIG_PROD
    : REACT_APP_CONFIG_DEV;

REACT_APP_CONFIG["versions"] = {
  released: {
    number: "0.5",
    date: "07-10-2025",
    features: ["Athlete profiles, events"],
    contact: { name: "Sid Thakur", email: "rfactor.corp@gmail.com" },
    copyrightText: "Copyright 2025, Alpha-Val.",
    license:
      "Trial - All rights reserved. See data and terms policy on the main website.",
  },
  candidate: {
    number: "0.",
    date: "- - 2025",
    features: ["TO DO"],
    contact: { name: "Sid Thakur", email: "rfactor.corp@gmail.com" },
    copyrightText: "Copyright 2025, Alpha-Val.",
    license:
      "Trial - All rights reserved. See data and terms policy on the main website.",
  },
  history: [],
};
export default REACT_APP_CONFIG;