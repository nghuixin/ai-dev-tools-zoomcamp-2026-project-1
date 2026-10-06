import { detectPhi } from "../phi";
import type {
  Category,
  Issue,
  IssueFilters,
  IssueNote,
  Severity,
  Status,
} from "../types";
import { CATEGORIES, DUE_DAYS, SEVERITIES, STATUSES } from "../vocab";
import { heuristicAnalyze } from "./analyze";
import { ApiError } from "./errors";
import type {
  CreateIssueInput,
  CreateSiteInput,
  IssueService,
  UpdateIssueInput,
} from "./issueService";
import { seedSnapshot, type Snapshot, type StoredIssue } from "./seed";

const STORE_KEY = "site-issue-triage.mock.v1";
const SEVERITY_RANK: Record<Severity, number> = {
  CRITICAL: 0,
  HIGH: 1,
  MEDIUM: 2,
  LOW: 3,
};
const EDIT_FIELDS = ["category", "severity", "summary", "recommended_action"] as const;

function todayDate() {
  return new Date().toISOString().slice(0, 10);
}

function addDays(days: number) {
  const d = new Date(`${todayDate()}T12:00:00`);
  d.setDate(d.getDate() + days);
  return d.toISOString().slice(0, 10);
}

function ageDays(createdAt: string) {
  return Math.max(0, Math.floor((Date.now() - new Date(createdAt).getTime()) / 86400000));
}

function load(): Snapshot {
  const raw = localStorage.getItem(STORE_KEY);
  if (!raw) {
    const seeded = seedSnapshot();
    save(seeded);
    return seeded;
  }
  try {
    return JSON.parse(raw) as Snapshot;
  } catch {
    const seeded = seedSnapshot();
    save(seeded);
    return seeded;
  }
}

function save(snapshot: Snapshot) {
  localStorage.setItem(STORE_KEY, JSON.stringify(snapshot));
}

function shape(snapshot: Snapshot, issue: StoredIssue, withNotes = false): Issue {
  const study = snapshot.studies.find((item) => item.id === issue.study_id);
  const site = snapshot.sites.find((item) => item.id === issue.site_id);
  if (!study || !site) throw new ApiError("Issue is missing study or site", 500);
  const suggestion = issue.ai_suggestion;
  return {
    ...issue,
    study,
    site,
    edited_fields: suggestion
      ? EDIT_FIELDS.filter((field) => String(issue[field] ?? "").trim() !== String(suggestion[field] ?? "").trim())
      : [],
    age_days: ageDays(issue.created_at),
    overdue: Boolean(issue.due_date && issue.status !== "RESOLVED" && issue.due_date < todayDate()),
    notes: withNotes
      ? snapshot.notes.filter((note) => note.issue_id === issue.id).sort((a, b) => a.id - b.id)
      : undefined,
  };
}

function filtered(snapshot: Snapshot, filters: IssueFilters) {
  let rows = snapshot.issues.slice();
  if (filters.study_id) rows = rows.filter((row) => row.study_id === Number(filters.study_id));
  if (filters.site_id) rows = rows.filter((row) => row.site_id === Number(filters.site_id));
  if (filters.severity) rows = rows.filter((row) => row.severity === filters.severity);
  if (!filters.status || filters.status === "active") {
    rows = rows.filter((row) => row.status !== "RESOLVED");
  } else if (filters.status !== "ALL") {
    rows = rows.filter((row) => row.status === filters.status);
  }
  rows.sort((a, b) => {
    const rank = SEVERITY_RANK[a.severity] - SEVERITY_RANK[b.severity];
    if (rank !== 0) return rank;
    if (a.created_at === b.created_at) return a.id - b.id;
    return a.created_at < b.created_at ? -1 : 1;
  });
  return rows.map((row) => shape(snapshot, row));
}

function toCsv(issues: Issue[]) {
  const headers = [
    "id",
    "study",
    "site",
    "severity",
    "status",
    "summary",
    "category",
    "owner",
    "due_date",
    "age_days",
    "overdue",
  ];
  const escape = (value: unknown) => {
    const text = value == null ? "" : String(value);
    if (/[",\n]/.test(text)) return `"${text.replaceAll('"', '""')}"`;
    return text;
  };
  const lines = [
    headers.join(","),
    ...issues.map((row) =>
      [
        row.id,
        `${row.study.code} ${row.study.name}`,
        `${row.site.code} ${row.site.name}`,
        row.severity,
        row.status,
        row.summary,
        row.category,
        row.owner ?? "",
        row.due_date ?? "",
        row.age_days,
        row.overdue ? "yes" : "no",
      ]
        .map(escape)
        .join(","),
    ),
  ];
  return new Blob([lines.join("\n")], { type: "text/csv;charset=utf-8" });
}

export function createMockIssueService(): IssueService {
  return {
    async listStudies() {
      return load().studies.slice().sort((a, b) => a.code.localeCompare(b.code));
    },
    async listSites(studyId) {
      const sites = load().sites.filter((site) => (studyId ? site.study_id === studyId : true));
      return sites.sort((a, b) => a.code.localeCompare(b.code));
    },
    async createSite(input: CreateSiteInput) {
      const snapshot = load();
      if (!snapshot.studies.some((study) => study.id === input.study_id)) {
        throw new ApiError("Unknown study");
      }
      const name = input.name.trim();
      if (!name) throw new ApiError("study_id and name are required");
      let code = (input.code || "").trim();
      if (!code) {
        const count = snapshot.sites.filter((site) => site.study_id === input.study_id).length;
        code = String(count + 1).padStart(2, "0");
      }
      if (snapshot.sites.some((site) => site.study_id === input.study_id && site.code === code)) {
        throw new ApiError("Could not add site. Use a unique site number for this study.");
      }
      const site = { id: snapshot.nextIds.site, study_id: input.study_id, code, name };
      snapshot.sites.push(site);
      snapshot.nextIds.site += 1;
      save(snapshot);
      return site;
    },
    async analyze(input) {
      return heuristicAnalyze(input);
    },
    async listIssues(filters) {
      return filtered(load(), filters);
    },
    async getIssue(id) {
      const snapshot = load();
      const issue = snapshot.issues.find((row) => row.id === id);
      if (!issue) throw new ApiError("Issue not found", 404);
      return shape(snapshot, issue, true);
    },
    async createIssue(input: CreateIssueInput) {
      if (!input.description?.trim() || !input.category || !input.severity) {
        throw new ApiError("description, category, and severity are required");
      }
      if (!CATEGORIES.includes(input.category as Category) || !SEVERITIES.includes(input.severity as Severity)) {
        throw new ApiError("Invalid category or severity");
      }
      const snapshot = load();
      const site = snapshot.sites.find(
        (row) => row.id === input.site_id && row.study_id === input.study_id,
      );
      if (!site) throw new ApiError("Site does not belong to the selected study");
      const now = new Date().toISOString();
      const issue: StoredIssue = {
        id: snapshot.nextIds.issue,
        study_id: input.study_id,
        site_id: input.site_id,
        description: input.description.trim(),
        category: input.category as Category,
        severity: input.severity as Severity,
        summary: (input.summary || "").trim(),
        recommended_action: (input.recommended_action || "").trim(),
        status: "OPEN",
        owner: input.owner?.trim() || null,
        due_date: input.due_date?.trim() || addDays(DUE_DAYS[input.severity as Severity]),
        resolution_note: null,
        ai_suggestion: input.ai_suggestion ?? null,
        phi_flag: input.phi_flag ?? detectPhi(input.description),
        created_at: now,
        updated_at: now,
        resolved_at: null,
      };
      snapshot.issues.push(issue);
      snapshot.nextIds.issue += 1;
      save(snapshot);
      return shape(snapshot, issue, true);
    },
    async updateIssue(id, input: UpdateIssueInput) {
      const snapshot = load();
      const existing = snapshot.issues.find((row) => row.id === id);
      if (!existing) throw new ApiError("Issue not found", 404);
      const next = {
        ...existing,
        ...input,
        owner: input.owner === undefined ? existing.owner : String(input.owner || "").trim() || null,
        due_date: input.due_date === undefined ? existing.due_date : input.due_date,
        resolution_note:
          input.resolution_note === undefined
            ? existing.resolution_note
            : String(input.resolution_note || "").trim() || null,
        phi_flag: input.phi_flag ?? existing.phi_flag,
      };
      const category = next.category as Category;
      const severity = next.severity as Severity;
      if (!CATEGORIES.includes(category) || !SEVERITIES.includes(severity)) {
        throw new ApiError("Invalid category or severity");
      }
      if (!STATUSES.includes(next.status as Status)) throw new ApiError("Invalid status");
      if (next.status === "RESOLVED" && !String(next.resolution_note || "").trim()) {
        throw new ApiError("Resolution note required");
      }
      if (!snapshot.sites.some((site) => site.id === next.site_id && site.study_id === next.study_id)) {
        throw new ApiError("Site does not belong to the selected study");
      }
      next.category = category;
      next.severity = severity;
      if (!String(next.due_date || "").trim()) next.due_date = addDays(DUE_DAYS[severity]);
      if (next.status === "RESOLVED" && !next.resolved_at) next.resolved_at = new Date().toISOString();
      next.updated_at = new Date().toISOString();
      Object.assign(existing, next);
      save(snapshot);
      return shape(snapshot, existing, true);
    },
    async addNote(id, body) {
      const text = body.trim();
      if (!text) throw new ApiError("Note body is required");
      const snapshot = load();
      if (!snapshot.issues.some((issue) => issue.id === id)) throw new ApiError("Issue not found", 404);
      const note: IssueNote = {
        id: snapshot.nextIds.note,
        issue_id: id,
        body: text,
        created_at: new Date().toISOString(),
      };
      snapshot.notes.push(note);
      snapshot.nextIds.note += 1;
      save(snapshot);
      return note;
    },
    async exportCsv(filters) {
      return toCsv(filtered(load(), filters));
    },
  };
}
