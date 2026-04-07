# Agent Upgrade Command
**Status: implementation-ready**
---
## Problem
Existing projects on older Notion schemas can hit silent failures: the provisioner's schema-repair path only runs inside provision, and there is no standalone upgrade command for validating or repairing an already-linked workspace. Users also lack a single diagnostic command that reports whether their Notion config, README/Templates page IDs, and token environment setup are healthy before they start work.
## Goal
A single CLI command, `agent upgrade`, validates and repairs an existing project's Notion workspace without re-provisioning from scratch. It detects schema gaps, stale config, token environment issues, and missing expected structure, reports findings clearly, and applies only safe additive repairs.
## Acceptance Criteria
- [ ] `agent upgrade --check` reports the health of the existing Notion workspace without making changes
- [ ] Health checks cover schema completeness per database, required README/Templates pages, token environment state, and `_project/storage.yaml` validity
- [ ] `agent upgrade` applies safe additive repairs only: adds missing database properties/select options and restores missing README/Templates IDs in `storage.yaml` when those pages already exist
- [ ] Token environment issues are reported clearly and never fixed by silently rewriting secret values
- [ ] `agent upgrade --check` exits non-zero if any fixable or manual-action issues are found
- [ ] Output clearly distinguishes `OK`, `FIXED`, and `NEEDS MANUAL ACTION` items
- [ ] Upgrade is idempotent: running it twice on a healthy workspace produces no changes and exits zero
- [ ] If the workspace cannot be found, the command fails with a clear error message
- [ ] Unit tests cover: healthy workspace (no-op), missing properties (auto-fix), missing config page IDs (auto-fix), and missing token env var (report only)
## Out of Scope
Migrating data between schema versions; upgrading local-backend projects; modifying `DATABASE_REGISTRY`; creating missing databases or pages (that is provision, not upgrade); bulk-importing local markdown artifacts to Notion (that is a migrate/import command); rewriting `.env` or other secret files automatically
## Open Questions
All resolved. Extract schema inspection/repair into a shared upgrade module, limit auto-fixes to additive changes, and treat token env issues as diagnostics or manual action rather than secret-file mutation.
## Technical Approach
### Command behavior
Add a top-level CLI command:
- `agent upgrade --check` performs inspection only and exits with status `0` when healthy or non-zero when any issue is found
- `agent upgrade` runs inspection, prints a repair plan, asks for confirmation, then applies safe repairs
- `agent upgrade --yes` skips the interactive confirmation prompt for scripted usage
The command is only valid for `backend: notion`. For `backend: local`, return a clear error that upgrade is not applicable.
### Shared upgrade service
Extract upgrade logic from the provisioner into a reusable module such as `src/integrations/notion/upgrade.py`.
Core responsibilities:
- inspect configured Notion resources
- compare existing database properties against `DATABASE_REGISTRY`
- compare existing select options against the expected schema
- discover README/Templates pages under the configured parent page
- classify findings as `ok`, `fixable`, or `manual`
- apply only the `fixable` findings
`NotionProvisioner.provision()` should reuse this service for schema verification so provision and upgrade share one definition of workspace health.
### Safe repair boundary
`agent upgrade` may auto-apply only additive, low-risk changes:
- add missing properties to configured databases
- add missing select options to existing select properties when the property type already matches
- backfill missing `readme` and `templates` IDs into `_project/storage.yaml` when those pages already exist under the configured parent page
`agent upgrade` must not:
- create missing databases or pages
- retarget relations
- mutate or infer missing data rows
- rewrite secret values in `.env`
- perform v1-to-v2 data migration
Anything outside the safe additive boundary is reported as `NEEDS MANUAL ACTION`.
### Token environment handling
Runtime remains backward compatible with both `NOTION_API_KEY` and legacy `NOTION_API_TOKEN`, but `NOTION_API_KEY` is the canonical name presented in diagnostics and docs.
Upgrade checks should report:
- `OK` when `NOTION_API_KEY` is present
- `OK (legacy)` or `NEEDS MANUAL ACTION` when only `NOTION_API_TOKEN` is present, depending on desired strictness in CLI output
- `NEEDS MANUAL ACTION` when neither variable is present
The command should never rewrite or duplicate secret values automatically. Diagnostics should point the user to the exact variable name to add or rename.
### Storage config validation
Validate `_project/storage.yaml` for:
- `backend: notion`
- presence of `parent_page_id`
- configured database IDs for at least `backlog` and `decisions`
- optional `readme` and `templates` IDs that can be restored if missing but discoverable
If the parent page cannot be queried, fail fast with a clear error that the workspace cannot be found or the integration lacks access.
### Output model
Produce a human-readable report grouped by status:
- `OK` — no action needed
- `FIXED` — issue found and repaired during this run
- `NEEDS MANUAL ACTION` — user must intervene
Examples:
- `OK: backlog schema matches expected properties`
- `FIXED: added missing Feature Status property to Backlog`
- `NEEDS MANUAL ACTION: NOTION_API_KEY is not set`
This keeps the command useful both interactively and in CI.
### Files to change
- `src/cli/main.py` — register `upgrade`
- `src/cli/commands/upgrade.py` — implement command UX and exit codes
- `src/integrations/notion/upgrade.py` — shared inspection and repair service
- `src/integrations/notion/provisioner.py` — delegate schema verification to the shared service
- `src/core/storage/config.py` — if needed, expose helpers for updating discovered page IDs
- tests under `tests/cli/integration/` and `tests/integrations/notion/`
### Test plan
Required coverage:
- unit tests for schema inspection and repair classification
- unit tests for additive property and select-option repair
- integration tests for `agent upgrade --check` and `agent upgrade --yes`
- explicit regression test for missing `readme`/`templates` IDs in `storage.yaml`
- explicit diagnostic test for missing token environment variables
### Cost and dependency impact
No new dependencies are required. The command reuses existing Notion client capabilities and should stay well within the current free-tier operational profile because it inspects a small fixed set of databases and pages.
