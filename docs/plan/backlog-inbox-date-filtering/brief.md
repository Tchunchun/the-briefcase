**Status: implementation-ready**
---
## Problem
The briefcase inbox list and briefcase backlog list commands return no timestamp information. Notion pages natively store created_time and last_edited_time, but read_inbox and read_backlog discard them. Users and agents cannot distinguish today's work from yesterday's, making daily progress tracking impossible.
## Goal
Surface created_at and updated_at timestamps in inbox and backlog list output, add date-based filtering (--since, --today), and provide date-grouped visual output so users can quickly see what changed today.
## Acceptance Criteria
- [ ] briefcase inbox list output includes created_at and updated_at ISO-8601 fields for each item (Notion backend)
- [ ] briefcase backlog list output includes created_at and updated_at ISO-8601 fields for each item (Notion backend)
- [ ] Local backend surfaces comparable timestamps (file mtime or explicit field)
- [ ] --since YYYY-MM-DD flag on inbox list and backlog list returns only items created or modified on/after that date
- [ ] --today flag on inbox list and backlog list is shorthand for --since today
- [ ] Date-grouped output mode groups items under date headers (newest first) when --group-by-date flag is passed
- [ ] Storage protocol (protocol.py) updated with optional timestamp and filter parameters
- [ ] Existing tests pass; new tests cover timestamp surfacing and filtering for both backends
- [ ] CLI help text documents new flags
## Non-Functional Requirements
Expected load: small dataset (under 500 rows). Latency: no perceptible increase for list commands. No new dependencies required. Backward-compatible: existing JSON output shape adds fields but does not remove any.
## Out of Scope
Brief list timestamps (separate idea: Briefs page reverse-chronological). Notion database schema changes (timestamps are native). Sort-by-date without grouping. Pagination. Full-text search.
## Open Questions
Q1 RESOLVED (D-035): Local backend uses file mtime for updated_at, optional YAML frontmatter created_at (fallback ctime). Q2 RESOLVED (D-035): --since filters on updated_at (last modified) by default. Q3 RESOLVED (D-035): --group-by-date requires explicit flag; default output stays flat JSON.
## Technical Approach
### Layer 1: Storage Protocol
Add optional `since: str | None` parameter to `read_inbox()` and `read_backlog()` in protocol.py. Both backends return `created_at` and `updated_at` ISO-8601 strings per item. When `since` is provided, backends filter to items where `updated_at >= since`.
### Layer 2: Notion Backend
In `backend.py` `read_inbox()` and `read_backlog()`: extract `r['created_time']` and `r['last_edited_time']` from each Notion page result. Map to `created_at` and `updated_at` keys in the returned dict. When `since` is set, add a Notion API filter: `{'timestamp': 'last_edited_time', 'last_edited_time': {'on_or_after': since}}`. This is server-side filtering -- no extra API calls.
### Layer 3: Local Backend
In `local_backend.py`: derive `updated_at` from file mtime via `os.path.getmtime()`. Parse optional `created_at` YAML frontmatter field; fall back to file ctime if absent. When `since` is set, filter in Python after reading.
### Layer 4: CLI Commands
In `commands/inbox.py` and `commands/backlog.py`: add Click options `--since` (date string) and `--today` (boolean flag). `--today` sets `since` to today's date. Add `--group-by-date` flag. When `--group-by-date` is set, post-process the list to group items by date header (newest first). Default output remains flat JSON with the new timestamp fields appended.
### Layer 5: Artifact Service
Pass `since` parameter through `list_inbox()` and `list_backlog()` in artifact_service.py.
### Decision Reference
See D-035: Timestamp surfacing approach.
