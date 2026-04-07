**Status: draft**
## Problem
The current feature lifecycle jumps from implementation-ready toward done without a clean state for work that is implemented, tested, and awaiting review. That makes review intake ambiguous and overloads done before the feature is actually shipped.
## Goal
Introduce an explicit review handoff state so implementation, review, and ship each have a durable and unambiguous transition point in the workflow.
## Acceptance Criteria
- [ ] The workflow defines a Feature state for implementation-complete work that is awaiting review, and that state is named and documented consistently across backlog schema, playbook, and role skills.
- [ ] The implementation agent is responsible for moving a Feature into that review intake state only after scoped work and relevant tests are complete.
- [ ] The review agent is responsible for pulling Features from that review intake state and recording an acceptance outcome that can route either a fix cycle or a ship path.
- [ ] Accepted work does not overload `done` before ship; the lifecycle preserves a distinct post-review, pre-ship state or equivalent structured routing signal.
- [ ] The end-to-end Feature lifecycle from draft through ship is documented clearly enough that each role can update the correct state without relying on free-form interpretation.
## Out of Scope
- Fixing unrelated Notion brief persistence issues beyond what is needed to support this lifecycle change.
- Redesigning Idea or Task workflows except where they must align with Feature review handoff.
- Reworking the broader five-role model or replacing delivery-manager orchestration.
- Historical cleanup of old backlog rows unless migration is required for the new state model.
## Open Questions
- Should the accepted post-review state be modeled as `accepted`, `ready-to-ship`, or as a separate review verdict field while Feature status stays unchanged?
- Should review verdicts be stored directly on Feature rows, or as a separate artifact/property that delivery-manager can route from?
- What is the smallest backwards-compatible migration for existing Feature rows that currently use `done` immediately after review acceptance?
- Non-functional requirements are not currently representable through the brief CLI/Notion renderer; should that brief schema gap be solved first or tracked separately?
## Technical Approach
*Owned by architect agent.*
