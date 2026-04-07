**Status: draft**
**Created: 2026-03-29**

---

## Problem
Three consumer-reported issues with briefcase brief write: (1) Destructive upsert — fields not passed in a write are wiped to empty on both local and Notion backends. (2) Missing --expected-experience flag — consumer expected a dedicated flag but all NFR sub-items go through --non-functional-requirements with no documentation. (3) Shell escaping — zsh history expansion breaks double-quoted values containing !, $, backticks; no documentation or workaround guidance.

## Goal
Make brief write safe for partial updates (preserve untouched fields), document NFR flag usage clearly, and provide shell-escaping guidance so consumers can reliably write briefs without data loss or CLI errors.

## Acceptance Criteria
- [x] Partial brief write preserves untouched fields on local backend
- [x] Partial brief write preserves untouched fields on Notion backend
- [x] --file path preserves existing sections not in the file
- [x] parse_brief_sections omits missing sections instead of defaulting to empty
- [x] --non-functional-requirements help text mentions sub-items
- [x] PLAYBOOK.md has Shell Escaping section with single-quote and --file guidance
- [x] SKILL.md examples updated to single quotes
- [x] Regression tests for partial inline write
- [x] Regression tests for partial --file write
- [x] Unit test for parse_brief_sections omission behavior

## Non-Functional Requirements
- **Backward compatibility:** Existing briefs must not be affected. Full writes (all fields provided) must work identically.
- **Test coverage:** Regression tests for all three fix paths.

## Out of Scope
- Adding --expected-experience as a dedicated CLI flag
- Adding --stdin support to inbox/backlog/decision commands (stretch goal, not in this fix)
- Retroactive repair of already-corrupted briefs

## Open Questions
None — all resolved during implementation.

## Technical Approach
Five-layer fix:
1. parse_brief_sections (briefs.py): Changed init dict from {key: "" for ...} to {} — omits missing sections.
2. CLI inline path (brief.py): Only include keys where CLI arg is not None.
3. CLI --file path (brief.py): Inherits parse_brief_sections fix — missing sections not in file are omitted.
4. LocalBackend.write_brief (local_backend.py): Read-merge-write pattern — starts from current, overlays only keys present in data.
5. NotionBackend.write_brief (backend.py): Filters internal _-prefixed keys before merge.
Docs: Shell Escaping section in PLAYBOOK.md, single-quote examples in SKILL.md, improved --nfr help text.
