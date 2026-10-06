# Process

How Site Issue Triage work moves from a request to a verified change. Product truth stays `docs/spec.md`. The contract stays `openapi.yaml`. Skills and roles live under `.agents/`.

## Default loop

The **main session** (the human’s chat) owns the loop. It does not skip QA and it does not let SWE mark the issue done.

```
request
   ↓
PM grooms          →  .agents/agents/pm.md
   ↓                   scoped issue vs docs/spec.md
SWE implements     →  .agents/agents/swe.md
   ↓                   spec + openapi.yaml; skills in .agents/skills/
QA checks          →  .agents/agents/qa-engineer.md
   ↓
PASS → done
FAIL → back to SWE with the QA repro (same scoped issue)
```

- **PM** writes the scoped issue. Does not implement.
- **SWE** implements only what PM scoped. Does not invent routes or fields.
- **QA** runs tests and the flow (log → Analyze → save → list → resolve). Verdict is PASS or FAIL. Does not fix.
- A FAIL returns to SWE. PM is re-entered only if QA/SWE discover the spec was wrong or the ask is a non-goal.

Contract drift: run `.agents/skills/check-contract` after any path/field change, before claiming PASS.

## Parallel work

Split the backlog into **independent tracks** before launching anyone. A track is one issue whose files and spec slice do not overlap another in-flight track (example: seed copy vs list CSS). Same enum, same OpenAPI path, or the same service file = one track, serial.

When two or more tracks are in flight:

- Use **git worktrees** (or branches) so checkouts do not stomp each other.
- Split by **non-overlapping files**. Example: seed copy vs CSS is fine; two people editing `openapi.yaml` + `httpIssueService.ts` is not.
- Merge **passing** branches **one at a time**. Re-run `make test` (and `.agents/skills/check-contract` if the API moved) after each merge.

Do not parallelize a spec change to the same enum or the same OpenAPI path.

## Permissions

Destructive or production steps stay outside this loop until a human approves them. See [permissions.md](./permissions.md).
