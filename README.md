# Site Issue Triage Assistant

Local MVP for a single site manager: log a free-text site issue, optionally get an editable AI triage, save it, and track it to resolution.

This repository is **AI Dev Tools Zoomcamp 2026 — Project 1**.

## Problem

Site managers log operational issues as free text and then reconstruct category, severity, owner, and next steps by hand. Intake is slow, lists are hard to scan, and the original judgment trail is lost when a record is later edited.

This project exists so a site manager can describe an issue in their own words, get an optional AI triage, edit and save it, and track it to resolution without that extra reconstruction work.

## What it does

A site manager picks a study and site, describes an operational issue, and can run **Analyze** to pre-fill category, severity, summary, recommended action, and a one-line rationale. The form stays editable. AI failure never blocks saving.

Saved issues appear in a filterable list (severity, site, summary, status, owner, due date, age). From detail, any field can be edited, status can change, and notes can be appended. Resolving an issue requires a resolution note.

Data lives in SQLite and survives restart. There is no auth, no multi-user access, and no patient data.

## Current status

Specification only. Implementation has not started.

The product spec is the source of truth:

- [`product-spec.md`](./product-spec.md)

## Flow

1. Pick study and site (seeded lists; a site can be added inline).
2. Describe the issue (required). Hint: no names, DOBs, MRNs, or contact details.
3. Optionally run **Analyze**.
4. Edit the form and save (category and severity required).
5. Find the issue in the list. `RESOLVED` is hidden by default.
6. Update status; resolve with a note.
7. Export the filtered list as CSV.

## Constraints

| | |
|---|---|
| Users | Single site manager |
| Runtime | Local app + SQLite |
| Auth | None |
| Data | Operational site issues only — not real patient data |

Analyze output is operational next steps only. No clinical advice, causality, or dosing guidance.

## Out of scope

CTMS/EDC integration, authentication, email ingestion, CAPA workflow, clinical decision support, notifications, and duplicate detection.

## Success (MVP)

- Full flow works and data survives restart.


## Learning in Public
- https://nghuixin.notion.site/Clinical-Trial-Site-Issue-Triage-Assistant-3f072266c5fb80a8b500d9331f392def

- In a 30-issue pilot: ≥70% of AI categories and ≥60% of severities saved unchanged; median log time ≤ 2 minutes.

See [`product-spec.md`](./product-spec.md) for vocabularies, the AI contract, and the data model.
