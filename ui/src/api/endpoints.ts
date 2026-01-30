import { apiFetch } from "./client";
import type {
  CourseInput,
  SimulateRequest,
  ExportRequest,
  AssessStartRequest,
  AssessRespondRequest,
  InfoResponse,
  ValidationResponse,
  PathsResponse,
  SimulateResponse,
  ExportResponse,
  AssessStartResponse,
  AssessRespondResponse,
  AssessSummaryResponse,
} from "./types";

export function fetchInfo(data: CourseInput): Promise<InfoResponse> {
  return apiFetch("/info", { method: "POST", body: JSON.stringify(data) });
}

export function fetchValidation(
  data: CourseInput,
): Promise<ValidationResponse> {
  return apiFetch("/validate", { method: "POST", body: JSON.stringify(data) });
}

export function fetchPaths(data: CourseInput): Promise<PathsResponse> {
  return apiFetch("/paths", { method: "POST", body: JSON.stringify(data) });
}

export function fetchSimulation(
  data: SimulateRequest,
): Promise<SimulateResponse> {
  return apiFetch("/simulate", { method: "POST", body: JSON.stringify(data) });
}

export function fetchExport(data: ExportRequest): Promise<ExportResponse> {
  return apiFetch("/export", { method: "POST", body: JSON.stringify(data) });
}

export function startAssessment(
  data: AssessStartRequest,
): Promise<AssessStartResponse> {
  return apiFetch("/assess/start", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function respondAssessment(
  sessionId: string,
  data: AssessRespondRequest,
): Promise<AssessRespondResponse> {
  return apiFetch(`/assess/${sessionId}/respond`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function fetchAssessmentSummary(
  sessionId: string,
): Promise<AssessSummaryResponse> {
  return apiFetch(`/assess/${sessionId}/summary`);
}
