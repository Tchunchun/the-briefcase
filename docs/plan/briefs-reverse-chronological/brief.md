**Status: implementation-ready**

---

## Problem
briefcase brief list returns briefs as raw JSON. As the project grows, the user cannot quickly scan what was worked on recently. The output needs to be human-readable with date grouping, not a JSON blob.

## Goal
Make briefcase brief list return a human-readable, terminal-friendly display of all briefs grouped by date (newest first), showing brief name and status per line under date section headers.

## Acceptance Criteria
- [ ] briefcase brief list outputs human-readable text (not JSON) to the terminal
- [ ] Output is grouped by date with visual section headers (e.g. ── 2026-03-20 ──)
- [ ] Each brief line shows: name and status, left-aligned with consistent spacing
- [ ] Briefs are sorted by last-modified date, newest first
- [ ] All briefs are shown (no cap or pagination)
- [ ] Notion backend: uses page last_edited_time for sort/grouping
- [ ] Local backend: uses brief file mtime for sort/grouping

## Non-Functional Requirements
No new dependencies. Must work with both Notion and local backends.

## Out of Scope
Filtering by date range. Pagination. Changes to brief read or brief write commands. JSON output flag.

## Open Questions
All resolved: output is always human-readable, no JSON flag needed. Show all briefs grouped by date. Fields: name + status.

## Technical Approach
Single change in the CLI layer — backends already return sorted, dated brief lists.

**File: src/cli/commands/brief.py (brief_list function)**
- Replace JSON output with human-readable formatted text
- Group briefs by date (already grouped by _group_briefs_by_date)
- For each date group, print a section header: ── YYYY-MM-DD ──────────
- For each brief in the group, print: name (left-aligned) + status (right-aligned with padding)
- Use consistent column widths based on the longest brief name

No backend changes needed — the sort order and date field are already implemented correctly.
