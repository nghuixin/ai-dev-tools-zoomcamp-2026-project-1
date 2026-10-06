from datetime import date, datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class Category(str, Enum):
    PROTOCOL_DEVIATION = "PROTOCOL_DEVIATION"
    SAFETY_REPORTING = "SAFETY_REPORTING"
    CONSENT = "CONSENT"
    REGULATORY_IRB = "REGULATORY_IRB"
    ENROLLMENT = "ENROLLMENT"
    IP_MANAGEMENT = "IP_MANAGEMENT"
    DATA_QUALITY = "DATA_QUALITY"
    STAFFING_TRAINING = "STAFFING_TRAINING"
    MONITORING_FINDING = "MONITORING_FINDING"
    EQUIPMENT_LAB = "EQUIPMENT_LAB"
    CONTRACT_BUDGET = "CONTRACT_BUDGET"
    OTHER = "OTHER"


class Severity(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class Status(str, Enum):
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    ESCALATED = "ESCALATED"
    RESOLVED = "RESOLVED"


DUE_DAYS = {
    Severity.CRITICAL: 1,
    Severity.HIGH: 5,
    Severity.MEDIUM: 15,
    Severity.LOW: 30,
}

CATEGORY_LABELS = {
    Category.PROTOCOL_DEVIATION: "Protocol deviation",
    Category.SAFETY_REPORTING: "Safety reporting",
    Category.CONSENT: "Consent",
    Category.REGULATORY_IRB: "Regulatory / IRB",
    Category.ENROLLMENT: "Enrollment",
    Category.IP_MANAGEMENT: "IP management",
    Category.DATA_QUALITY: "Data quality",
    Category.STAFFING_TRAINING: "Staffing / training",
    Category.MONITORING_FINDING: "Monitoring finding",
    Category.EQUIPMENT_LAB: "Equipment / lab",
    Category.CONTRACT_BUDGET: "Contract / budget",
    Category.OTHER: "Other",
}

EDIT_COMPARE_FIELDS = ("category", "severity", "summary", "recommended_action")


class Study(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: int
    code: str
    name: str


class Site(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: int
    study_id: int
    code: str
    name: str


class CreateSiteRequest(BaseModel):
    study_id: int
    name: str
    code: Optional[str] = None


class AnalyzeRequest(BaseModel):
    study: str
    site: str
    description: str


class AiSuggestion(BaseModel):
    category: Category
    severity: Severity
    summary: str = Field(max_length=200)
    recommended_action: str
    rationale: str
    phi_flag: bool


class IssueNote(BaseModel):
    id: int
    issue_id: int
    body: str
    created_at: datetime


class Issue(BaseModel):
    id: int
    study_id: int
    site_id: int
    study: Study
    site: Site
    description: str
    category: Category
    severity: Severity
    summary: str
    recommended_action: str
    status: Status
    owner: Optional[str] = None
    due_date: Optional[date] = None
    resolution_note: Optional[str] = None
    ai_suggestion: Optional[AiSuggestion] = None
    edited_fields: list[str]
    phi_flag: bool
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime] = None
    age_days: int
    overdue: bool
    notes: Optional[list[IssueNote]] = None


class CreateIssueRequest(BaseModel):
    study_id: int
    site_id: int
    description: str
    category: Category
    severity: Severity
    summary: str = ""
    recommended_action: str = ""
    owner: Optional[str] = None
    due_date: Optional[date] = None
    ai_suggestion: Optional[AiSuggestion] = None
    phi_flag: Optional[bool] = None


class UpdateIssueRequest(BaseModel):
    study_id: Optional[int] = None
    site_id: Optional[int] = None
    description: Optional[str] = None
    category: Optional[Category] = None
    severity: Optional[Severity] = None
    summary: Optional[str] = None
    recommended_action: Optional[str] = None
    status: Optional[Status] = None
    owner: Optional[str] = None
    due_date: Optional[date] = None
    resolution_note: Optional[str] = None
    phi_flag: Optional[bool] = None


class CreateNoteRequest(BaseModel):
    body: str
