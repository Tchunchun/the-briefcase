# {Feature Name} (v3)

**Status: draft** ← ideation agent sets this to `draft`; architect agent sets this to `implementation-ready`

---

## Problem
*Owned by ideation agent.*
What problem does this solve? Keep this to 1 to 3 sentences.

## Goal
*Owned by ideation agent.*
What does success look like for the user or system?

## Acceptance Criteria
*Owned by ideation agent.*
- [ ] Criterion 1
- [ ] Criterion 2

## Non-Functional Requirements
*Owned by ideation agent. Leave a field blank or write "not yet known" if genuinely unknown — the architect will flag it as an Open Question.*

- **Expected load / scale:** (e.g. ~50 req/day, single user, up to 1 000 concurrent)
- **Latency / response time:** (e.g. CLI response < 2 s, API p95 < 500 ms, or "not applicable")
- **Availability / reliability:** (e.g. best-effort, 99% uptime, graceful degradation on API failure)
- **Cost constraints:** (e.g. must stay within free tier, < $10/month, no new paid services)
- **Compliance / data residency:** (e.g. no PII stored, EU data only, internal use only)
- **Other constraints:** (e.g. must work offline, must not break existing CLI commands)

## Out of Scope
*Owned by ideation agent.*
- Item 1

## Open Questions
*Ideation agent lists unresolved questions. Architect agent resolves them before setting status to implementation-ready.*
- Question 1

## Technical Approach
*Owned by architect agent.*
Describe the chosen architecture, patterns, libraries, and any constraints from `_project/tech-stack.md` relevant to this feature. Address any NFRs that have architectural implications.

---

## Notes

- Ideation agent fills everything above Technical Approach, then flags open questions.
- During ideation handoff, the brief stays `draft` while the Feature backlog row moves to `architect-review`; these are not the same field.
- Architect agent fills Technical Approach, resolves open questions, and sets Status to `implementation-ready`.
- Implementation agent treats this entire file as read-only.
- A brief is implementation-ready only when the architect has signed off and the implementation agent can create `tasks.md` without guessing.
