/**
 * API service for project operations.
 * 
 * Handles all HTTP requests to the backend API.
 */

import axios, { AxiosInstance } from "axios";
import {
  ProjectCreate,
  ProjectUpdate,
  ProjectOut,
  ClearProjectDataResponse,
  ApiError,
  FileUploadResponse,
  ProjectReportResponse,
  ProjectStatus,
} from "../types/api";

// Get API base URL from environment or use default
// Note: process.env.REACT_APP_API_BASE_URL is replaced by webpack DefinePlugin at build time
// @ts-ignore - process.env is defined by webpack DefinePlugin
const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || "http://localhost:8000";

/**
 * Create axios instance with default configuration
 */
const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

/**
 * Add request interceptor for authentication token
 * (You can add token from localStorage/Redux here)
 */
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("access_token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

/**
 * Add response interceptor for error handling
 */
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Handle unauthorized - redirect to login
      localStorage.removeItem("access_token");
      window.location.href = "/login";
    }
    return Promise.reject(error);
  }
);

/**
 * Project API service
 */
export const projectApi = {
  /**
   * Create a new project
   */
  create: async (data: ProjectCreate): Promise<ProjectOut> => {
    const response = await apiClient.post<ProjectOut>("/api/v1/projects", data);
    return response.data;
  },

  /**
   * Get all projects
   */
  listAll: async (): Promise<ProjectOut[]> => {
    const response = await apiClient.get<ProjectOut[]>("/api/v1/projects");
    return response.data;
  },

  /**
   * Get a project by ID
   */
  getById: async (projectId: string): Promise<ProjectOut> => {
    const response = await apiClient.get<ProjectOut>(
      `/api/v1/projects/${projectId}`
    );
    return response.data;
  },

  /**
   * Update a project
   */
  update: async (
    projectId: string,
    data: ProjectUpdate
  ): Promise<ProjectOut> => {
    const response = await apiClient.patch<ProjectOut>(
      `/api/v1/projects/${projectId}`,
      data
    );
    return response.data;
  },

  /**
   * Delete a project
   */
  delete: async (projectId: string): Promise<void> => {
    await apiClient.delete(`/api/v1/projects/${projectId}`);
  },

  /**
   * Clear project data (entities, relations, etc.)
   */
  clearData: async (
    projectId: string
  ): Promise<ClearProjectDataResponse> => {
    const response = await apiClient.post<ClearProjectDataResponse>(
      `/api/v1/projects/${projectId}/clear-data`
    );
    return response.data;
  },

  /**
   * Upload files for a project
   */
  uploadProjectFiles: async (
    projectId: string,
    baseCaseFiles: File[],
    tabularDataFiles: File[]
  ): Promise<FileUploadResponse> => {
    const formData = new FormData();
    
    // Append base case files
    baseCaseFiles.forEach((file) => {
      formData.append("base_case_files", file);
    });
    
    // Append tabular data files
    tabularDataFiles.forEach((file) => {
      formData.append("tabular_data_files", file);
    });
    
    const response = await apiClient.post<FileUploadResponse>(
      `/api/v1/projects/${projectId}/upload-files`,
      formData,
      {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      }
    );
    return response.data;
  },

  /**
   * Get project report (markdown)
   */
  getProjectReport: async (
    projectId: string
  ): Promise<ProjectReportResponse> => {
    const response = await apiClient.get<ProjectReportResponse>(
      `/api/v1/projects/${projectId}/report`
    );
    return response.data;
  },

  /**
   * Update project status
   */
  updateProjectStatus: async (
    projectId: string,
    status: ProjectStatus
  ): Promise<ProjectOut> => {
    const response = await apiClient.patch<ProjectOut>(
      `/api/v1/projects/${projectId}/status?status_value=${status}`,
      {}
    );
    return response.data;
  },
};

export default apiClient;

