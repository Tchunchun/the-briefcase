# Release v0.4.0 — 2026-03-16

## What Shipped

- Feature: `cli-first-skill-instructions` — All 5 skill files + PLAYBOOK.md rewritten to use CLI commands for planning artifact access

## Summary

When `storage.yaml` is set to `backend: notion`, agents were still reading/writing local markdown files because the skill instructions referenced file paths directly. This release rewrites every skill's Required Workflow, Artifact Rules, and supporting sections to route all planning artifact operations through `agent` CLI commands — which transparently hit the correct backend.

### Changes

**All 5 skill files updated:**

| Skill | Key changes |
|---|---|
| Ideation | 9-step CLI-first workflow with `exploring` status + brief-link attachment; prior-art check uses CLI |
| Architect | Feature Review reads brief via `briefcase brief read`; decisions logged via `briefcase decision add` |
| Implementation | tasks.md eliminated — tasks are backlog rows (`type=Task`); all reads via CLI |
| Review | Findings written to Task `--notes`; reads brief/tasks via CLI |
| Delivery Manager | Handoff validation uses CLI reads; transition checklists reference CLI verification |

**PLAYBOOK.md updated:**
- Session Protocol, Collaboration Protocol, Workflow Phases, Handoff Sequence, Backlog Schema, Definition of Done, Shared Rules — all CLI-first
- Folder Structure annotated with "managed via CLI"

### What was eliminated

- **"File paths (local backend only)" fallback block** — removed from all 5 skills
- **tasks.md** — eliminated as a concept; tasks are backlog rows (`type=Task`) linked via `--parent-id`
- **Review Findings in tasks.md** — findings go to Task `--notes` field

### What stays file-based (by design)

- `_project/` config files — project constants, always local
- `src/` and `tests/` — code authoring
- ADRs — niche reference artifact
- Folder Structure diagram — describes local layout with CLI annotations

### Decision

- D-021: CLI-only artifact access in skills

## Rollback

Revert the 6 modified files to their pre-v0.4.0 state via git. No code changes were made — only markdown skill files were modified.

## Known Limitations

- The `briefcase backlog list --type Task` filter is done client-side (Python filter), not server-side. Works correctly but may be slow with very large backlogs.
- Brief status parsing from Notion body text can show `draft` even when the brief was written as `implementation-ready` — the backlog Feature Status is the authoritative source of truth.
