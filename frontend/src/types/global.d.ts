/**
 * Global type declarations for browser environment
 * 
 * These types allow process.env to work in the browser via webpack DefinePlugin
 */

declare namespace NodeJS {
  interface ProcessEnv {
    [key: string]: string | undefined;
    REACT_APP_API_BASE_URL?: string;
    REACT_APP_OPENAI_API_KEY?: string;
  }
}

// Declare process for browser environment (provided by webpack DefinePlugin)
declare const process: {
  env: NodeJS.ProcessEnv;
};

