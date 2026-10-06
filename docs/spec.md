# Site Issue Triage Assistant

**Version:** MVP  
**Audience:** Single site manager  
**Runtime:** Local application with SQLite  
**Auth:** None

## 1. Problem

Site managers currently log operational issues as free text and then reconstruct category, severity, owner, and next steps by hand. That slows intake, makes lists hard to scan, and loses the original judgment trail when a record is later edited.

This product lets a site manager describe an issue in their own words, optionally receive an AI triage suggestion, edit it, save it, and track it to resolution.

## 2. Product goal

A site manager can:

1. Pick a study and site.
2. Describe an issue in free text.
3. Optionally run **Analyze** to pre-fill triage fields.
4. Edit the form.
5. Save the issue.
6. Find it in the list.
7. Update status.
8. Resolve it with a note.

Data persists across application restarts.

## 3. Users and constraints

| Constraint | Decision |
|---|---|
| Users | Single site manager |
| Deployment | Local |
| Persistence | SQLite |
| Authentication | Out of scope |
| Patient data | Out of scope — operational site issues only |

The description field must show a hint: do not include names, dates of birth, MRNs, or contact details.

## 4. Primary flow

```
Pick study + site
        ↓
Describe issue (required)
        ↓
Analyze (optional) → pre-fills form; form stays editable
        ↓
Edit category, severity, summary, recommended action, owner, due date
        ↓
Save
        ↓
Find in list (filters + default sort)
        ↓
Open detail → edit fields, change status, append notes
        ↓
Resolve with a resolution note
```

**Analyze is optional.** Saving must still work if Analyze is skipped or if the AI call fails.

## 5. Functional requirements

### 5.1 Study and site

- Study and site are chosen from seeded lists.
- A site can be added inline from the issue form.
- Study and site are required to save an issue.

### 5.2 Log form

Required to save:

- Study
- Site
- Description
- Category
- Severity

Optional:

- Owner
- Due date

Due date behavior:

- If the user does not set a due date, default it from severity:
  - **CRITICAL** → 1 day
  - **HIGH** → 5 days
  - **MEDIUM** → 15 days
  - **LOW** → 30 days

Description hint (always visible near the field): no names, DOBs, MRNs, or contact details.

### 5.3 Analyze

Analyze sends study, site, and description to the AI and, on success, pre-fills:

- Category
- Severity
- Summary (≤ 200 characters)
- Recommended action
- One-line rationale

Rules:

- The form remains fully editable after Analyze.
- AI failure never blocks save.
- On invalid or failed AI output, show **suggestion unavailable** and leave fields as they were.

### 5.4 List view

Each row shows:

- Severity chip
- Site
- Summary
- Status
- Owner
- Due date
- Age

Default sort: severity (highest first), then oldest first.

Filters:

- Study
- Site
- Status
- Severity

**RESOLVED** issues are hidden by default. The user can include them via the status filter.

### 5.5 Detail view

From detail, the user can:

- Edit any issue field
- Change status
- Append notes

Status may move in any order among `OPEN`, `IN_PROGRESS`, `ESCALATED`, and `RESOLVED`.

Moving to **RESOLVED** requires a resolution note. Set `resolved_at` when the issue first becomes `RESOLVED`.

### 5.6 AI vs. final values

Persist both:

- The original AI suggestion (JSON)
- The values the user saved

Mark which fields the user edited relative to the original suggestion.

If Analyze was never run or failed, store no suggestion (or an empty/unavailable payload). Edited-field marks apply only when a suggestion exists.

### 5.7 CSV export

Export the **currently filtered** list as CSV.

## 6. Vocabularies

### 6.1 Category

| Value | Meaning (operational) |
|---|---|
| `PROTOCOL_DEVIATION` | Protocol not followed as written |
| `SAFETY_REPORTING` | Safety event reporting process gap |
| `CONSENT` | Informed consent process or documentation |
| `REGULATORY_IRB` | IRB / regulatory submission or approval |
| `ENROLLMENT` | Screening, eligibility, or enrollment operations |
| `IP_MANAGEMENT` | Investigational product handling, storage, accountability |
| `DATA_QUALITY` | Source, CRF, query, or data completeness |
| `STAFFING_TRAINING` | Staffing, delegation, or training |
| `MONITORING_FINDING` | Monitoring visit finding follow-up |
| `EQUIPMENT_LAB` | Equipment, lab, or sample handling operations |
| `CONTRACT_BUDGET` | Contract, budget, or payment operations |
| `OTHER` | Does not fit the above |

### 6.2 Severity

Severity is **impact**, not urgency.

| Value | Definition | Default due |
|---|---|---|
| `CRITICAL` | Subject safety or rights at risk, or a regulatory deadline missed | 1 day |
| `HIGH` | Threatens data, IP, or compliance if not fixed soon | 5 days |
| `MEDIUM` | Contained process gap | 15 days |
| `LOW` | Administrative | 30 days |

### 6.3 Status

Allowed values: `OPEN`, `IN_PROGRESS`, `ESCALATED`, `RESOLVED`.

Any transition is allowed. `RESOLVED` always requires a resolution note.

## 7. AI contract

### Input

| Field | Required |
|---|---|
| `study` | yes |
| `site` | yes |
| `description` | yes |

### Output (JSON)

| Field | Rules |
|---|---|
| `category` | One of the category vocabulary values |
| `severity` | One of `CRITICAL`, `HIGH`, `MEDIUM`, `LOW` |
| `summary` | ≤ 200 characters |
| `recommended_action` | Operational next steps only |
| `rationale` | One line |
| `phi_flag` | Boolean; true if the description appears to contain identifiers |

### Guardrails

The model must produce **operational next steps only**. It must not give:

- Clinical advice
- Causality assessment
- Dosing or treatment guidance

### Server-side validation

Reject the suggestion if:

- JSON is missing or malformed
- `category` or `severity` is not in vocabulary
- `summary` exceeds 200 characters
- Required output fields are missing

On rejection or transport failure, show **suggestion unavailable**. Do not block save.

Store a valid suggestion as `ai_suggestion` JSON and set `phi_flag` from the suggestion (user can still save).

## 8. Data model

### `studies`

Seeded. At minimum: `id`, display name / code as needed by the UI.

### `sites`

Seeded, with inline create from the issue form. At minimum: `id`, `study_id` (if sites are study-scoped), display name / code.

### `issues`

| Column | Notes |
|---|---|
| `id` | Primary key |
| `study_id` | FK |
| `site_id` | FK |
| `description` | Original free text; required |
| `category` | Vocabulary; required on save |
| `severity` | Vocabulary; required on save |
| `summary` | User-facing short text |
| `recommended_action` | User-facing next step |
| `status` | Default `OPEN` |
| `owner` | Optional |
| `due_date` | Optional; defaulted from severity if unset |
| `resolution_note` | Required when status is `RESOLVED` |
| `ai_suggestion` | JSON of original AI output |
| `phi_flag` | From AI or equivalent local flag |
| `created_at` | Set on insert |
| `updated_at` | Set on every save |
| `resolved_at` | Set when first resolved |

Edited-field marks may live inside `ai_suggestion` metadata or a sibling JSON column; MVP must be able to show which saved fields differ from the original suggestion.

### `issue_notes`

| Column | Notes |
|---|---|
| `id` | Primary key |
| `issue_id` | FK to `issues` |
| `body` | Note text |
| `created_at` | Set on insert |

Notes are append-only.

## 9. Success criteria

### Must-have (MVP acceptance)

- The full flow in §4 works end to end.
- Saved issues survive application restart.
- Analyze failure does not prevent save.
- List default sort and default hiding of `RESOLVED` behave as specified.
- `RESOLVED` cannot be set without a resolution note.
- CSV export matches the active list filters.

### Pilot metrics (30-issue pilot)

| Metric | Target |
|---|---|
| AI category saved unchanged | ≥ 70% |
| AI severity saved unchanged | ≥ 60% |
| Median time to log an issue | ≤ 2 minutes |

## 10. Non-goals

Out of scope for this MVP:

- Real patient / clinical data
- CTMS or EDC integration
- Authentication or multi-user access
- Email ingestion
- CAPA workflow
- Clinical decision support
- Notifications
- Duplicate detection
