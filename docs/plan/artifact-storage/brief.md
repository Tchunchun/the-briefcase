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
## Out of Scope
- Real-time bi-directional sync (v1 sync is on-demand and one-directional per run)
- Backends beyond Local and Notion in v1 (abstraction supports future backends but we don't build them now)
- Auto-generating `tasks.md` or editing `backlog.md` from Notion (agents still own these operations through the storage interface)
- Migrating historical planning docs into Notion in bulk
- Multi-user permission management within Notion workspaces
- Replacing agent roles or ownership rules defined in `skills/PLAYBOOK.md`
- Notion template marketplace or database admin UI
- Offline-first conflict resolution (v1 uses last-write-wins with explicit sync)
## Open Questions
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
