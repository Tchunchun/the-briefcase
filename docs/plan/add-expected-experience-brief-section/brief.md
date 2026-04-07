**Status: draft**
**Created: 2026-03-29**

---

## Problem
The brief template and ideation SKILL reference "Expected Experience" as a concept that brief authors should capture, but `briefcase brief write` has no `--expected-experience` CLI flag and the `BRIEF_SECTIONS` schema has no "Expected Experience" entry. Brief authors either skip the field entirely or fold UX-intent content into `--acceptance-criteria` or `--non-functional-requirements`, losing the structured separation between what the user should experience and what the implementation must satisfy.

## Goal
Add `--expected-experience` as a first-class optional flag on `briefcase brief write`, backed by a new "Expected Experience" section in the brief schema, so that brief authors can capture UX intent separately from technical acceptance criteria.

## Acceptance Criteria
- [ ] `briefcase brief write my-feat --expected-experience 'Smooth onboarding in under 2 minutes'` writes an "Expected Experience" section to the brief
- [ ] `briefcase brief read my-feat` returns an `expected_experience` field in the JSON output
- [ ] The brief template (`template/brief.md`) includes an `## Expected Experience` section between Acceptance Criteria and Non-Functional Requirements
- [ ] `BRIEF_SECTIONS` in `src/core/storage/briefs.py` maps `"Expected Experience"` to `"expected_experience"`
- [ ] `render_brief_markdown` renders the new section in the correct position
- [ ] `parse_brief_sections` correctly extracts the new section from markdown
- [ ] Omitting `--expected-experience` on an update preserves any existing value (no destructive upsert)
- [ ] The `--file` path also parses `## Expected Experience` from markdown files
- [ ] Unit tests for `parse_brief_sections` cover the new section
- [ ] Integration test for `brief write` + `brief read` round-trips the new field

## Non-Functional Requirements
- **Expected load / scale:** not applicable — CLI schema change only
- **Latency / response time:** no change expected
- **Availability / reliability:** not applicable
- **Cost constraints:** none — no new dependencies
- **Compliance / data residency:** not applicable
- **Other constraints:** must not break existing briefs that lack the section

## Out of Scope
- Adding sub-flags for individual NFR items (load, latency, etc.)
- Changing the NFR section structure
- Migrating existing briefs to add the new section retroactively

## Open Questions
- Should the section appear before or after Non-Functional Requirements in the brief template? (Recommendation: between Acceptance Criteria and NFR, since it's closer to UX intent than operational constraints.)

## Technical Approach
*Owned by architect agent.*
