import type { AiSuggestion, Issue, IssueFilters, IssueNote, Site, Study } from "../types";

export type CreateSiteInput = {
  study_id: number;
  name: string;
  code?: string;
};

export type CreateIssueInput = {
  study_id: number;
  site_id: number;
  description: string;
  category: string;
  severity: string;
  summary?: string;
  recommended_action?: string;
  owner?: string | null;
  due_date?: string | null;
  ai_suggestion?: AiSuggestion | null;
  phi_flag?: boolean;
};

export type UpdateIssueInput = Partial<
  Omit<CreateIssueInput, "ai_suggestion"> & { status: string; resolution_note: string | null }
>;

/**
 * Single integration point for every backend call.
 * Swap the mock for HTTP when the FastAPI backend exists.
 */
export interface IssueService {
  listStudies(): Promise<Study[]>;
  listSites(studyId?: number): Promise<Site[]>;
  createSite(input: CreateSiteInput): Promise<Site>;
  analyze(input: { study: string; site: string; description: string }): Promise<AiSuggestion>;
  listIssues(filters: IssueFilters): Promise<Issue[]>;
  getIssue(id: number): Promise<Issue>;
  createIssue(input: CreateIssueInput): Promise<Issue>;
  updateIssue(id: number, input: UpdateIssueInput): Promise<Issue>;
  addNote(id: number, body: string): Promise<IssueNote>;
  exportCsv(filters: IssueFilters): Promise<Blob>;
}
