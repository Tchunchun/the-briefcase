# Release v0.3.0 — 2026-03-16

## What Shipped

- Feature: `agent-artifact-api` — CLI subcommands for direct artifact CRUD (inbox, brief, decision, backlog)

## Summary

Agents can now read and write planning artifacts directly via CLI commands that route transparently to whichever backend is active (local files or Notion). This eliminates the need for sync round-trips when using the Notion backend — agents call `briefcase brief read <name>` instead of reading local files.

### CLI Artifact Commands

Four new command groups added to the `agent` CLI:

| Command | Operations | Maps to |
|---|---|---|
| `briefcase inbox` | `list`, `add` | `ArtifactStore.read_inbox()`, `append_inbox()` |
| `briefcase brief` | `list`, `read <name>`, `write <name>` | `list_briefs()`, `read_brief()`, `write_brief()` |
| `briefcase decision` | `list`, `add` | `read_decisions()`, `append_decision()` |
| `briefcase backlog` | `list [--type]`, `upsert` | `read_backlog()`, `write_backlog_row()` |

All commands:
- Output structured JSON: `{"success": true, "data": ...}` (stdout) or `{"success": false, "error": "..."}` (stderr)
- Route transparently via `_project/storage.yaml` — same command works for local and Notion
- Accept `--project-dir` to target any project directory

### Brief write supports file import

`briefcase brief write <name> --file brief.md` parses a markdown brief file and uploads it to the active backend. Also supports inline options (`--problem`, `--goal`, etc.) for agent-generated content.

### Dual-mode skill instructions

All 5 agent skills (ideation, architect, implementation, review, delivery-manager) updated with "How to Access Artifacts" section:
- **CLI commands** (primary) — works with any backend
- **File paths** (fallback) — works with local backend only

### Backend transparency

| Backend | Agent reads/writes via | Source of truth |
|---|---|---|
| `backend: local` | CLI commands OR file paths (both work) | Local markdown files |
| `backend: notion` | CLI commands only | Notion API |

## Files Changed

| Area | Files |
|---|---|
| CLI commands | `src/cli/commands/inbox.py`, `brief.py`, `decision.py`, `backlog.py` — **new** |
| CLI helpers | `src/cli/helpers.py` — **new** |
| CLI main | `src/cli/main.py` — registered 4 new command groups |
| Skills | All 5 `SKILL.md` files — added dual-mode artifact access section |

## Test Results

- **Unit + Integration**: 93 passed, 0 failures
- **E2E (live Notion)**: 11/11 passed — inbox, brief, decision, backlog CRUD + filter
- **Demo workflow**: Full Ideation → Architect review executed via CLI against live Notion

## Decisions Logged

| ID | Decision |
|---|---|
| D-017 | Dual-mode skills: CLI primary, file-path fallback |
| D-018 | No write conflict — CLI and file edits equivalent on local backend |
| D-019 | Stateless auth via env var |
| D-020 | CLI params match Notion schema; LocalBackend translates to flat markdown |

## Known Limitations

- Template read/write not exposed as CLI commands (out of scope — templates rarely change)
- No mocked unit tests for CLI commands (E2E covers the flow; commands are thin wrappers)
- `brief write --file` parses standard brief template format only

## Rollback

Revert to v0.2.0. CLI commands are additive — removing them doesn't break existing sync or file-based workflows.
