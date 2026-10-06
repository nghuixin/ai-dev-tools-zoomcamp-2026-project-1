---
name: check-contract
description: >-
  Runs the Site Issue Triage contract-check workflow against openapi.yaml,
  the HTTP client, and FastAPI routers. Use when the user invokes
  /check-contract, asks to verify the OpenAPI contract, or wants a reusable
  API drift check before changing routes.
---

# Check contract

Reusable workflow: confirm the three API surfaces still match. Do not add endpoints.

## Steps

1. Read `openapi.yaml` and list every path + method.
2. Read `frontend/src/services/httpIssueService.ts` and list every URL it calls.
3. Read `backend/app/routers/*.py` and list every `@router` path + method.
4. Search `frontend/src/pages` and `frontend/src/components` for `\bfetch\s*\(`.
5. Confirm no auth (`security: []`, no `Authorization`).
6. Report using the template below. If anything drifts, name the file and field. Do not invent a fix that adds a new route.

## Report

```
## Contract check
- OpenAPI paths:
- HTTP client paths:
- FastAPI paths:
- Drift:
- Auth:
- fetch() outside services:
- Verdict: pass | fail
```
