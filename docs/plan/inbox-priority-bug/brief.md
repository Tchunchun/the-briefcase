**Status: implementation-ready**
---
## Problem
briefcase inbox add has no --priority option. When agents or users want to set priority on an inbox item, they embed it in --notes text instead. The Notion backlog row is created with no Priority property set, so all inbox items appear unprioritized. The backlog upsert command supports --priority, but inbox add does not pass it through.
## Goal
Add a --priority option to briefcase inbox add that sets the Priority property on the created backlog row. Default to Medium (matching backlog upsert behavior).
## Acceptance Criteria
- [ ] briefcase inbox add accepts --priority High|Medium|Low option
- [ ] Priority value is set on the Notion backlog row (or local backlog entry) when the item is created
- [ ] Default priority is Medium when --priority is omitted
- [ ] Existing inbox add calls without --priority continue to work (backward compatible)
- [ ] Both local and Notion backends handle the priority field correctly
## Non-Functional Requirements
No new dependencies. Backward compatible — omitting --priority defaults to Medium.
## Out of Scope
Auto-classification of priority based on content. Bulk priority updates for existing items. Priority on non-Idea types.
## Open Questions
Resolved: Pass priority through append_inbox (not backlog upsert). The Notion backend already handles entry.get('priority') at backend.py:175-176 — it just never receives the value because the CLI doesn't pass it. Keep append_inbox as the single write path for inbox items.
## Technical Approach
Three changes across two layers: (1) CLI layer — src/cli/commands/inbox.py: add --priority option to inbox_add (Click choice: High/Medium/Low, default Medium), include priority in the entry dict passed to store.append_inbox(). (2) Protocol layer — src/core/storage/protocol.py: update append_inbox docstring to document the optional priority field. (3) Local backend — src/core/storage/local_backend.py: update append_inbox to include priority in the markdown line format (e.g. [idea/High]). The Notion backend already handles priority — no changes needed there. Tests: add test cases in tests/ for inbox add with and without --priority on both backends.
