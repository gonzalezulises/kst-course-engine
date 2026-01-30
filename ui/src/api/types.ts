// TS mirrors of all Pydantic API models

// --- Request types ---

export interface ItemInput {
  id: string;
  label?: string;
}

export interface DomainInput {
  name: string;
  description?: string;
  items: ItemInput[];
}

export interface PrerequisitesInput {
  edges: [string, string][];
}

export interface CourseInput {
  domain: DomainInput;
  prerequisites?: PrerequisitesInput;
}

export interface SimulateRequest {
  domain: DomainInput;
  prerequisites?: PrerequisitesInput;
  learners?: number;
  beta?: number;
  eta?: number;
  seed?: number | null;
}

export interface ExportRequest {
  domain: DomainInput;
  prerequisites?: PrerequisitesInput;
  format?: "dot" | "mermaid" | "json";
  type?: "hasse" | "prerequisites";
}

export interface AssessStartRequest {
  domain: DomainInput;
  prerequisites?: PrerequisitesInput;
  beta?: number;
  eta?: number;
}

export interface AssessRespondRequest {
  correct: boolean;
}

// --- Response types ---

export interface InfoResponse {
  name: string;
  description: string;
  items: number;
  states: number;
  prerequisites: number;
  critical_path: string[];
  critical_path_length: number;
  learning_paths: number;
}

export interface ValidationCheckResponse {
  property_name: string;
  passed: boolean;
  message: string;
  reference: string;
}

export interface ValidationResponse {
  is_valid: boolean;
  summary: string;
  results: ValidationCheckResponse[];
}

export interface PathsResponse {
  total: number;
  paths: string[][];
}

export interface SimulateResponse {
  learners: number;
  accuracy: number;
  accuracy_pct: number;
  avg_questions: number;
  expected_steps: number;
  simulated_avg_steps: number;
}

export interface ExportResponse {
  format: string;
  type: string;
  content: string;
}

export interface AssessStartResponse {
  session_id: string;
  first_item: string;
}

export interface AssessStepResponse {
  item_id: string;
  correct: boolean;
  entropy_before: number;
  entropy_after: number;
  estimate_ids: string[];
}

export interface AssessRespondResponse {
  step: AssessStepResponse;
  next_item: string | null;
  is_complete: boolean;
}

export interface AssessSummaryResponse {
  total_questions: number;
  final_state_ids: string[];
  confidence: number;
  mastered: string[];
  not_mastered: string[];
}
