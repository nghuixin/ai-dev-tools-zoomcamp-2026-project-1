import type { AiSuggestion, Issue, IssueNote, Site, Study } from "../types";
import { ApiError } from "./errors";
import type {
  CreateIssueInput,
  CreateSiteInput,
  IssueService,
  UpdateIssueInput,
} from "./issueService";
import type { IssueFilters } from "../types";

export const DEFAULT_API_URL = "http://127.0.0.1:8000";

function apiBaseUrl() {
  const fromEnv = import.meta.env.VITE_API_URL;
  // Empty string (Docker same-origin build) must not fall back to localhost.
  if (typeof fromEnv === "string") return fromEnv.replace(/\/$/, "");
  return DEFAULT_API_URL;
}

function issueQuery(filters: IssueFilters) {
  const params = new URLSearchParams();
  if (filters.study_id) params.set("study_id", filters.study_id);
  if (filters.site_id) params.set("site_id", filters.site_id);
  if (filters.status) params.set("status", filters.status);
  if (filters.severity) params.set("severity", filters.severity);
  const encoded = params.toString();
  return encoded ? `?${encoded}` : "";
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${apiBaseUrl()}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers || {}),
    },
  });
  if (!res.ok) {
    const payload = (await res.json().catch(() => ({}))) as { error?: string };
    throw new ApiError(payload.error || `Request failed (${res.status})`, res.status);
  }
  return res.json() as Promise<T>;
}

export function createHttpIssueService(): IssueService {
  return {
    listStudies: () => request<Study[]>("/api/studies"),
    listSites: (studyId) =>
      request<Site[]>(`/api/sites${studyId ? `?study_id=${studyId}` : ""}`),
    createSite: (input: CreateSiteInput) =>
      request<Site>("/api/sites", { method: "POST", body: JSON.stringify(input) }),
    analyze: (input) =>
      request<AiSuggestion>("/api/issues/analyze", {
        method: "POST",
        body: JSON.stringify(input),
      }),
    listIssues: (filters) => request<Issue[]>(`/api/issues${issueQuery(filters)}`),
    getIssue: (id) => request<Issue>(`/api/issues/${id}`),
    createIssue: (input: CreateIssueInput) =>
      request<Issue>("/api/issues", { method: "POST", body: JSON.stringify(input) }),
    updateIssue: (id, input: UpdateIssueInput) =>
      request<Issue>(`/api/issues/${id}`, { method: "PATCH", body: JSON.stringify(input) }),
    addNote: (id, body) =>
      request<IssueNote>(`/api/issues/${id}/notes`, {
        method: "POST",
        body: JSON.stringify({ body }),
      }),
    async exportCsv(filters) {
      const res = await fetch(`${apiBaseUrl()}/api/issues.csv${issueQuery(filters)}`);
      if (!res.ok) throw new ApiError("Could not export CSV", res.status);
      return res.blob();
    },
  };
}
