**Status: implementation-ready**
## Problem
Brief updates currently overwrite prior planning state, which makes it hard to see what changed, who changed it, and whether a scope edit should be rolled back. This is especially risky when brief refinement happens across multiple roles or through a Notion-backed workflow where update behavior has already been fragile.
## Goal
Make brief updates durable and inspectable so teams can review prior versions, understand changes over time, and safely recover from mistaken edits without losing the current planning workflow.
## Acceptance Criteria
- [ ] The system stores multiple versions of a brief instead of treating each update as a destructive overwrite.
- [ ] Users or agents can view enough history to understand what changed between brief revisions.
- [ ] The workflow defines a safe way to restore or roll back a brief to an earlier version.
- [ ] Versioning works for the supported storage backends or clearly defines backend-specific behavior where exact parity is not practical.
- [ ] Brief update commands and role guidance align with the version-control behavior so agents do not accidentally bypass it.
- [ ] The design keeps the current brief readable as the source of truth while preserving prior revisions as history rather than creating scope confusion.
## Non-Functional Requirements
- **Durability / auditability:** Each brief write creates an immutable prior revision before the head brief is updated.
- **Source of truth clarity:** The current brief page/file remains the canonical head; history is stored separately, not embedded in the body.
- **Rollback safety:** Restoring a prior revision creates a new head revision and does not mutate stored history.
- **Backend scope:** Local backend support is required; Notion support in v1 is limited to briefs created in the dedicated Briefs container page.
- **Operational cost:** No new paid service or external version store is introduced in v1.
## Out of Scope
- Full version control for every artifact type in the system.
- Replacing Git or turning backlog rows into a full document-management system.
- Real-time collaborative editing semantics.
- Broad permissions or approval workflows beyond what is needed to manage brief revisions safely.
## Open Questions
- None for v1. Revision modeling, metadata, rollback semantics, and backend scope are resolved in D-039 and the Technical Approach below.
## Technical Approach
Use append-only full snapshots rather than in-body changelogs. Keep the existing brief artifact as the head revision and add explicit revision storage plus read/list/restore operations around it.
Local backend:
- Keep  as the readable head brief.
- Before overwriting the head, write the previous full content to a revision artifact under a dedicated per-brief history location with metadata: revision id, timestamp, actor if available, and change note/summary.
- Reading the brief continues to return the head; history/list/read commands target the revision artifacts.
Notion backend:
- Support only briefs created in the dedicated  container page. Legacy root-level brief pages are explicitly out of scope for v1.
- Keep the existing brief page as the head. Store prior revisions as immutable revision artifacts attached to that brief in a backend-specific history structure, with the same metadata as local.
- Do not rely on native Notion page history for product behavior; the application-managed revision artifacts are the durable history layer.
CLI and workflow:
- Extend brief commands with explicit history operations (list/read/restore) and an optional human change summary on write.
- Rollback copies an older snapshot into a new head revision while preserving both the previous head and the selected historical revision.
- Agent guidance should continue to treat the head brief as the source of truth and use the history commands for inspection or restoration rather than editing history manually.
Diff visibility:
- v1 does not require a custom structural diff engine. History visibility is provided through revision metadata plus full snapshot retrieval, which is sufficient for users or agents to compare revisions and understand changes over time.
