**Status: implementation-ready**
---
## Problem
During the automated implementation flow entered from the architect skill, task rows can jump from to-do directly to done because the inlined implementation instructions tell the agent to mark tasks done as work progresses without restating the required in-progress transition. That breaks backlog accuracy and conflicts with the implementation skill and PLAYBOOK task lifecycle.
## Goal
Define the smallest workflow change that makes automated implementation paths preserve the intended task lifecycle so each task moves through to-do, in-progress, and done in order.
## Acceptance Criteria
- [ ] The brief identifies the workflow path where task rows currently skip in-progress during automated implementation handoff.
- [ ] The scoped fix requires the automated implementation guidance or supporting workflow logic to move each task from to-do to in-progress before done.
- [ ] The architect can evaluate whether the fix belongs only in skill guidance, in automation helpers, or in both places.
- [ ] Validation expectations include a regression check that proves the affected path records the in-progress transition.
## Non-Functional Requirements
- **Expected load / scale:** low-frequency agent workflow operations over a small number of task rows per feature
- **Latency / response time:** no meaningful change to current workflow execution time
- **Availability / reliability:** task status tracking must stay accurate and deterministic across repeated automated runs
- **Cost constraints:** no new services or external dependencies
- **Compliance / data residency:** planning metadata only; no new secret handling
- **Other constraints:** stay aligned with PLAYBOOK task status definitions and the implementation skill lifecycle
## Out of Scope
- Redesigning the overall implementation workflow
- Changing Feature or Idea status semantics
- Reworking unrelated task backlog UX
## Open Questions
none
## Technical Approach
Keep this fix at the workflow-guidance layer rather than adding a generic automate.py task-status hook. The bug originates in the architect-to-implementation inline instructions, which tell the agent to mark tasks done as work progresses without restating the required to-do -> in-progress -> done sequence. Update the architect skill handoff steps and the implementation skill task lifecycle steps so any selected Task is explicitly moved to in-progress before code changes begin and before it can be marked done. Do not make the dispatcher mutate Task rows generically: automate.py has Feature-level routing context, but it cannot safely infer which Task should advance or when. Validation should add a regression test around the architect-triggered implementation path or command guidance plus a focused workflow test proving that affected tasks record an in-progress transition before done.
