import type { AiSuggestion, Category, IssueNote, Severity, Status } from "../types";
import { DUE_DAYS } from "../vocab";

export type StoredStudy = { id: number; code: string; name: string };
export type StoredSite = { id: number; study_id: number; code: string; name: string };
export type StoredIssue = {
  id: number;
  study_id: number;
  site_id: number;
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
  phi_flag: boolean;
  created_at: string;
  updated_at: string;
  resolved_at: string | null;
};
export type Snapshot = {
  studies: StoredStudy[];
  sites: StoredSite[];
  issues: StoredIssue[];
  notes: IssueNote[];
  nextIds: { site: number; issue: number; note: number };
};

function isoDaysFromToday(offset: number) {
  const d = new Date();
  d.setHours(12, 0, 0, 0);
  d.setDate(d.getDate() + offset);
  return d.toISOString();
}

function dateDaysFromToday(offset: number) {
  return isoDaysFromToday(offset).slice(0, 10);
}

export function seedSnapshot(): Snapshot {
  const studies: StoredStudy[] = [
    { id: 1, code: "ST-104", name: "HARMONY NSCLC" },
    { id: 2, code: "ST-221", name: "RIVER Heart Failure" },
    { id: 3, code: "ST-018", name: "LARK RSV Vaccine" },
  ];
  const sites: StoredSite[] = [
    { id: 1, study_id: 1, code: "01", name: "Metro General" },
    { id: 2, study_id: 1, code: "04", name: "Lakeside Research" },
    { id: 3, study_id: 1, code: "12", name: "North Clinic" },
    { id: 4, study_id: 2, code: "02", name: "Harbor Medical" },
    { id: 5, study_id: 2, code: "07", name: "Valley Site" },
    { id: 6, study_id: 3, code: "03", name: "Ridgeview" },
  ];

  const rows: Array<
    Omit<StoredIssue, "id" | "created_at" | "updated_at" | "due_date" | "resolved_at"> & {
      createdOffset: number;
      resolvedOffset?: number;
    }
  > = [
    {
      study_id: 1,
      site_id: 1,
      createdOffset: -6,
      status: "OPEN",
      owner: "Site manager",
      category: "SAFETY_REPORTING",
      severity: "CRITICAL",
      phi_flag: false,
      resolution_note: null,
      description:
        "The 24-hour sponsor notification for a serious adverse event identified at last week's visit was not sent. The reporting clock is already past due.",
      summary: "Missed 24-hour SAE notification clock at Metro General.",
      recommended_action:
        "Send the outstanding sponsor notification now, document the clock start/stop, and confirm IRB reporting status. Do not assess causality.",
      ai_suggestion: {
        category: "SAFETY_REPORTING",
        severity: "CRITICAL",
        summary: "Missed 24-hour SAE notification clock at Metro General.",
        recommended_action:
          "Send the outstanding sponsor notification now, document the clock start/stop, and confirm IRB reporting status. Do not assess causality.",
        rationale: "A missed safety reporting deadline is critical operational impact.",
        phi_flag: false,
      },
    },
    {
      study_id: 1,
      site_id: 2,
      createdOffset: -3,
      status: "IN_PROGRESS",
      owner: "Pharmacy",
      category: "IP_MANAGEMENT",
      severity: "HIGH",
      phi_flag: false,
      resolution_note: null,
      description:
        "Pharmacy documented a temperature excursion on the investigational product refrigerator overnight. Kits on the affected shelf have not been quarantined in the IRT.",
      summary: "IP refrigerator excursion; kits not yet quarantined in IRT.",
      recommended_action:
        "Quarantine affected kits in IRT, keep them out of dispensing, and notify pharmacy and the sponsor per the pharmacy manual.",
      ai_suggestion: {
        category: "IP_MANAGEMENT",
        severity: "HIGH",
        summary: "IP refrigerator excursion; kits not yet quarantined in IRT.",
        recommended_action:
          "Quarantine affected kits in IRT, keep them out of dispensing, and notify pharmacy and the sponsor per the pharmacy manual.",
        rationale: "IP accountability gaps threaten supply and compliance if not fixed soon.",
        phi_flag: false,
      },
    },
    {
      study_id: 2,
      site_id: 4,
      createdOffset: -4,
      status: "OPEN",
      owner: "CRC",
      category: "CONSENT",
      severity: "HIGH",
      phi_flag: false,
      resolution_note: null,
      description:
        "Two screenings this week used consent version 3.0 after IRB approved version 4.1. The current version is in the regulatory binder but was not placed in the visit kits.",
      summary: "Screenings used expired consent version 3.0 instead of 4.1.",
      recommended_action: "Stop using version 3.0, reconsent with 4.1 if required, and replace visit-kit copies.",
      ai_suggestion: {
        category: "CONSENT",
        severity: "MEDIUM",
        summary: "Wrong consent version used at screening.",
        recommended_action: "Replace the form in the kit and reconsent if required.",
        rationale: "Consent version mismatch is usually a contained process gap.",
        phi_flag: false,
      },
    },
    {
      study_id: 1,
      site_id: 3,
      createdOffset: -8,
      status: "OPEN",
      owner: null,
      category: "PROTOCOL_DEVIATION",
      severity: "MEDIUM",
      phi_flag: false,
      resolution_note: null,
      description:
        "Week 8 visits for two participants were completed three days outside the protocol window. The PI has not yet signed the deviation forms.",
      summary: "Two Week 8 visits completed outside the protocol window.",
      recommended_action: "Complete deviation forms, obtain PI signature, and file per the site deviation SOP.",
      ai_suggestion: {
        category: "PROTOCOL_DEVIATION",
        severity: "MEDIUM",
        summary: "Two Week 8 visits completed outside the protocol window.",
        recommended_action: "Complete deviation forms, obtain PI signature, and file per the site deviation SOP.",
        rationale: "Out-of-window visits are a contained protocol process gap.",
        phi_flag: false,
      },
    },
    {
      study_id: 3,
      site_id: 6,
      createdOffset: -10,
      status: "ESCALATED",
      owner: "Regulatory",
      category: "REGULATORY_IRB",
      severity: "HIGH",
      phi_flag: false,
      resolution_note: null,
      description:
        "Continuing review acknowledgement from the IRB is not in the binder and expires in four days. The coordinator has not received the approval letter.",
      summary: "IRB continuing review acknowledgement missing; expiry in four days.",
      recommended_action:
        "Obtain the IRB acknowledgement, file it, and confirm coverage before visits that depend on it.",
      ai_suggestion: {
        category: "REGULATORY_IRB",
        severity: "HIGH",
        summary: "IRB continuing review acknowledgement missing; expiry in four days.",
        recommended_action:
          "Obtain the IRB acknowledgement, file it, and confirm coverage before visits that depend on it.",
        rationale: "An approaching IRB expiry threatens compliance if not closed soon.",
        phi_flag: false,
      },
    },
    {
      study_id: 2,
      site_id: 5,
      createdOffset: -2,
      status: "OPEN",
      owner: "Data manager",
      category: "DATA_QUALITY",
      severity: "HIGH",
      phi_flag: false,
      resolution_note: null,
      description:
        "Thirty-two open queries are aging past 14 days, including several source-to-CRF mismatches on primary endpoint pages before Friday's data cut.",
      summary: "32 queries aging past 14 days ahead of Friday data cut.",
      recommended_action: "Prioritize endpoint-page queries, assign owners, and close them before the data cut.",
      ai_suggestion: {
        category: "DATA_QUALITY",
        severity: "HIGH",
        summary: "32 queries aging past 14 days ahead of Friday data cut.",
        recommended_action: "Prioritize endpoint-page queries, assign owners, and close them before the data cut.",
        rationale: "Unresolved endpoint queries threaten data integrity before a cut.",
        phi_flag: false,
      },
    },
    {
      study_id: 1,
      site_id: 1,
      createdOffset: -1,
      status: "OPEN",
      owner: "CRC",
      category: "ENROLLMENT",
      severity: "MEDIUM",
      phi_flag: false,
      resolution_note: null,
      description:
        "The screening log is missing outcomes for last Thursday's pre-screens, so the site cannot confirm which patients are still pending eligibility review.",
      summary: "Screening log missing Thursday pre-screen outcomes.",
      recommended_action:
        "Backfill the screening log and confirm pending eligibility with the PI before the next slot.",
      ai_suggestion: {
        category: "ENROLLMENT",
        severity: "MEDIUM",
        summary: "Screening log missing Thursday pre-screen outcomes.",
        recommended_action:
          "Backfill the screening log and confirm pending eligibility with the PI before the next slot.",
        rationale: "Log gaps are a contained enrollment process issue.",
        phi_flag: false,
      },
    },
    {
      study_id: 3,
      site_id: 6,
      createdOffset: -12,
      status: "OPEN",
      owner: "Lab",
      category: "EQUIPMENT_LAB",
      severity: "MEDIUM",
      phi_flag: false,
      resolution_note: null,
      description:
        "The backup freezer alarm was silenced during a weekend power blip. Calibration is current, but the incident was not logged and staff are unsure whether samples were moved.",
      summary: "Backup freezer alarm silenced; weekend incident not logged.",
      recommended_action: "Log the incident, confirm sample location, and restore alarm settings.",
      ai_suggestion: {
        category: "EQUIPMENT_LAB",
        severity: "MEDIUM",
        summary: "Backup freezer alarm silenced; weekend incident not logged.",
        recommended_action: "Log the incident, confirm sample location, and restore alarm settings.",
        rationale: "Equipment process gap appears contained.",
        phi_flag: false,
      },
    },
    {
      study_id: 2,
      site_id: 4,
      createdOffset: -5,
      status: "IN_PROGRESS",
      owner: "CRA",
      category: "MONITORING_FINDING",
      severity: "MEDIUM",
      phi_flag: false,
      resolution_note: null,
      description:
        "The last monitoring letter asked for certified copies of three source notes that are still not in the eTMF. Response is due this week.",
      summary: "Monitoring letter: three certified source copies still outstanding.",
      recommended_action: "Upload the certified copies and send the site response before the letter due date.",
      ai_suggestion: {
        category: "MONITORING_FINDING",
        severity: "MEDIUM",
        summary: "Monitoring letter: three certified source copies still outstanding.",
        recommended_action: "Upload the certified copies and send the site response before the letter due date.",
        rationale: "Open monitoring follow-up is a contained process gap.",
        phi_flag: false,
      },
    },
    {
      study_id: 1,
      site_id: 2,
      createdOffset: -15,
      resolvedOffset: -2,
      status: "RESOLVED",
      owner: "Site manager",
      category: "STAFFING_TRAINING",
      severity: "MEDIUM",
      phi_flag: false,
      resolution_note:
        "Coordinator completed protocol training; delegation log updated 15 Sep. No untrained staff assigned to visits.",
      description:
        "A newly hired coordinator was listed on the visit calendar before protocol-specific training and delegation were complete.",
      summary: "New coordinator scheduled before training and delegation were complete.",
      recommended_action:
        "Remove untrained staff from the calendar, complete training, and update the delegation log.",
      ai_suggestion: {
        category: "STAFFING_TRAINING",
        severity: "MEDIUM",
        summary: "New coordinator scheduled before training and delegation were complete.",
        recommended_action:
          "Remove untrained staff from the calendar, complete training, and update the delegation log.",
        rationale: "Training/delegation gaps are contained if visits have not started.",
        phi_flag: false,
      },
    },
    {
      study_id: 3,
      site_id: 6,
      createdOffset: -20,
      resolvedOffset: -6,
      status: "RESOLVED",
      owner: "Finance",
      category: "CONTRACT_BUDGET",
      severity: "LOW",
      phi_flag: false,
      resolution_note: "Invoice #4412 resubmitted with the correct visit codes; AP confirmed receipt.",
      description:
        "The last visit invoice was rejected because visit codes did not match the budget grid. No subject visits are blocked.",
      summary: "Visit invoice rejected for mismatched budget grid codes.",
      recommended_action: "Correct the visit codes and resubmit the invoice to AP.",
      ai_suggestion: {
        category: "CONTRACT_BUDGET",
        severity: "LOW",
        summary: "Visit invoice rejected for mismatched budget grid codes.",
        recommended_action: "Correct the visit codes and resubmit the invoice to AP.",
        rationale: "Administrative payment issue with no visit impact.",
        phi_flag: false,
      },
    },
    {
      study_id: 2,
      site_id: 5,
      createdOffset: -1,
      status: "OPEN",
      owner: null,
      category: "OTHER",
      severity: "LOW",
      phi_flag: false,
      resolution_note: null,
      description:
        "The copier used for certified copies is down. Staff are using the clinic copier on another floor until repair.",
      summary: "Certified-copy copier is down; staff using another floor.",
      recommended_action: "Use the clinic copier for certified copies until repair, and log the workaround.",
      ai_suggestion: null,
    },
  ];

  const issues: StoredIssue[] = rows.map((row, index) => {
    const created_at = isoDaysFromToday(row.createdOffset);
    return {
      id: index + 1,
      study_id: row.study_id,
      site_id: row.site_id,
      description: row.description,
      category: row.category,
      severity: row.severity,
      summary: row.summary,
      recommended_action: row.recommended_action,
      status: row.status,
      owner: row.owner,
      due_date: dateDaysFromToday(row.createdOffset + DUE_DAYS[row.severity]),
      resolution_note: row.resolution_note,
      ai_suggestion: row.ai_suggestion,
      phi_flag: row.phi_flag,
      created_at,
      updated_at: created_at,
      resolved_at: row.status === "RESOLVED" ? isoDaysFromToday(row.resolvedOffset ?? 0) : null,
    };
  });

  const notes: IssueNote[] = issues
    .filter((issue) => issue.status === "IN_PROGRESS")
    .map((issue, index) => ({
      id: index + 1,
      issue_id: issue.id,
      body: "Owner assigned; waiting on documentation.",
      created_at: issue.created_at,
    }));

  return {
    studies,
    sites,
    issues,
    notes,
    nextIds: { site: 7, issue: 13, note: notes.length + 1 },
  };
}
