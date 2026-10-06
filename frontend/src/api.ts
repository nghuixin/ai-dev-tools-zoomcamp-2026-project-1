import type { IssueFilters } from "./types";
import { issueService } from "./services";

export type { IssueFilters } from "./types";

export function fetchStudies() {
  return issueService.listStudies();
}

export function fetchSites(studyId?: number) {
  return issueService.listSites(studyId);
}

export function createSite(body: { study_id: number; name: string; code?: string }) {
  return issueService.createSite(body);
}

export function analyzeIssue(body: { study: string; site: string; description: string }) {
  return issueService.analyze(body);
}

export function fetchIssues(filters: IssueFilters) {
  return issueService.listIssues(filters);
}

export function fetchIssue(id: string | number) {
  return issueService.getIssue(Number(id));
}

export function createIssue(body: Record<string, unknown>) {
  return issueService.createIssue(body as Parameters<typeof issueService.createIssue>[0]);
}

export function updateIssue(id: number, body: Record<string, unknown>) {
  return issueService.updateIssue(id, body);
}

export function addNote(id: number, body: string) {
  return issueService.addNote(id, body);
}

export async function downloadCsv(filters: IssueFilters) {
  const blob = await issueService.exportCsv(filters);
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "site-issues.csv";
  link.click();
  URL.revokeObjectURL(url);
}
