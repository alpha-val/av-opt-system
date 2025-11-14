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
  ScenarioCreate,
  ScenarioUpdate,
  ScenarioOut,
  RecommendationsResponse,
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

  /**
   * Run or re-run analysis for a project
   */
  runAnalysis: async (projectId: string): Promise<{
    project_id: string;
    status: string;
    message: string;
    processing_result?: any;
  }> => {
    const response = await apiClient.post<{
      project_id: string;
      status: string;
      message: string;
      processing_result?: any;
    }>(`/api/v1/projects/${projectId}/run-analysis`);
    return response.data;
  },

  /**
   * List all files for a project
   */
  listProjectFiles: async (projectId: string, artifactType?: string): Promise<{
    project_id: string;
    base_case_files: Array<{
      file_id: string;
      filename: string;
      length: number;
      upload_date: string;
      content_type: string;
      artifact_type: string;
      sha256?: string;
    }>;
    tabular_data_files: Array<{
      file_id: string;
      filename: string;
      length: number;
      upload_date: string;
      content_type: string;
      artifact_type: string;
      sha256?: string;
    }>;
    total_files: number;
  }> => {
    const params = artifactType ? `?artifact_type=${artifactType}` : '';
    const response = await apiClient.get<{
      project_id: string;
      base_case_files: Array<{
        file_id: string;
        filename: string;
        length: number;
        upload_date: string;
        content_type: string;
        artifact_type: string;
        sha256?: string;
      }>;
      tabular_data_files: Array<{
        file_id: string;
        filename: string;
        length: number;
        upload_date: string;
        content_type: string;
        artifact_type: string;
        sha256?: string;
      }>;
      total_files: number;
    }>(`/api/v1/projects/${projectId}/files${params}`);
    return response.data;
  },

  /**
   * Download a project file
   */
  downloadProjectFile: async (projectId: string, fileId: string): Promise<Blob> => {
    const response = await apiClient.get<Blob>(
      `/api/v1/projects/${projectId}/files/${fileId}`,
      {
        responseType: 'blob',
      }
    );
    return response.data;
  },

  /**
   * Delete a project file
   */
  deleteProjectFile: async (projectId: string, fileId: string): Promise<void> => {
    await apiClient.delete(`/api/v1/projects/${projectId}/files/${fileId}`);
  },
};

/**
 * Scenario API service
 */
export const scenarioApi = {
  /**
   * Create a new scenario
   */
  create: async (data: ScenarioCreate): Promise<ScenarioOut> => {
    const response = await apiClient.post<ScenarioOut>("/api/v1/scenarios", data);
    return response.data;
  },

  /**
   * List all scenarios, optionally filtered by project_id
   */
  listAll: async (projectId?: string): Promise<ScenarioOut[]> => {
    const params = projectId ? `?project_id=${projectId}` : '';
    const response = await apiClient.get<ScenarioOut[]>(`/api/v1/scenarios${params}`);
    return response.data;
  },

  /**
   * Get a scenario by ID
   */
  getById: async (scenarioId: string): Promise<ScenarioOut> => {
    const response = await apiClient.get<ScenarioOut>(`/api/v1/scenarios/${scenarioId}`);
    return response.data;
  },

  /**
   * Update a scenario
   */
  update: async (scenarioId: string, data: ScenarioUpdate): Promise<ScenarioOut> => {
    const response = await apiClient.patch<ScenarioOut>(
      `/api/v1/scenarios/${scenarioId}`,
      data
    );
    return response.data;
  },

  /**
   * Delete a scenario
   */
  delete: async (scenarioId: string): Promise<void> => {
    await apiClient.delete(`/api/v1/scenarios/${scenarioId}`);
  },

  /**
   * Run or re-run analysis for a scenario
   */
  runAnalysis: async (scenarioId: string): Promise<{
    scenario_id: string;
    project_id: string;
    status: string;
    message: string;
    processing_result?: any;
  }> => {
    const response = await apiClient.post<{
      scenario_id: string;
      project_id: string;
      status: string;
      message: string;
      processing_result?: any;
    }>(`/api/v1/scenarios/${scenarioId}/run-analysis`);
    return response.data;
  },

  /**
   * Run or re-run analysis for a scenario using V2 workflow
   */
  runAnalysisV2: async (
    scenarioId: string,
    options?: {
      extract_summary?: boolean;
      extraction_scope?: "exact" | "with_relationships" | "with_context";
    }
  ): Promise<{
    scenario_id: string;
    project_id: string;
    status: string;
    workflow_version: string;
    message: string;
    documents_processed: number;
    document_results: Array<{
      document_id: string;
      status: string;
      entities_extracted: number;
      relations_extracted: number;
      summary_id?: string;
      recommendations_id?: string;
      relevant_entities_count: number;
      recommendations_count: number;
      extraction_scope: string;
    }>;
    errors?: Array<{
      document_id: string;
      error?: string;
      warning?: string;
    }>;
  }> => {
    const params = new URLSearchParams();
    if (options?.extract_summary !== undefined) {
      params.append("extract_summary", String(options.extract_summary));
    }
    if (options?.extraction_scope) {
      params.append("extraction_scope", options.extraction_scope);
    }
    const queryString = params.toString();
    const url = `/api/v1/scenarios/${scenarioId}/run-analysis-v2${
      queryString ? `?${queryString}` : ""
    }`;
    const response = await apiClient.post<{
      scenario_id: string;
      project_id: string;
      status: string;
      workflow_version: string;
      message: string;
      documents_processed: number;
      document_results: Array<{
        document_id: string;
        status: string;
        entities_extracted: number;
        relations_extracted: number;
        summary_id?: string;
        recommendations_id?: string;
        relevant_entities_count: number;
        recommendations_count: number;
        extraction_scope: string;
      }>;
      errors?: Array<{
        document_id: string;
        error?: string;
        warning?: string;
      }>;
    }>(url);
    return response.data;
  },

  /**
   * Get recommendations for a scenario
   */
  getRecommendations: async (scenarioId: string): Promise<RecommendationsResponse> => {
    const response = await apiClient.get<RecommendationsResponse>(
      `/api/v1/scenarios/${scenarioId}/recommendations`
    );
    return response.data;
  },

  /**
   * Get entities for a scenario
   */
  getEntities: async (
    scenarioId: string,
    artifactType: string = "base_case"
  ): Promise<{
    scenario_id: string;
    artifact_type: string;
    entities: Array<{
      id: string;
      type: string;
      properties: {
        name?: string;
        discipline?: string;
        category?: string;
        subcategory?: string;
        entity?: string;
        attributes?: Array<{
          name: string;
          value: number | null;
          unit: string | null;
          evidence_text: string | null;
          confidence: number;
        }>;
        [key: string]: any;
      };
    }>;
    count: number;
  }> => {
    const response = await apiClient.get<{
      scenario_id: string;
      artifact_type: string;
      entities: Array<{
        id: string;
        type: string;
        properties: {
          name?: string;
          discipline?: string;
          category?: string;
          subcategory?: string;
          entity?: string;
          attributes?: Array<{
            name: string;
            value: number | null;
            unit: string | null;
            evidence_text: string | null;
            confidence: number;
          }>;
          [key: string]: any;
        };
      }>;
      count: number;
    }>(`/api/v1/scenarios/${scenarioId}/entities?artifact_type=${artifactType}`);
    return response.data;
  },
};

/**
 * Delete all user data
 */
export const deleteAllUserData = async (): Promise<{
  user_id: string;
  deleted_counts: {
    projects: number;
    scenarios: number;
    files: number;
  };
  total_items: number;
}> => {
  const response = await apiClient.delete<{
    user_id: string;
    deleted_counts: {
      projects: number;
      scenarios: number;
      files: number;
    };
    total_items: number;
  }>("/api/v1/projects/delete-all-user-data");
  return response.data;
};

export default apiClient;

