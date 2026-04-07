**Status: implementation-ready**

---

## Problem
Briefs capture acceptance criteria but miss UX intent. The review agent validates against the letter of the brief, not the user's actual intent. For solo developers who rely entirely on AI review, this means features ship 'to spec' but don't match what the user wanted — and the mismatch isn't caught until the user sees the output. Concrete example: brief list was specified as 'grouped by date with date headers' — implementation returned raw JSON with date groups, technically satisfying the criteria but not the user's intent of human-readable terminal output. The feature was implemented twice and still wasn't right.

## Goal
Close the intent gap between what the user envisions and what gets built/reviewed, so that features match user expectations on the first implementation cycle. Three independent changes: (1) Add an 'Expected Experience' section to the brief template requiring concrete before/after examples, (2) Add a pre-implementation validation step where the implementation agent restates its plan and shows a mock of expected output before coding, (3) Add an intent-check step to the review agent that compares actual behavior against the brief's Expected Experience examples.

## Acceptance Criteria
- [ ] Brief template includes a new 'Expected Experience' section between Goal and Acceptance Criteria
- [ ] The Expected Experience section requires: (a) a 'Before' example showing current behavior, (b) an 'After' example showing desired behavior, (c) for CLI features, literal terminal output examples
- [ ] Ideation SKILL.md lists Expected Experience as a required section the ideation agent must fill
- [ ] Ideation SKILL.md context completeness check includes Expected Experience as a fifth dimension
- [ ] Implementation SKILL.md includes a pre-build validation step: restate the plan in plain language and show a mock of expected output before writing code, ask user to confirm
- [ ] Review SKILL.md includes an intent-check step: run the feature and compare actual output against the Expected Experience examples in the brief
- [ ] Review agent flags a finding when actual behavior diverges from Expected Experience, even if acceptance criteria are technically met
- [ ] All three changes are independent — each can be implemented and reverted separately

## Non-Functional Requirements
No new dependencies. No changes to CLI commands or storage backends. Changes are limited to skill instruction files (SKILL.md) and the brief template. Backward compatible — existing briefs without Expected Experience sections remain valid.

## Out of Scope
Multi-model review (using different LLMs as cross-check). Automated test generation from Expected Experience examples. Changes to the brief write CLI command schema. Enforcing Expected Experience at the CLI level (this is a skill-level instruction, not a CLI validation).

## Open Questions
All resolved during architect review:
1. Pre-implementation validation: BLOCKING for features (agent must show plan + mock output and wait for user confirmation before coding). ADVISORY for bug fixes and tech debt (agent shows plan, continues unless user objects). Rationale: features carry the highest intent-fidelity risk; bug fixes have narrower scope where the fix is usually obvious.
2. Expected Experience placement: BETWEEN Goal and Acceptance Criteria. Rationale: the concrete examples inform how acceptance criteria should be interpreted — placing them first gives the implementer the "picture" before the "checklist."
3. Review intent-check: FOLD INTO existing findings as a new severity category. No separate verdict dimension. Rationale: adding a new lifecycle axis for a single check adds complexity without proportional value. A finding like "Review: [Intent-Mismatch] actual output differs from Expected Experience" is clear enough.

## Technical Approach
Three independent changes to instruction files only. No code changes. Each commit modifies a different set of files so they can be reverted independently.

**Commit 1 — Brief template: Expected Experience section**
File: template/brief.md
- Add new section '## Expected Experience' between '## Goal' and '## Acceptance Criteria'
- Section owned by ideation agent, with guidance text: show Before (current behavior) and After (desired behavior) with concrete examples
- For CLI features: include literal terminal output. For UI: describe what the user sees. For API: show request/response pairs.
- Add ownership note in the Notes section at bottom

**Commit 2 — Ideation SKILL.md: Expected Experience ownership + context check**
File: skills/ideation/SKILL.md
- Add 'Expected Experience' to the 'Brief Sections You Own' list with guidance on what to fill in
- Add fifth dimension to Context Completeness Check: 'Expected experience — concrete before/after examples of what the user will see'
- The hard gate for briefs now requires all five dimensions

**Commit 3 — Implementation SKILL.md: Pre-build validation step**
File: skills/implementation/SKILL.md
- Add step between reading the brief and creating tasks: 'Pre-Build Validation'
- Implementation agent must: (a) restate in plain language what it will build, (b) show a mock of expected output matching the brief's Expected Experience, (c) for features: STOP and ask user to confirm before proceeding, (d) for bug fixes/tech debt: show the plan and continue unless user objects
- Add this as a new section after 'Operating Principle' and before 'Required Workflow'

**Commit 4 — Review SKILL.md: Intent-check step**
File: skills/review/SKILL.md
- Add step 6.5 (after comparing against acceptance criteria, before checking dependencies): 'Intent Check — run the feature and compare actual behavior against the Expected Experience examples in the brief'
- Add to Review Checklist: 'Does the actual user experience match the Expected Experience examples in the brief?'
- Add to Finding Rules: 'Intent-Mismatch' as a finding type — raised when actual behavior diverges from Expected Experience, even if acceptance criteria are technically met. Default severity: Blocking.
- Add note: if the brief has no Expected Experience section (legacy briefs), skip this step

No new dependencies. Consistent with tech stack (pure markdown changes).
