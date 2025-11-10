/**
 * API type definitions matching backend schemas.
 * 
 * These types correspond to the Pydantic models in the backend.
 * Keep them in sync with backend/app_v3/domain/projects/schemas.py
 */

/**
 * Project status enumeration
 */
export enum ProjectStatus {
  DRAFT = "draft",
  PROCESSING = "processing",
  VALIDATION = "validation",
  COMPLETED = "completed",
}

/**
 * Base project interface with common fields
 */
export interface ProjectBase {
  name: string;
  description?: string | null;
  tags?: string[] | null;
  // Global objective fields
  global_objective_type: string;
  global_objective_target: string;
  objective_description?: string | null;
  // Project status
  status: ProjectStatus;
  // Document references
  base_case_documents: string[];
  tabular_data_documents: string[];
}

/**
 * Project creation request payload
 */
export interface ProjectCreate extends ProjectBase {}

/**
 * Project update request payload (all fields optional for PATCH)
 */
export interface ProjectUpdate {
  name?: string;
  description?: string | null;
  tags?: string[] | null;
  global_objective_type?: string;
  global_objective_target?: string;
  objective_description?: string | null;
  status?: ProjectStatus;
  base_case_documents?: string[];
  tabular_data_documents?: string[];
}

/**
 * Project output/response from API
 */
export interface ProjectOut extends ProjectBase {
  id: string;
  created_at: string; // ISO 8601 datetime string
  updated_at: string; // ISO 8601 datetime string
}

/**
 * API response wrapper for list operations
 */
export interface ApiListResponse<T> {
  items: T[];
  count?: number;
}

/**
 * API error response
 */
export interface ApiError {
  detail: string;
  status_code?: number;
}

/**
 * Clear project data response
 */
export interface ClearProjectDataResponse {
  project_id: string;
  deleted_counts: {
    entities: number;
    relations: number;
  };
  total_items: number;
}

/**
 * File upload response
 */
export interface FileUploadResponse {
  project_id: string;
  base_case_documents: string[];
  tabular_data_documents: string[];
  total_files: number;
  total_size_bytes: number;
  message: string;
}

/**
 * Project report response
 */
export interface ProjectReportResponse {
  project_id: string;
  report: string; // Markdown content
  format: string;
}

