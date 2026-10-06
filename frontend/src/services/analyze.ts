import { detectPhi } from "../phi";
import type { AiSuggestion, Category, Severity } from "../types";
import { CATEGORIES, CATEGORY_LABELS, SEVERITIES } from "../vocab";
import { ApiError } from "./errors";

const CATEGORY_RULES: { category: Category; re: RegExp }[] = [
  { category: "SAFETY_REPORTING", re: /\b(sae|susar|serious adverse|safety report|expedited|24-hour|reporting clock)\b/i },
  { category: "CONSENT", re: /\b(consent|icf|re-?consent|informed consent|wrong version)\b/i },
  { category: "IP_MANAGEMENT", re: /\b(investigational product|\bip\b|accountability|temperature excursion|drug kit|pharmacy)\b/i },
  { category: "REGULATORY_IRB", re: /\b(irb|iec|continuing review|regulatory packet|ethics committee)\b/i },
  { category: "ENROLLMENT", re: /\b(enroll|screening log|eligibility|randomiz|recruit)\b/i },
  { category: "DATA_QUALITY", re: /\b(query|source data|crf|edc|data cut|missing pages)\b/i },
  { category: "STAFFING_TRAINING", re: /\b(training|delegation|staffing|untrained|gcp)\b/i },
  { category: "MONITORING_FINDING", re: /\b(monitor|monitoring visit|cra finding|follow-up letter)\b/i },
  { category: "EQUIPMENT_LAB", re: /\b(centrifuge|freezer|lab kit|sample|equipment|calibration)\b/i },
  { category: "CONTRACT_BUDGET", re: /\b(invoice|budget|cta|contract|payment)\b/i },
  { category: "PROTOCOL_DEVIATION", re: /\b(protocol|deviation|visit window|out of window|inclusion|exclusion)\b/i },
];

const ACTIONS: Record<Category, string> = {
  PROTOCOL_DEVIATION:
    "Document the deviation, notify the PI, and file per the site deviation SOP. Confirm whether a protocol exception or sponsor notice is required.",
  SAFETY_REPORTING:
    "Complete the outstanding safety notification, document the clock, and confirm sponsor/IRB reporting is caught up. Do not assess causality or treatment.",
  CONSENT: "Quarantine the incorrect form, reconsent with the current IRB-approved version if required, and file a note-to-file.",
  REGULATORY_IRB:
    "Assemble the missing packet, submit to the IRB/IEC, and track acknowledgement before the next subject visit that depends on it.",
  ENROLLMENT: "Pause affected screening if eligibility is uncertain, correct the log, and confirm the next eligible slot with the PI.",
  IP_MANAGEMENT:
    "Quarantine affected kits if needed, document accountability/temperature, and notify pharmacy and the sponsor per the pharmacy manual.",
  DATA_QUALITY: "List the missing or inconsistent data, assign an owner, and close queries before the next data cut.",
  STAFFING_TRAINING:
    "Stop untrained staff from delegated tasks, complete training/delegation updates, and file certificates before the next visit.",
  MONITORING_FINDING: "Draft the site response, attach evidence of correction, and send it by the letter due date.",
  EQUIPMENT_LAB: "Take the equipment out of use if out of calibration, move samples to a qualified unit, and log the incident.",
  CONTRACT_BUDGET: "Route the invoice or amendment to the budget owner and confirm the next payment milestone.",
  OTHER: "Confirm the operational owner, write the next concrete site action, and set a follow-up date.",
};

function pickCategory(description: string): Category {
  return CATEGORY_RULES.find((rule) => rule.re.test(description))?.category ?? "OTHER";
}

function pickSeverity(description: string, category: Category): Severity {
  if (/\b(safety|rights at risk|missed (the )?deadline|24-hour|not sent|subject at risk)\b/i.test(description)) {
    return "CRITICAL";
  }
  if (category === "SAFETY_REPORTING" && /\b(missed|late|clock)\b/i.test(description)) return "CRITICAL";
  if (/\b(excursion|data integrity|compliance|wrong consent|unblinding|accountability)\b/i.test(description)) {
    return "HIGH";
  }
  if (category === "IP_MANAGEMENT" || category === "CONSENT" || category === "REGULATORY_IRB") return "HIGH";
  if (/\b(filing|admin|invoice|copy|binder)\b/i.test(description) || category === "CONTRACT_BUDGET") return "LOW";
  return "MEDIUM";
}

export function heuristicAnalyze(input: { study: string; site: string; description: string }): AiSuggestion {
  const { site, description } = input;
  if (!input.study.trim() || !site.trim() || !description.trim()) {
    throw new ApiError("study, site, and description are required");
  }
  const category = pickCategory(description);
  const severity = pickSeverity(description, category);
  const first = description.replace(/\s+/g, " ").trim().split(/(?<=[.!?])\s/)[0] || description.trim();
  const prefix = `${CATEGORY_LABELS[category]} · ${site}`;
  const summary = `${prefix}: ${first}`.slice(0, 200);
  const suggestion: AiSuggestion = {
    category,
    severity,
    summary,
    recommended_action: ACTIONS[category],
    rationale: `${severity} impact based on operational cues in the description (${CATEGORY_LABELS[category].toLowerCase()}).`,
    phi_flag: detectPhi(description),
  };
  if (!CATEGORIES.includes(suggestion.category) || !SEVERITIES.includes(suggestion.severity)) {
    throw new ApiError("suggestion unavailable", 422);
  }
  return suggestion;
}
