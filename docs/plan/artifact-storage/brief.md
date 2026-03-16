# Artifact Storage (v2)

**Status: implementation-ready**

---

## Problem

The 0-to-1 agent workflow produces planning artifacts (inbox entries, briefs, decisions, backlogs, templates) that today exist only as local markdown files in git. This works for solo developers but creates friction for teams and non-technical operators who prefer cloud-based tools like Notion for day-to-day planning. There is no standard way to choose where artifacts live at project setup, no abstraction that lets agents read/write artifacts regardless of backend, and no automated provisioning of external workspaces. Each project ends up with an ad-hoc, inconsistent setup.

## Goal

Provide a pluggable artifact storage system that lets users choose their planning backend at project setup — local files (default), Notion, or future backends — with a consistent interface for agents and CLI commands. When Notion is chosen, the system provisions a structured workspace, seeds it with templates from the git repo, and makes Notion the primary working surface for planning artifacts.

## Acceptance Criteria

### Phase 1 — Storage Abstraction & Local Backend

- [ ] A storage interface defines standard operations for planning artifacts: read, write, list, and sync for each artifact type (inbox entries, briefs, decisions, backlog rows, templates)
- [ ] The local-file backend implements this interface using the existing markdown file conventions (`docs/plan/`, `_project/`, `template/`)
- [ ] A `_project/storage.yaml` (or equivalent) config file records which backend is active, created during project setup
- [ ] Agents read/write artifacts through the storage interface, not by directly accessing file paths — so backend changes don't require agent logic changes
- [ ] The existing agent workflow (ideation → architect → implementation → review) works identically with the local backend as it does today
- [ ] `agent setup` CLI command includes a backend selection step (default: `local`)

### Phase 2 — Notion Backend

- [ ] `agent setup --backend notion` provisions a full Notion workspace for the project
- [ ] Setup requires only a Notion API token and parent page ID — no manual Notion configuration
- [ ] The provisioned workspace includes databases for: Intake, Feature Briefs, Decisions, Backlog, Templates
- [ ] Templates from `template/` are seeded into the Notion Templates database during setup (brief, tasks, backlog, inbox, adr, release-notes, tech-stack, testing-strategy, definition-of-done)
- [ ] Each database has a defined property schema (types, required fields, allowed values)
- [ ] Setup is idempotent — re-running does not duplicate databases or pages
- [ ] Setup outputs a confirmation summary and fails loudly on API errors
- [ ] Setup stores Notion database IDs in `_project/storage.yaml` so subsequent commands auto-discover the right databases
- [ ] When Notion is the active backend, Notion is the source of truth for planning artifacts — agents and CLI commands read from and write to Notion
- [ ] On-demand sync generates local markdown files from Notion for git audit trail (`agent sync local`)
- [ ] Sync uses stable dedup keys (Notion page IDs) so repeated runs never duplicate local entries
- [ ] Sync commands provide summary output (fetched, created, skipped, failed) and fail loudly on errors
- [ ] Per-project isolation — each project gets its own Notion page tree, no shared databases across projects

### Phase 3 — Template Management in Notion

- [ ] Non-technical users can edit templates directly in Notion
- [ ] When a new artifact is created (e.g., new brief), the agent uses the Notion template as the starting point
- [ ] Template changes in Notion do not retroactively alter existing artifacts
- [ ] A CLI command (`agent sync templates`) can pull updated templates from Notion back to local `template/` files for git versioning

## Non-Functional Requirements

- **Expected load / scale:** Single user or small team, low volume; on-demand sync; one setup run per project
- **Latency / response time:** Setup under 15 seconds; sync under 10 seconds for tens of records
- **Availability / reliability:** Best-effort sync with explicit failures; no silent drops; idempotent
- **Cost constraints:** No new paid services beyond existing Notion API (free tier); abstraction layer must not require a paid database or SaaS
- **Compliance / data residency:** API tokens stored locally, never committed to git; consumer projects may store credentials via their own secrets management
- **Extensibility:** Adding a new backend (e.g., Airtable, Supabase, GitHub Projects) should require implementing the storage interface only — no changes to agent skills, PLAYBOOK.md, or CLI command structure
- **Backward compatibility:** Projects using local backend must work exactly as today with zero migration

## Out of Scope

- Real-time bi-directional sync (v1 sync is on-demand and one-directional per run)
- Backends beyond Local and Notion in v1 (abstraction supports future backends but we don't build them now)
- Auto-generating `tasks.md` or editing `backlog.md` from Notion (agents still own these operations through the storage interface)
- Migrating historical planning docs into Notion in bulk
- Multi-user permission management within Notion workspaces
- Replacing agent roles or ownership rules defined in `skills/PLAYBOOK.md`
- Notion template marketplace or database admin UI
- Offline-first conflict resolution (v1 uses last-write-wins with explicit sync)

## Open Questions — Resolved

- **OQ-1 → D-005:** Python `typing.Protocol` class. Each artifact type (inbox, brief, decision, backlog, template) gets a method set on the protocol. Operations: `read(id)`, `write(id, data)`, `list(filters)`, `delete(id)`. Sync is a separate concern — `sync_to_local()` is a method on cloud backends only. See Technical Approach for full contract.
- **OQ-2:** See Notion Database Schemas in Technical Approach below. Each database has required properties, types, and allowed values defined.
- **OQ-3:** The storage interface does NOT enforce ownership rules. Ownership is the agent's responsibility (enforced by PLAYBOOK.md and each SKILL.md). The interface is a dumb pipe — agents decide who can call what.
- **OQ-4:** Sync from Notion to local uses **append-only for inbox/decisions** (existing entries are never overwritten) and **overwrite for briefs/templates** (Notion is source of truth, local is a generated snapshot). Add `--dry-run` flag for safe preview. No `--force` needed in v1.
- **OQ-5:** Notion API client lives at `src/integrations/notion/` per AGENTS.md structure. The storage interface lives at `src/core/storage/`. The Notion backend imports from `src/integrations/notion/` and implements the protocol from `src/core/storage/`.
- **OQ-6 → D-004:** `_project/storage.yaml` stores: backend type, backend-specific IDs (Notion database IDs), and a human-readable reference URL. Credentials (API token) are stored in `.env` or environment variables, never in `storage.yaml`.
- **OQ-7:** Agents call the Notion API directly via the storage interface (no local cache/proxy in v1). Consistency over latency — Notion is the source of truth. If latency becomes a problem, a read-through cache can be added later without changing the interface contract.
- **OQ-8:** Template seeding records the template version (from the `(vN)` marker in each template file) in the Notion page properties. `agent sync templates` compares local version vs. Notion version and prompts before overwriting. No auto-re-seed.

## Technical Approach

*Resolved by architect agent — 2026-03-16*

### Architecture Overview

```
┌─────────────────────────────────────────────┐
│              Agent / CLI Command             │
│  (ideation, architect, implementation, etc.) │
└──────────────────┬──────────────────────────┘
                   │ calls
                   ▼
┌─────────────────────────────────────────────┐
│          ArtifactStore (Protocol)            │
│  read() · write() · list() · delete()       │
│  + sync_to_local() (cloud backends only)    │
└──────┬──────────────────────┬───────────────┘
       │                      │
       ▼                      ▼
┌──────────────┐   ┌──────────────────────┐
│ LocalBackend │   │   NotionBackend      │
│ (markdown)   │   │ (notion-client SDK)  │
└──────────────┘   └──────────────────────┘
       │                      │
       ▼                      ▼
  docs/plan/             Notion API
  _project/              (databases)
  template/
```

### Storage Interface Contract

```python
from typing import Protocol, Any

class ArtifactStore(Protocol):
    """Protocol for pluggable artifact storage backends."""

    def read_inbox(self) -> list[dict]:
        """Return all inbox entries."""
        ...

    def append_inbox(self, entry: dict) -> None:
        """Append a single entry to the inbox."""
        ...

    def read_brief(self, brief_name: str) -> dict:
        """Return structured brief data for a given brief."""
        ...

    def write_brief(self, brief_name: str, data: dict) -> None:
        """Create or update a brief."""
        ...

    def list_briefs(self) -> list[dict]:
        """Return summaries of all briefs."""
        ...

    def read_decisions(self) -> list[dict]:
        """Return all decision log entries."""
        ...

    def append_decision(self, entry: dict) -> None:
        """Append a decision to the log."""
        ...

    def read_backlog(self) -> list[dict]:
        """Return all backlog rows."""
        ...

    def write_backlog_row(self, row: dict) -> None:
        """Create or update a backlog row by ID."""
        ...

    def read_templates(self) -> list[dict]:
        """Return all templates with name and version."""
        ...

    def write_template(self, name: str, content: str, version: str) -> None:
        """Create or update a template."""
        ...
```

Cloud backends additionally implement:

```python
class SyncableStore(Protocol):
    def sync_to_local(self, target_dir: str, dry_run: bool = False) -> dict:
        """Generate local markdown files from the cloud backend.
        Returns summary: {fetched, created, skipped, failed}."""
        ...
```

### Source Tree Layout

```
src/
├── core/
│   └── storage/
│       ├── __init__.py
│       ├── protocol.py          ← ArtifactStore + SyncableStore protocols
│       ├── config.py            ← Load/save _project/storage.yaml
│       ├── factory.py           ← get_store(config) → ArtifactStore
│       └── local_backend.py     ← LocalBackend (markdown files)
├── integrations/
│   └── notion/
│       ├── __init__.py
│       ├── client.py            ← Thin wrapper around notion-client SDK
│       ├── backend.py           ← NotionBackend (implements ArtifactStore + SyncableStore)
│       ├── schemas.py           ← Database property schemas + validation
│       └── provisioner.py       ← Workspace setup (create pages + databases)
├── cli/
│   ├── __init__.py
│   ├── main.py                  ← Root CLI group
│   └── commands/
│       ├── setup.py             ← `agent setup` (backend selection, provisioning)
│       └── sync.py              ← `agent sync local`, `agent sync templates`
└── sync/
    ├── __init__.py
    └── to_local.py              ← Notion → local markdown generation logic
```

### `_project/storage.yaml` Schema

```yaml
backend: notion  # or "local"
notion:
  parent_page_id: "abc123..."
  parent_page_url: "https://notion.so/..."  # human reference only
  databases:
    intake: "db-id-1"
    briefs: "db-id-2"
    decisions: "db-id-3"
    backlog: "db-id-4"
    templates: "db-id-5"
  seeded_template_versions:
    brief: "v3"
    tasks: "v2"
    backlog: "v1"
    inbox: "v1"
    adr: "v1"
    release-notes: "v1"
    tech-stack: "v2"
    testing-strategy: "v1"
    definition-of-done: "v1"
```

For `backend: local`, the `notion:` section is absent. The local backend reads files at their canonical paths (`docs/plan/`, `_project/`, `template/`) with no additional config.

### Notion Database Schemas

**Intake**
| Property | Type | Required | Allowed values |
|---|---|---|---|
| Title | title | yes | free text |
| Type | select | yes | `idea`, `bug`, `feature-request`, `tech-debt`, `question`, `other` |
| Status | select | yes | `new`, `planned`, `architect-review`, `rejected` |
| Created | created_time | auto | — |
| Brief Link | url | no | link to brief page |

**Feature Briefs**
| Property | Type | Required | Allowed values |
|---|---|---|---|
| Title | title | yes | free text |
| Brief Name | rich_text | yes | kebab-case identifier |
| Status | select | yes | `draft`, `implementation-ready` |
| Phase | select | no | `Phase 1`, `Phase 2`, `Phase 3` |
| Created | created_time | auto | — |
| Last Edited | last_edited_time | auto | — |

Body content: full brief sections (Problem, Goal, Acceptance Criteria, etc.) as Notion blocks.

**Decisions**
| Property | Type | Required | Allowed values |
|---|---|---|---|
| ID | rich_text | yes | `D-NNN` format |
| Title | title | yes | free text |
| Date | date | yes | — |
| Status | select | yes | `proposed`, `accepted`, `superseded` |
| Why | rich_text | yes | — |
| Alternatives Rejected | rich_text | no | — |
| ADR Link | url | no | link to ADR page |

**Backlog**
| Property | Type | Required | Allowed values |
|---|---|---|---|
| ID | rich_text | yes | `T-NNN` format |
| Title | title | yes | free text |
| Type | select | yes | `Feature`, `Tech Debt`, `Bug` |
| Use Case | rich_text | no | — |
| Feature | rich_text | yes | brief name (kebab-case) |
| Priority | select | yes | `High`, `Medium`, `Low` |
| Status | select | yes | `To Do`, `In Progress`, `Done`, `Blocked` |
| Notes | rich_text | no | — |

**Templates**
| Property | Type | Required | Allowed values |
|---|---|---|---|
| Name | title | yes | template file name (e.g., `brief`) |
| Version | rich_text | yes | `vN` format |
| Last Seeded | date | yes | — |

Body content: full template content as Notion blocks.

### Dependency Cost Estimates

| Dependency | License | Free tier | Cost at expected usage |
|---|---|---|---|
| `notion-client` (Python SDK) | MIT | unlimited | $0 — client library only |
| Notion API | Notion terms | Free plan: unlimited API calls, 1 integration | $0 at single-user scale |
| `click` | BSD-3 | unlimited | $0 |
| `pyyaml` | MIT | unlimited | $0 |
| `ruff` | MIT | unlimited | $0 |

All within the "no new paid services" NFR constraint.

### CLI Commands

```
agent setup                         # Interactive: choose backend (local/notion)
agent setup --backend local         # Explicit local setup
agent setup --backend notion        # Notion setup (prompts for token + page ID)

agent sync local                    # Generate local markdown from Notion (when Notion is active)
agent sync local --dry-run          # Preview what would be generated
agent sync templates                # Pull Notion templates back to local template/ files
```

### Credential Management

- Notion API token: stored in `.env` file at project root (added to `.gitignore`)
- Environment variable: `NOTION_API_TOKEN`
- CLI reads from env var first, falls back to `.env` file
- Never stored in `_project/storage.yaml` or any committed file
