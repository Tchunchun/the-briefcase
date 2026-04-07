**Status: implementation-ready**
---
## Problem
The Notion brief write/read roundtrip is lossy. Three compounding issues: (1) _markdown_to_blocks strips empty lines, collapsing section separators. (2) _blocks_to_markdown loses inline formatting — bold markers (**Status: draft**) become plain text, horizontal rules (---) are not handled. (3) When a brief is re-written after a lossy read, the corruption propagates — sections can be emptied or reshaped. Surfaced during automate-idea-close where updating the brief dropped early sections (status/problem/goal/AC) while later sections survived.
## Goal
Make the Notion markdown-to-blocks-to-markdown roundtrip lossless for all brief section content. A brief read immediately after a write must return identical structured data.
## Acceptance Criteria
- [ ] _markdown_to_blocks preserves empty lines as empty paragraph blocks (section separators survive)
- [ ] _markdown_to_blocks handles horizontal rules (---) as divider blocks
- [ ] _blocks_to_markdown reconstructs bold/italic formatting from rich_text annotations
- [ ] _blocks_to_markdown handles divider blocks as ---
- [ ] A write-then-read roundtrip returns identical parse_brief_sections output for all seven brief sections
- [ ] Existing briefs are not corrupted by the fix (backward compatible read of old block formats)
## Non-Functional Requirements
No new dependencies. Must not break existing brief revision history. Notion API block limit (100 per append) must still be respected.
## Out of Scope
Full markdown fidelity (code blocks, tables, nested lists). Retroactive repair of already-corrupted briefs. Local backend changes (local roundtrip is already lossless).
## Open Questions
Resolved: Both. Add a unit test with mocked blocks for fast CI coverage, plus a tagged integration test (pytest mark: notion_integration) that does a real write-then-read roundtrip — skipped by default, run manually when touching the Notion layer.
## Technical Approach
Three files, four changes:
**1. _markdown_to_blocks (provisioner.py:520):**
- Stop skipping empty lines. Instead, emit an empty paragraph block for blank lines (preserves section separators).
- Add a check for lines matching ^\-\-\-$ — emit a divider block ({type: divider, divider: {}}).
**2. _blocks_to_markdown (backend.py:921):**
- Handle divider block type — emit '---'.
- For rich_text items, check annotations.bold and annotations.italic. Wrap text in ** or * accordingly. Currently only uses plain_text which strips formatting.
- Emit an empty line for empty paragraph blocks (paragraph with no rich_text or empty string).
**3. write_brief merge safety (backend.py:210):**
- After reading current brief state (line 218), merge the incoming data dict on top of the read data so that unspecified fields retain their current values rather than defaulting to empty. This prevents partial writes from blanking sections even if the roundtrip is lossy.
**4. Tests (new file: tests/integrations/notion/unit/test_roundtrip.py):**
- Unit test: render a full brief → _markdown_to_blocks → _blocks_to_markdown → parse_brief_sections. Assert all seven sections match.
- Unit test: empty paragraph blocks survive roundtrip.
- Unit test: bold status line survives roundtrip.
- Integration test (marked notion_integration): write_brief then read_brief, assert structured data match.
