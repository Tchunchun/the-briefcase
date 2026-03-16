# Release v0.1.0 — 2026-03-16

## What Shipped

- Feature: `artifact-storage` — Pluggable artifact storage system with Local and Notion backends

## Summary

A storage abstraction layer that lets consumer projects choose where planning artifacts live — local markdown files (default) or Notion databases — with a consistent interface for agents and CLI commands.

### Phase 1 — Storage Abstraction & Local Backend
- `ArtifactStore` protocol defining standard CRUD operations for inbox, briefs, decisions, backlog, and templates
- `SyncableStore` protocol for cloud backends with sync-to-local capability
- `LocalBackend` implementing all operations via markdown files at canonical paths
- `_project/storage.yaml` config — records active backend, created during setup
- `get_store()` factory — returns the right backend from config
- `agent setup` CLI command with interactive backend selection (default: `local`)

### Phase 2 — Notion Backend
- `NotionClient` wrapper over `notion-client` SDK + raw HTTP for database queries
- 5 Notion databases provisioned automatically: Intake, Feature Briefs, Decisions, Backlog, Templates
- Each database has a defined property schema with types, required fields, and allowed values
- Workspace provisioning is idempotent — re-running finds existing databases
- 9 templates seeded from `template/` into Notion during setup
- `NotionBackend` implements `ArtifactStore` + `SyncableStore` — full CRUD via Notion API
- `agent setup --backend notion` — one command to provision, seed, and configure
- `agent sync local` — generates local markdown from Notion for git audit trail
- `--dry-run` flag for safe preview

### Phase 3 — Template Management
- `agent sync templates` — pulls updated templates from Notion back to `template/`
- Version comparison before overwriting (template `(vN)` markers)

## Included Tasks

| ID | Title | Status |
|---|---|---|
| T-001 | Define ArtifactStore + SyncableStore protocols | Done |
| T-002 | Implement storage config loader | Done |
| T-003 | Implement LocalBackend | Done |
| T-004 | Factory + `agent setup` CLI | Done |
| T-005 | Notion API client wrapper | Done |
| T-006 | Notion schemas + provisioner | Done |
| T-007 | NotionBackend (ArtifactStore + SyncableStore) | Done |
| T-008 | `agent setup --backend notion` CLI extension | Done |
| T-009 | `agent sync local` command + sync logic | Done |
| T-010 | `agent sync templates` command | Done |

## Test Results

- **95 passed, 10 skipped** (Notion E2E skipped without live credentials)
- Unit tests: 32 (protocol, config, local backend, schemas)
- Integration tests: 45 (factory, CLI setup, CLI sync, Notion client, provisioner, backend)
- E2E tests: 8 local + 10 Notion (live API)

## CLI Commands

```
agent setup                         # Interactive backend selection
agent setup --backend local         # Local file backend
agent setup --backend notion        # Notion backend (provisions workspace)
agent sync local                    # Notion → local markdown
agent sync local --dry-run          # Preview only
agent sync templates                # Pull Notion templates → local
```

## How to Deploy

1. Copy `skills/`, `template/`, and `src/` to the consumer project
2. Install dependencies: `pip install click pyyaml notion-client`
3. Run `agent setup` to choose backend
4. For Notion: provide API token + parent page ID when prompted

## Rollback

- For local backend: delete `_project/storage.yaml` and re-run `agent setup`
- For Notion backend: Notion databases remain in place; switch back to local via `agent setup --backend local`

## Known Limitations

- `notion-client` v3.0.0 removed `databases.query()` — we use raw HTTP POST for database queries
- `notion-client` v3.0.0 changed `databases.create()` — we use raw HTTP POST for database creation
- No real-time sync; all sync is on-demand via CLI
- No offline/conflict resolution; last-write-wins
- `pytest-mock` and `responses`/`respx` listed in tech-stack but tests use `unittest.mock` (works fine, tech-stack doc should be updated)
- Protocol does not include `delete` methods (not needed for v1)

---

## Addendum — Delivery Manager Orchestrated Mode (2026-03-16)

### What Shipped

- Feature: `delivery-manager-orchestrated-mode` — delivery-manager can operate as a single user-facing orchestrator and delegate implementation/review through existing role skills.

### Included Tasks

| ID | Title | Status |
|---|---|---|
| T-014 | Add orchestrated mode and mode toggle documentation in PLAYBOOK | Done |
| T-015 | Define delivery-manager dispatch, retry, and escalation contract | Done |
| T-016 | Update implementation/review skills for delivery-manager delegation path | Done |

### Notes

- No runtime source code changed; workflow/skill documentation update only.
- Review verdict for this feature: `accepted`.
