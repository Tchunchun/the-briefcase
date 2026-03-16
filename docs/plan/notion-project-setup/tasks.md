# Tasks — Notion Project Setup

Feature: `notion-project-setup`
Brief: `docs/plan/notion-project-setup/brief.md`

---

## Task List

- [x] **T-017** — Replace database schemas with unified Backlog + Decisions
- [x] **T-018** — Add `update_database()` to NotionClient for self-relation PATCH
- [x] **T-019** — Rewrite provisioner for new structure (Backlog, Decisions, README, Templates page)
- [x] **T-020** — Rewrite NotionBackend for unified Backlog schema
- [x] **T-021** — Implement sync manifest and git orphan branch snapshot helpers
- [x] **T-022** — Update `agent sync local` pull logic for new schema
- [x] **T-023** — Add `agent sync notion` push command
- [x] **T-024** — Update `agent setup --backend notion` CLI (config, .gitignore, orphan branch)
- [x] **T-025** — Tests: unit + integration for all changed modules

---

## T-017 — Replace database schemas

**What:** Rewrite `src/integrations/notion/schemas.py` — remove INTAKE_SCHEMA, BRIEFS_SCHEMA, old BACKLOG_SCHEMA, TEMPLATES_SCHEMA. Replace with BACKLOG_SCHEMA (unified with Type, Idea Status, Feature Status, Task Status, Priority, Brief Link, Notes) and DECISIONS_SCHEMA (with Feature Link). Update DATABASE_REGISTRY.
**AC:** New schemas match brief's Backlog and Decisions tables. Old schemas removed. Registry has exactly 2 entries: `backlog` and `decisions`.
**Depends on:** Nothing.

## T-018 — Add `update_database()` to NotionClient

**What:** Add `update_database(database_id, properties)` method to `src/integrations/notion/client.py` using `httpx.patch("https://api.notion.com/v1/databases/{id}", ...)`. Needed for the self-relation two-step.
**AC:** Method sends PATCH request with provided properties. Returns response JSON. Existing methods unchanged.
**Depends on:** Nothing.

## T-019 — Rewrite provisioner

**What:** Rewrite `src/integrations/notion/provisioner.py`:
1. Create Backlog database (without Parent relation)
2. PATCH Backlog to add self-relation Parent property
3. Create Decisions database
4. Create README page with project structure + view setup guide
5. Create Templates page with child sub-pages (one per template file)
6. Idempotency: detect existing databases/pages by title before creating
**AC:** `provision()` creates exactly 2 databases + 2 pages + N template child pages. Re-running is safe. Returns database IDs in the result.
**Depends on:** T-017 (schemas), T-018 (update_database).

## T-020 — Rewrite NotionBackend

**What:** Rewrite `src/integrations/notion/backend.py`:
- `read_inbox` / `append_inbox` → query/write Backlog with `Type = Idea` filter
- `read_backlog` / `write_backlog_row` → unified schema with type-specific status mapping
- `write_brief` → create/update page directly under project root (not in a database)
- `read_brief` → find page by title under project root, parse content
- `list_briefs` → list child pages of project root that aren't databases/README/Templates
- `read_templates` / `write_template` → read/write child pages of Templates page
- `read_decisions` / `append_decision` → Decisions database with Feature Link
**AC:** All `ArtifactStore` protocol methods work against the new Notion structure. Existing protocol unchanged.
**Depends on:** T-017 (schemas), T-019 (provisioner creates the structure).

## T-021 — Sync manifest and git snapshot helpers

**What:** Create two new modules:
- `src/sync/manifest.py` — `read_manifest()`, `write_manifest()`, `compute_checksums()`, `detect_conflicts()`
- `src/sync/snapshots.py` — `init_orphan_branch()`, `commit_snapshot()`, `list_snapshots()`
**AC:** Manifest reads/writes `.sync-manifest.json` with timestamps, direction, artifact list, SHA-256 checksums. Snapshot helpers create/commit to `notion-sync-snapshots` orphan branch. Conflict detection compares current checksums vs manifest.
**Depends on:** Nothing (pure utility modules).

## T-022 — Update `agent sync local` pull logic

**What:** Rewrite `src/sync/to_local.py` to:
1. Read sync manifest (if exists) and compute current checksums
2. Detect conflicts (local changes since last sync) → warn
3. Pull from Notion via updated NotionBackend methods
4. Commit snapshot to orphan branch
5. Write updated sync manifest
**AC:** `agent sync local` pulls from unified Backlog, brief pages, Decisions. Orphan branch commit created. Manifest updated. Conflicts warned.
**Depends on:** T-020 (backend), T-021 (manifest + snapshots).

## T-023 — Add `agent sync notion` push command

**What:**
- Create `src/sync/to_notion.py` — reads local markdown, writes to Notion via NotionBackend
- Add `notion` subcommand to `src/cli/commands/sync.py`
**AC:** `agent sync notion` pushes local inbox, backlog, briefs, decisions to Notion. Manifest updated with direction `push`.
**Depends on:** T-020 (backend), T-021 (manifest).

## T-024 — Update `agent setup --backend notion` CLI

**What:** Update `src/cli/commands/setup.py`:
- Store only `backlog` and `decisions` DB IDs in config (not 5)
- Store `templates_page_id` and `readme_page_id` in config
- Append `docs/plan/` to `.gitignore` (if not already present)
- Create orphan branch `notion-sync-snapshots` via `snapshots.init_orphan_branch()`
**AC:** Setup provisions new structure, saves correct config, gitignore updated, orphan branch created. Local backend path unchanged.
**Depends on:** T-019 (provisioner), T-021 (snapshots).

## T-025 — Tests

**What:** Unit + integration tests for all changed modules:
- `tests/integrations/notion/unit/test_schemas.py` — schema structure validation
- `tests/integrations/notion/unit/test_client.py` — update_database mock test
- `tests/integrations/notion/integration/test_provisioner.py` — provisioner with mocked API
- `tests/integrations/notion/integration/test_backend.py` — backend CRUD with mocked API
- `tests/sync/unit/test_manifest.py` — manifest read/write/checksums/conflict detection
- `tests/sync/unit/test_snapshots.py` — orphan branch helpers (mocked git)
- `tests/sync/integration/test_to_local.py` — full pull flow
- `tests/sync/integration/test_to_notion.py` — full push flow
- `tests/cli/integration/test_setup.py` — updated setup flow
- `tests/cli/integration/test_sync.py` — sync commands
**AC:** All unit + integration tests pass. Coverage for new and changed code.
**Depends on:** All other tasks.

---

## Execution Order

```
T-017 (schemas) ─────┐
T-018 (client)  ─────┼→ T-019 (provisioner) → T-024 (setup CLI)
T-021 (manifest/snap) ┘→ T-020 (backend) ───→ T-022 (sync pull) → T-023 (sync push)
                                                                     ↓
                                                               T-025 (tests)
```

Phase 1 (foundations): T-017, T-018, T-021 — no dependencies, can be done in parallel
Phase 2 (core): T-019, T-020 — depend on Phase 1
Phase 3 (sync + CLI): T-022, T-023, T-024 — depend on Phase 2
Phase 4 (verification): T-025 — after all code is written
