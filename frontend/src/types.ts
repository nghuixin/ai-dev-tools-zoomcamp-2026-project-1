export type Category =
  | "PROTOCOL_DEVIATION"
  | "SAFETY_REPORTING"
  | "CONSENT"
  | "REGULATORY_IRB"
  | "ENROLLMENT"
  | "IP_MANAGEMENT"
  | "DATA_QUALITY"
  | "STAFFING_TRAINING"
  | "MONITORING_FINDING"
  | "EQUIPMENT_LAB"
  | "CONTRACT_BUDGET"
  | "OTHER";

export type Severity = "CRITICAL" | "HIGH" | "MEDIUM" | "LOW";
export type Status = "OPEN" | "IN_PROGRESS" | "ESCALATED" | "RESOLVED";
export type AnalyzeTweak = "normal" | "unavailable";

export type Tweaks = {
  analyze?: AnalyzeTweak;
};

export type IssueFilters = {
  study_id?: string;
  site_id?: string;
  status?: string;
  severity?: string;
};

export type Study = {
  id: number;
  code: string;
  name: string;
};

export type Site = {
  id: number;
  study_id: number;
  code: string;
  name: string;
};

export type AiSuggestion = {
  category: Category;
  severity: Severity;
  summary: string;
  recommended_action: string;
  rationale: string;
  phi_flag: boolean;
};

export type IssueNote = {
  id: number;
  issue_id: number;
  body: string;
  created_at: string;
};

export type Issue = {
  id: number;
  study_id: number;
  site_id: number;
  study: Study;
  site: Site;
  description: string;
  category: Category;
  severity: Severity;
  summary: string;
  recommended_action: string;
  status: Status;
  owner: string | null;
  due_date: string | null;
  resolution_note: string | null;
  ai_suggestion: AiSuggestion | null;
  edited_fields: string[];
  phi_flag: boolean;
  created_at: string;
  updated_at: string;
  resolved_at: string | null;
  age_days: number;
  overdue: boolean;
  notes?: IssueNote[];
};
