import type { Category, Severity, Status } from "./types";

export const CATEGORIES: Category[] = [
  "PROTOCOL_DEVIATION",
  "SAFETY_REPORTING",
  "CONSENT",
  "REGULATORY_IRB",
  "ENROLLMENT",
  "IP_MANAGEMENT",
  "DATA_QUALITY",
  "STAFFING_TRAINING",
  "MONITORING_FINDING",
  "EQUIPMENT_LAB",
  "CONTRACT_BUDGET",
  "OTHER",
];

export const CATEGORY_LABELS: Record<Category, string> = {
  PROTOCOL_DEVIATION: "Protocol deviation",
  SAFETY_REPORTING: "Safety reporting",
  CONSENT: "Consent",
  REGULATORY_IRB: "Regulatory / IRB",
  ENROLLMENT: "Enrollment",
  IP_MANAGEMENT: "IP management",
  DATA_QUALITY: "Data quality",
  STAFFING_TRAINING: "Staffing / training",
  MONITORING_FINDING: "Monitoring finding",
  EQUIPMENT_LAB: "Equipment / lab",
  CONTRACT_BUDGET: "Contract / budget",
  OTHER: "Other",
};

export const SEVERITIES: Severity[] = ["CRITICAL", "HIGH", "MEDIUM", "LOW"];

export const SEVERITY_LABELS: Record<Severity, string> = {
  CRITICAL: "Critical",
  HIGH: "High",
  MEDIUM: "Medium",
  LOW: "Low",
};

export const DUE_DAYS: Record<Severity, number> = {
  CRITICAL: 1,
  HIGH: 5,
  MEDIUM: 15,
  LOW: 30,
};

export const STATUSES: Status[] = ["OPEN", "IN_PROGRESS", "ESCALATED", "RESOLVED"];

export const STATUS_LABELS: Record<Status, string> = {
  OPEN: "Open",
  IN_PROGRESS: "In progress",
  ESCALATED: "Escalated",
  RESOLVED: "Resolved",
};

export function dueHint(severity?: Severity | "") {
  if (!severity) return "Due date defaults from severity once you pick one.";
  const days = DUE_DAYS[severity];
  const unit = days === 1 ? "day" : "days";
  return `If left blank, due date defaults to ${days} ${unit} from today (${SEVERITY_LABELS[severity]}).`;
}

export function formatDate(value?: string | null) {
  if (!value) return "—";
  const date = new Date(`${value.slice(0, 10)}T12:00:00`);
  return date.toLocaleDateString("en-GB", {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
}

export function formatAge(days: number) {
  if (days <= 0) return "today";
  if (days === 1) return "1d";
  return `${days}d`;
}
