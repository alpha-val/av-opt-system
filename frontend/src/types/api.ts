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
  // Optional fields for async processing (when tabular files are uploaded)
  job_id?: string;
  status?: string;
  websocket_url?: string;
}

/**
 * Project report response
 */
export interface ProjectReportResponse {
  project_id: string;
  report: string; // Markdown content
  format: string;
}

/**
 * Scenario status enumeration
 */
export enum ScenarioStatus {
  DRAFT = "draft",
  PROCESSING = "processing",
  COMPLETED = "completed",
  FAILED = "failed",
  CANCELLED = "cancelled",
}

/**
 * Base scenario interface
 */
export interface ScenarioBase {
  name: string;
  description?: string | null;
  project_id: string;
  status: ScenarioStatus;
  // Global objective fields (optional - can be set later)
  global_objective_type?: string | null;
  global_objective_target?: string | null;
  global_objective_unit?: string | null;
  objective_description?: string | null;
  configuration?: Record<string, any> | null;
}

/**
 * Scenario creation request
 */
export interface ScenarioCreate extends ScenarioBase {}

/**
 * Scenario update request
 */
export interface ScenarioUpdate {
  name?: string;
  description?: string | null;
  status?: ScenarioStatus;
  global_objective_type?: string;
  global_objective_target?: string;
  global_objective_unit?: string;
  objective_description?: string | null;
  configuration?: Record<string, any> | null;
}

/**
 * Scenario output/response
 */
export interface ScenarioOut extends ScenarioBase {
  id: string;
  created_at: string;
  updated_at: string;
}

/**
 * Scenario analysis context block
 */
export interface ScenarioAnalysisContext {
  scenario_request_block?: string;
  base_case_block?: string;
  tabular_data_block?: string;
  [key: string]: any;
}

/**
 * Scenario analysis result document
 */
export interface ScenarioAnalysisResult {
  id?: string;
  _id?: string;
  scenario_id: string;
  project_id?: string;
  workflow?: string;
  job_id?: string;
  result: Record<string, any>;
  context?: ScenarioAnalysisContext;
  created_at?: string;
  updated_at?: string;
}

/**
 * Recommendation item interface
 */
export interface Recommendation {
  recommendation_id: string;
  type: string;
  title: string;
  description: string;
  rationale?: string;
  priority: "high" | "medium" | "low";
  estimated_impact?: string;
  implementation_complexity?: string;
  affected_entities?: string[];
}

/**
 * Relevant entity specification (V2 workflow)
 */
export interface RelevantEntity {
  entity_name: string;
  entity_type: string;
  msio_classification: {
    discipline: string;
    category: string;
    subcategory: string;
    entity: string;
  };
  expected_attributes?: string[];
  evidence_locations?: string[];
  rationale?: string;
  priority: "high" | "medium" | "low";
}

/**
 * Cost information structure
 */
export interface CostInfo {
  value?: number | null;
  currency?: string | null;
  unit?: string | null;
  basis?: string | null;
}

/**
 * Tabular match for cost comparison
 */
export interface TabularMatch {
  entity_id: string;
  entity_name: string;
  entity_type: string;
  cost_info: CostInfo;
  score: number;
}

/**
 * Cost comparison row
 */
export interface CostComparisonRow {
  entity_id: string;
  entity_name: string;
  entity_type: string;
  base_cost_info: CostInfo;
  tabular_matches: TabularMatch[];
}

/**
 * Cost estimate base interface
 */
export interface CostEstimateBase {
  name: string;
  description?: string | null;
  scenario_id: string;
}

/**
 * Cost estimate creation request payload
 */
export interface CostEstimateCreate extends CostEstimateBase {
  // Optional fields for cost calculation
  scenario_description?: string;
  selected_entities?: string[];
  entity_selection_state?: Record<string, boolean>;
  top_k?: number;
  revised_values?: Array<{
    entity_id: string;
    attributes: Array<{
      attr_name: string;
      revised_val: number | string | null;
    }>;
  }>;
}

/**
 * Cost estimate update request payload (all fields optional for PATCH)
 */
export interface CostEstimateUpdate {
  name?: string;
  description?: string | null;
}

/**
 * Cost estimate output/response from API
 */
export interface CostEstimateOut extends CostEstimateBase {
  id: string;
  created_at: string;
  updated_at: string;
  metadata?: {
    entity_selection_state?: Record<string, boolean>;
    cost_comparison_report?: CostComparisonRow[];
    [key: string]: any;
  };
}

/**
 * Recommendations response interface
 */
export interface RecommendationsResponse {
  id?: string;
  scenario_id: string;
  document_id?: string;
  project_id?: string;
  global_objective_type?: string;
  global_objective_target?: string;
  recommendations: Recommendation[];
  relevant_entities?: RelevantEntity[];
  workflow_version?: string;
  created_at?: string;
  updated_at?: string;
  count?: number;
  recommendations_documents?: RecommendationsResponse[];
}

