# Redesign Notion Project Setup (v3)

**Status: implementation-ready**

---

## Problem

The current Notion provisioner creates five separate databases (Intake, Feature Briefs, Decisions, Backlog, Templates) that mirror the local folder structure. This flat-database approach is hard to maintain in Notion: artifacts have no relational links between them, the Intake and Backlog schemas overlap, and managing five databases adds friction for non-technical users editing in Notion. The structure doesn't leverage Notion's relational, view, and rollup capabilities.

## Goal

Provision a Notion project workspace that is simple to navigate, uses relational properties across work items, and gives users board views grouped by lifecycle status — without changing the local markdown workflow. The new structure should be the canonical Notion layout created by `agent setup --backend notion`.

## Acceptance Criteria

- [ ] A single **Backlog** database is created with three work-item types: `Idea`, `Feature`, `Task`
- [ ] Each type has its own status property: `Idea Status`, `Feature Status`, `Task Status` — only the relevant status is used per row
- [ ] `Idea Status` options: `new`, `exploring`, `promoted`, `rejected`
- [ ] `Feature Status` options: `draft`, `architect-review`, `implementation-ready`, `done`
- [ ] `Task Status` options: `to-do`, `in-progress`, `blocked`, `done`
- [ ] A self-relation property (`Parent`) links Tasks → Features and Features → Ideas within the Backlog
- [ ] Features have a `Brief Link` (URL) property pointing to the standalone brief page
- [ ] A **Decisions** database is created with an optional `Feature Link` (URL) property for traceability
- [ ] A **Templates** standalone page is created (containing template content as child pages, not a database)
- [ ] Provisioner is idempotent — re-running does not duplicate databases or pages
- [ ] The old Intake and Briefs databases are no longer provisioned (replaced by Backlog rows and standalone pages)
- [ ] `agent sync local` continues to produce valid local markdown from the new structure
- [ ] Each `agent sync local` pull creates a git commit on a local orphan branch (`notion-sync-snapshots`) for version history
- [ ] A `.sync-manifest.json` is written after each sync with timestamps, direction, artifact list, and SHA-256 checksums
- [ ] Sync detects local-vs-pulled conflicts via checksum comparison and warns instead of silently overwriting
- [ ] Three recommended Notion views are documented for user setup: Idea Board (board, grouped by Idea Status), Feature Board (board, grouped by Feature Status), Task Board (board, grouped by Task Status)

## Non-Functional Requirements

- **Expected load / scale:** Single-user CLI; < 50 API calls per setup invocation
- **Latency / response time:** Full provisioning < 30 s (depends on Notion API)
- **Availability / reliability:** Graceful degradation — if Notion API fails mid-provision, already-created resources are not duplicated on retry (idempotency preserved)
- **Cost constraints:** Must stay within Notion free tier
- **Compliance / data residency:** No PII stored; tokens in `.env` only
- **Other constraints:** Must not break existing `agent setup --backend local` path; Notion API version 2022-06-28 (current); self-relation property requires a two-step create (database first, then update with relation pointing to self)

## Out of Scope

- Programmatic creation of Notion database views (not supported by Notion API — views documented for manual setup only)
- Migration of data from old 5-database structure to new structure (separate task if needed)
- Brief page creation workflow (this brief covers provisioning only; the ideation/architect agents create brief pages during their workflow)
- Rollup properties on the Backlog (nice-to-have, not required for v1)
- Changes to the local markdown backend or the local `backlog.md` schema

## Open Questions

All resolved — see Technical Approach and `_project/decisions.md` (D-010 through D-015).

## Technical Approach

### Notion Workspace Structure

The provisioner creates this hierarchy under the user's parent page:

```
📁 Project Root Page
├── 📄 README (page — project structure overview & view setup guide)
├── 📊 Backlog (database — unified Ideas/Features/Tasks)
├── ⚖️ Decisions (database — architectural decisions with optional feature URL)
├── 📄 Templates (page — child sub-pages, one per template)
├── 📄 {brief-name} (page — one per feature, created by ideation agent)
├── 📄 {brief-name} (page — ...)
└── ...
```

Brief pages live directly under the project root — no container page — for fast access and simple URLs. The README page is provisioned with the project structure, a guide to the three recommended board views, and usage notes.

### Backlog Database Schema

Single database, three work-item types, type-specific status properties:

| Property | Type | Values / Notes |
|---|---|---|
| Title | title | Work item name |
| Type | select | `Idea`, `Feature`, `Task` |
| Idea Status | select | `new`, `exploring`, `promoted`, `rejected` |
| Feature Status | select | `draft`, `architect-review`, `implementation-ready`, `done` |
| Task Status | select | `to-do`, `in-progress`, `blocked`, `done` |
| Priority | select | `High`, `Medium`, `Low` |
| Parent | relation (self) | Links Task→Feature, Feature→Idea |
| Brief Link | url | Notion URL of the standalone brief page (Features only) |
| Notes | rich_text | Blockers, context, test outcomes |

**Self-relation provisioning** (two-step):
1. `POST /v1/databases` — create Backlog with all properties except Parent
2. `PATCH /v1/databases/{backlog_id}` — add Parent property: `{"Parent": {"relation": {"database_id": "<backlog_id>", "single_property": {}}}}`

**Recommended views** (manual setup, documented in README page):
- **Idea Board**: filter `Type = Idea`, board grouped by `Idea Status`
- **Feature Board**: filter `Type = Feature`, board grouped by `Feature Status`
- **Task Board**: filter `Type = Task`, board grouped by `Task Status`

### Decisions Database Schema

| Property | Type | Values / Notes |
|---|---|---|
| Title | title | Decision summary |
| ID | rich_text | `D-NNN` identifier |
| Date | date | Decision date |
| Status | select | `proposed`, `accepted`, `superseded` |
| Why | rich_text | Rationale |
| Alternatives Rejected | rich_text | What was considered and dropped |
| Feature Link | url | Optional — Notion URL of the related Feature row or brief page |
| ADR Link | url | Optional — link to full ADR page |

### Templates Page

A standalone page under the project root with child sub-pages (one per template file). No database — templates are reference material. Version tracked via `(vN)` in the page title. `agent sync templates` reads child pages, compares versions against local `template/*.md`, and pulls updates.

### Sync Architecture (Decision D-014)

**Pattern: Sync-first with local files as read-only cache.**

Notion is the source of truth when Notion backend is active. Local `docs/plan/` is a transient cache, not committed to git.

**Pull gesture** (`agent sync local` — exists, needs update):
- Query Backlog where `Type = Idea` → write `docs/plan/_inbox.md`
- Query Backlog where `Type = Feature` or `Task` → write `docs/plan/_shared/backlog.md`
- List brief pages under project root → write `docs/plan/{brief-name}/brief.md` per page
- Query Decisions → write `_project/decisions.md`
- List Templates child pages → write `template/{name}.md`

**Push gesture** (`agent sync notion` — **new command**):
- Read local `docs/plan/_inbox.md` → upsert Backlog rows (Type = Idea)
- Read local `docs/plan/_shared/backlog.md` → upsert Backlog rows
- Read local `docs/plan/{brief-name}/brief.md` → upsert brief pages under project root
- Read local `_project/decisions.md` → upsert Decisions rows
- This is the reverse of pull. Uses existing `NotionBackend.write_*` methods.

**`.gitignore` update**: When Notion is the backend, `agent setup --backend notion` appends `docs/plan/` to `.gitignore`. Design artifacts stay in Notion, not GitHub.

### Version Tracking (Decision D-016)

**Problem**: Notion free tier retains page history for only 7 days. Local `docs/plan/` is gitignored (not committed to main). Without version tracking, sync overwrites are permanent and there is no audit trail.

**Solution**: Git orphan branch + sync manifest.

**Git orphan branch** (`notion-sync-snapshots`):
- Created once during `agent setup --backend notion`: `git checkout --orphan notion-sync-snapshots && git rm -rf . && git commit --allow-empty -m "init sync snapshots" && git checkout -`
- On every `agent sync local` pull, before overwriting local files:
  1. `git stash` current work (if any dirty state)
  2. `git checkout notion-sync-snapshots`
  3. Copy pulled files into the worktree
  4. `git add docs/plan/ _project/decisions.md template/`
  5. `git commit -m "sync: pull from Notion {ISO timestamp}"`
  6. `git checkout -` (back to working branch)
  7. `git stash pop` (if stashed)
- Result: full git history of every sync, accessible via `git log notion-sync-snapshots`
- Branch is **never pushed** to remote — stays local, zero remote footprint
- To diff between syncs: `git diff notion-sync-snapshots~1..notion-sync-snapshots -- docs/plan/`

**Sync manifest** (`docs/plan/.sync-manifest.json`):
```json
{
  "last_sync": "2026-03-16T14:30:00Z",
  "direction": "pull",
  "backend": "notion",
  "artifacts_synced": [
    "_inbox.md",
    "_shared/backlog.md",
    "notion-project-setup/brief.md"
  ],
  "checksums": {
    "_inbox.md": "sha256:abc123...",
    "_shared/backlog.md": "sha256:def456..."
  }
}
```
- Written after every sync (pull or push)
- On next pull: compare checksums of current local files against manifest. If a local file changed since last sync (checksum mismatch) but isn't in the push queue → **warn** about potential conflict instead of silently overwriting
- `.sync-manifest.json` is gitignored (transient metadata)

**Sync automation** (three tiers):
1. **Manual**: User runs `agent sync local` / `agent sync notion` before/after sessions
2. **Orchestrated**: Delivery-manager includes sync in handoff checklists
3. **Hooks** (recommended): Claude Code hooks (`.claude/hooks/`) — pre-session pulls from Notion, post-file-write pushes to Notion

**Agent skill impact**: Zero changes to skill files for this feature. Agents read/write local files as today. Sync handles the Notion ↔ local translation transparently.

**Future path**: A direct agent-to-API interface (CLI tools or API server) is tracked as a separate backlog item (see `docs/plan/agent-artifact-api/brief.md`). That feature would let agents call `agent read-brief <name>` instead of reading files, eliminating the sync step entirely.

### Provisioner Changes

**Files modified:**
- `src/integrations/notion/schemas.py` — replace `DATABASE_REGISTRY` with new Backlog + Decisions schemas; remove Intake, Briefs, old Backlog, Templates database schemas
- `src/integrations/notion/provisioner.py` — two-step DB creation for self-relation; create README page; create Templates page with seeded child pages; update `_find_existing_databases` to match new DB titles
- `src/integrations/notion/client.py` — add `update_database()` method (PATCH /databases/{id}) for self-relation step
- `src/integrations/notion/backend.py` — rewrite `read_inbox`/`append_inbox` to query Backlog with `Type = Idea` filter; rewrite `read_backlog`/`write_backlog_row` for unified schema; update `write_brief` to create pages under project root; update `read_templates`/`write_template` for page-based templates
- `src/cli/commands/setup.py` — update to store new DB IDs in config; add `.gitignore` update for `docs/plan/`
- `src/cli/commands/sync.py` — add `agent sync notion` subcommand (local → Notion push)
- `src/sync/to_local.py` — update pull logic for new Backlog schema mapping; add git orphan branch commit step; add sync manifest write
- New: `src/sync/to_notion.py` — push logic (local → Notion)
- New: `src/sync/manifest.py` — sync manifest read/write/checksum logic
- New: `src/sync/snapshots.py` — git orphan branch commit/diff helpers

**Files unchanged:**
- `src/core/storage/protocol.py` — `ArtifactStore` interface is stable
- `src/core/storage/config.py` — config shape unchanged (databases dict maps name→ID)
- `src/core/storage/local_backend.py` — untouched
- All skill files — untouched

### Cost Estimate

All Notion API usage stays within the free tier:
- Provisioning: ~10 API calls (create DB, patch for relation, create README page, create Templates page, seed template child pages)
- Per-sync: ~5-15 API calls depending on artifact count
- No new paid dependencies. `httpx` already in use.

---

## Notes

- The current 5-database structure is defined in `src/integrations/notion/schemas.py` (`DATABASE_REGISTRY`)
- Provisioner logic is in `src/integrations/notion/provisioner.py`
- Backend CRUD is in `src/integrations/notion/backend.py`
- The Notion client uses raw `httpx` for `create_database` and `query_database` (see `src/integrations/notion/client.py`)
- Notion API does not support creating database views programmatically — three board views must be documented as a manual post-setup step
- Self-relation in Notion: set `"relation": {"database_id": "<same_db_id>", "single_property": {}}` via `PATCH /databases/{id}/properties`
