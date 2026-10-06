from __future__ import annotations

import re

from app.errors import StoreError
from app.models import CATEGORY_LABELS, AiSuggestion, AnalyzeRequest, Category, Severity

CATEGORY_RULES: list[tuple[Category, re.Pattern[str]]] = [
    (Category.SAFETY_REPORTING, re.compile(r"\b(sae|susar|serious adverse|safety report|expedited|24-hour|reporting clock)\b", re.I)),
    (Category.CONSENT, re.compile(r"\b(consent|icf|re-?consent|informed consent|wrong version)\b", re.I)),
    (Category.IP_MANAGEMENT, re.compile(r"\b(investigational product|\bip\b|accountability|temperature excursion|drug kit|pharmacy)\b", re.I)),
    (Category.REGULATORY_IRB, re.compile(r"\b(irb|iec|continuing review|regulatory packet|ethics committee)\b", re.I)),
    (Category.ENROLLMENT, re.compile(r"\b(enroll|screening log|eligibility|randomiz|recruit)\b", re.I)),
    (Category.DATA_QUALITY, re.compile(r"\b(query|source data|crf|edc|data cut|missing pages)\b", re.I)),
    (Category.STAFFING_TRAINING, re.compile(r"\b(training|delegation|staffing|untrained|gcp)\b", re.I)),
    (Category.MONITORING_FINDING, re.compile(r"\b(monitor|monitoring visit|cra finding|follow-up letter)\b", re.I)),
    (Category.EQUIPMENT_LAB, re.compile(r"\b(centrifuge|freezer|lab kit|sample|equipment|calibration)\b", re.I)),
    (Category.CONTRACT_BUDGET, re.compile(r"\b(invoice|budget|cta|contract|payment)\b", re.I)),
    (Category.PROTOCOL_DEVIATION, re.compile(r"\b(protocol|deviation|visit window|out of window|inclusion|exclusion)\b", re.I)),
]

ACTIONS = {
    Category.PROTOCOL_DEVIATION: "Document the deviation, notify the PI, and file per the site deviation SOP. Confirm whether a protocol exception or sponsor notice is required.",
    Category.SAFETY_REPORTING: "Complete the outstanding safety notification, document the clock, and confirm sponsor/IRB reporting is caught up. Do not assess causality or treatment.",
    Category.CONSENT: "Quarantine the incorrect form, reconsent with the current IRB-approved version if required, and file a note-to-file.",
    Category.REGULATORY_IRB: "Assemble the missing packet, submit to the IRB/IEC, and track acknowledgement before the next subject visit that depends on it.",
    Category.ENROLLMENT: "Pause affected screening if eligibility is uncertain, correct the log, and confirm the next eligible slot with the PI.",
    Category.IP_MANAGEMENT: "Quarantine affected kits if needed, document accountability/temperature, and notify pharmacy and the sponsor per the pharmacy manual.",
    Category.DATA_QUALITY: "List the missing or inconsistent data, assign an owner, and close queries before the next data cut.",
    Category.STAFFING_TRAINING: "Stop untrained staff from delegated tasks, complete training/delegation updates, and file certificates before the next visit.",
    Category.MONITORING_FINDING: "Draft the site response, attach evidence of correction, and send it by the letter due date.",
    Category.EQUIPMENT_LAB: "Take the equipment out of use if out of calibration, move samples to a qualified unit, and log the incident.",
    Category.CONTRACT_BUDGET: "Route the invoice or amendment to the budget owner and confirm the next payment milestone.",
    Category.OTHER: "Confirm the operational owner, write the next concrete site action, and set a follow-up date.",
}

PHI_PATTERNS = [
    re.compile(r"\b[\w.+-]+@[\w.-]+\.\w+\b"),
    re.compile(r"\b(\+?\d{1,2}[\s.-]?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}\b"),
    re.compile(r"\b(mrn|medical record( number)?)\s*[:#]?\s*\d+", re.I),
    re.compile(r"\b(dob|date of birth)\b", re.I),
    re.compile(r"\b\d{1,2}[\/.-]\d{1,2}[\/.-]\d{2,4}\b"),
    re.compile(r"\b(ssn|social security)\b", re.I),
    re.compile(r"\b(patient|subject)\s+[A-Z][a-z]+(\s+[A-Z][a-z]+)?\b"),
]


def detect_phi(text: str) -> bool:
    return any(pattern.search(text or "") for pattern in PHI_PATTERNS)


def _pick_category(description: str) -> Category:
    for category, pattern in CATEGORY_RULES:
        if pattern.search(description):
            return category
    return Category.OTHER


def _pick_severity(description: str, category: Category) -> Severity:
    if re.search(r"\b(safety|rights at risk|missed (the )?deadline|24-hour|not sent|subject at risk)\b", description, re.I):
        return Severity.CRITICAL
    if category == Category.SAFETY_REPORTING and re.search(r"\b(missed|late|clock)\b", description, re.I):
        return Severity.CRITICAL
    if re.search(r"\b(excursion|data integrity|compliance|wrong consent|unblinding|accountability)\b", description, re.I):
        return Severity.HIGH
    if category in {Category.IP_MANAGEMENT, Category.CONSENT, Category.REGULATORY_IRB}:
        return Severity.HIGH
    if re.search(r"\b(filing|admin|invoice|copy|binder)\b", description, re.I) or category == Category.CONTRACT_BUDGET:
        return Severity.LOW
    return Severity.MEDIUM


def validate_suggestion(raw: AiSuggestion | None) -> AiSuggestion | None:
    if raw is None:
        return None
    if not raw.summary.strip() or len(raw.summary) > 200:
        return None
    if not raw.recommended_action.strip() or not raw.rationale.strip():
        return None
    return raw


def heuristic_analyze(payload: AnalyzeRequest) -> AiSuggestion:
    study = payload.study.strip()
    site = payload.site.strip()
    description = payload.description.strip()
    if not study or not site or not description:
        raise StoreError("study, site, and description are required")
    category = _pick_category(description)
    severity = _pick_severity(description, category)
    first = re.split(r"(?<=[.!?])\s", re.sub(r"\s+", " ", description).strip())[0]
    prefix = f"{CATEGORY_LABELS[category]} · {site}"
    summary = f"{prefix}: {first}"[:200]
    suggestion = AiSuggestion(
        category=category,
        severity=severity,
        summary=summary,
        recommended_action=ACTIONS[category],
        rationale=f"{severity.value} impact based on operational cues in the description ({CATEGORY_LABELS[category].lower()}).",
        phi_flag=detect_phi(description),
    )
    if validate_suggestion(suggestion) is None:
        raise StoreError("suggestion unavailable", 422)
    return suggestion
