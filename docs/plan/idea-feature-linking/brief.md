**Status: implementation-ready**
---
## Problem
The Idea→Feature parent relationship is inconsistently set and has no aggregation. Three specific gaps: (1) Single-Feature Ideas often skip --parent-id during Feature creation, breaking the link. Only the phase-splitting workflow in ideation SKILL.md documents parent linking — the standard single-Feature flow does not. (2) There is no way to query child Features of an Idea. You cannot ask 'show me all Features under this Idea and their statuses' without manually scanning the full backlog. (3) The delivery-manager marks Ideas as shipped without verifying all child Features are done. For 1:many Ideas (multi-phase initiatives), an Idea can be marked shipped while some Features are still in-progress — there is no partially-shipped state or aggregation check. Infrastructure exists (parent_ids list field, --parent-id on backlog upsert, Parent relation in Notion schema) but is underused.
## Goal
Ensure every Feature is linked to its parent Idea, and provide a mechanism to query and aggregate child Feature statuses so that Idea ship-readiness can be determined automatically. Support both 1:1 (single Feature) and 1:many (multi-phase) Idea→Feature relationships.
## Acceptance Criteria
- [ ] Ideation SKILL.md standard workflow (non-phase-split) requires --parent-id when creating a Feature from an Idea
- [ ] Implementation SKILL.md documents that --parent-id must be preserved when updating Feature rows
- [ ] New CLI command: briefcase backlog children <idea-id> lists all child Features with their statuses
- [ ] Children command output includes an aggregated ship-readiness summary (all done / partially done / none done)
- [ ] Delivery-manager SKILL.md requires checking child Feature statuses before marking an Idea as shipped
- [ ] Ship-routing automation includes a child-status check — blocks Idea→shipped if any child Feature is not done
- [ ] Both local and Notion backends support the children query
## Non-Functional Requirements
No new dependencies. Must work with existing Parent relation in Notion schema. Backward compatible — existing Features without parent links are not broken, just unlinkable.
## Out of Scope
Retroactive linking of existing unlinked Features to their parent Ideas. UI for visualizing the Idea→Feature tree. Partial-ship status as a new Idea lifecycle state (use notes for now). Feature→Task parent linking (already works via phase-splitting).
## Open Questions
Resolved: (1) Children query should traverse one level only (Idea→Feature). Task-level detail is implementation's concern and can be queried separately via backlog list --type Task. Keep it simple. (2) Yes, add a partial-ship note automatically. When some children are done but not all, the children command output should include a summary line like 'Ship readiness: 2/3 Features done (partially shipped)' and the ship-routing automation should append '[partial-ship] 2/3 Features done as of <date>' to the Idea notes when it blocks the shipped transition.
## Technical Approach
Four layers of changes:
**1. Skill instruction updates (3 files):**
- skills/ideation/SKILL.md: In Required Workflow step 9 (create Feature row), add --parent-id <idea-notion-id> to the backlog upsert command template. Add a note: 'The Idea notion_id is available from the backlog list output. Always set --parent-id to link the Feature back to its parent Idea.'
- skills/implementation/SKILL.md: Add a note that --parent-id must be preserved when updating Feature rows via backlog upsert.
- skills/delivery-manager/SKILL.md: Add a pre-ship check: before marking an Idea as shipped, run briefcase backlog children <idea-id> and verify all child Features are at done. If not, block the transition and note which Features are still in-progress.
**2. New CLI command (1 file):**
- src/cli/commands/backlog.py: Add a children subcommand. Input: --parent-id <notion-id>. Output: JSON list of child rows (Features with matching parent_ids) plus a summary object {total, done, in_progress, ship_ready: bool}.
**3. Backend support (2 files):**
- src/core/storage/protocol.py: Add list_children(parent_id) method to the protocol.
- src/integrations/notion/backend.py: Implement list_children — query the backlog database filtering where Parent relation contains parent_id. Return matching rows with status.
- src/core/storage/local_backend.py: Implement list_children — scan backlog entries, filter by parent_ids containing parent_id.
**4. Ship-routing automation update (1 file):**
- src/core/automation/ship_routing.py: After detecting a Feature at done, look up its parent Idea. If the Idea has other child Features not yet at done, append a partial-ship note to the Idea and do NOT mark it shipped. Only mark shipped when all children are done.
**5. Tests:**
- Unit tests for list_children on both backends.
- Unit test for the children CLI command output format.
- Unit test for ship-routing blocking partial-ship scenarios.
