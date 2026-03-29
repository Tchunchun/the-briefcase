# Backlog

Cross-feature source of truth for task priority and execution status.

| ID | Type | Use Case | Feature | Title | Priority | Status | Review Verdict | Route State | Release Note Link | Project | Notes | Automation Trace | Lane |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| T-001 | Feature | Example user scenario | example-feature | Example task title | High | To Do | — | — | — | — | — | | — |

## Rules

- `ID`: unique task identifier, prefixed with `T-`
- `Type`: `Feature`, `Tech Debt`, or `Bug`
- `Use Case`: user scenario or job-to-be-done
- `Feature`: matches `docs/plan/{feature-name}`
- `Title`: **3–7 words**, action-oriented. Move longer context to `Notes`.
- `Priority`: `High`, `Medium`, or `Low`
- `Status`: `To Do`, `In Progress`, `Done`, or `Blocked`
- `Notes`: blockers, context, dependencies, or meaningful test outcomes

**Type guidance:**
- `Feature` — new user-facing capability or planned behaviour from a `brief.md`
- `Tech Debt` — internal improvement with no user-visible change (refactor, dependency upgrade, test coverage gap). Log the item in `_inbox.md` first; the ideation agent decides whether to promote it to a brief.
- `Bug` — deviation from an existing, accepted acceptance criterion

Backlog state must match reality, not intent.
