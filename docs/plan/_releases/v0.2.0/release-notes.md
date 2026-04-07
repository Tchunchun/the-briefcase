# Release v0.2.0 — 2026-03-16

## What Shipped

- Feature: `notion-project-setup` — Redesigned Notion workspace with unified Backlog, standalone briefs, and sync version tracking
- Feature: `delivery-manager-handoffs` — Delivery-manager role with handoff packets and checklists
- Feature: `delivery-manager-orchestrated-mode` — Single-entrypoint orchestrated workflow

## Summary

The Notion workspace is restructured from 5 flat databases to a unified system that leverages Notion's relational properties and board views. Local sync now includes version tracking via git orphan branch snapshots and conflict detection.

### Notion Project Setup (notion-project-setup)

**Unified Backlog database** replaces Intake, Feature Briefs, and old Backlog:
- Three work-item types: `Idea`, `Feature`, `Task`
- Type-specific status properties: `Idea Status`, `Feature Status`, `Task Status`
- Self-relation `Parent` property linking Tasks → Features → Ideas
- `Brief Link` URL on Features pointing to standalone brief pages
- `Priority`, `Notes` columns
- Three recommended board views documented (Idea Board, Feature Board, Task Board)

**Decisions database** — streamlined with `Feature Link` URL for traceability.

**Standalone pages**:
- README page with project structure overview and view setup guide
- Templates page with child sub-pages (one per template, version-tracked)
- Brief pages created directly under project root (one per feature)

**Sync version tracking** (D-016):
- Git orphan branch `notion-sync-snapshots` — unlimited local history of every sync pull
- `.sync-manifest.json` — SHA-256 checksums, timestamps, conflict detection
- Conflict warnings when local files changed since last sync

**New command: `briefcase sync notion`** — push local markdown to Notion (reverse of `briefcase sync local`).

**Setup improvements**:
- `docs/plan/` added to `.gitignore` when Notion is backend (design artifacts stay in Notion, not GitHub)
- Orphan branch created automatically during setup
- Post-setup guidance with view creation instructions

### Delivery Manager (delivery-manager-handoffs, delivery-manager-orchestrated-mode)

See v0.1.0 release notes addendum for full details.

## Files Changed

| Area | Files |
|---|---|
| Schemas | `src/integrations/notion/schemas.py` — 5 DBs → 2 (unified Backlog + Decisions) |
| Client | `src/integrations/notion/client.py` — added `update_database()` |
| Provisioner | `src/integrations/notion/provisioner.py` — full rewrite |
| Backend | `src/integrations/notion/backend.py` — full rewrite |
| Sync (pull) | `src/sync/to_local.py` — manifest + snapshot integration |
| Sync (push) | `src/sync/to_notion.py` — **new** |
| Manifest | `src/sync/manifest.py` — **new** |
| Snapshots | `src/sync/snapshots.py` — **new** |
| CLI sync | `src/cli/commands/sync.py` — added `briefcase sync notion` |
| CLI setup | `src/cli/commands/setup.py` — gitignore, orphan branch, post-setup guide |
| Tests | Updated provisioner + backend tests; new manifest unit tests |

## Test Results

- **Unit + Integration**: 101 passed, 10 skipped, 0 failures
- **E2E (live Notion)**: 6/6 passed — provision, inbox, feature, task, decisions, idempotency

## Decisions Logged

| ID | Decision |
|---|---|
| D-010 | Unified Backlog replacing 3 databases |
| D-011 | Two-step self-relation provisioning |
| D-012 | Brief pages directly under project root |
| D-013 | Decisions → Feature as URL (not Relation) |
| D-014 | Sync-first pattern with gitignored docs/plan/ |
| D-015 | Templates as standalone page |
| D-016 | Git orphan branch + sync manifest for version tracking |

## Known Limitations

- Notion database views cannot be created via API — must be set up manually (documented in README page)
- Schema migration from v0.1.0 structure not included (fresh projects only)
- Sync is manual (`briefcase sync local` / `briefcase sync notion`) — automation via hooks is a future enhancement
- Agent Artifact API (CLI subcommands for direct artifact access) tracked as separate feature

## Rollback

Revert to `main` branch. Old provisioner created 5 databases; new provisioner creates 2 databases + 2 pages. No data migration needed since this targets fresh projects.
