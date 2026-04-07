**Status: implementation-ready**
---
## Problem
When workflow automation dispatches an agent session, the dispatched run can complete code changes without recording the Feature lifecycle transitions the role is required to own. In practice, Features dispatched from implementation-ready or review-ready can remain stuck in their pre-dispatch status even after work is complete, which breaks backlog accuracy and downstream routing.
## Goal
Guarantee that automation-dispatched sessions keep Feature status aligned with real workflow progress, including entry into active work and exit into the next valid handoff state, without relying on the dispatched agent to remember the status updates manually.
## Acceptance Criteria
- [ ] Implementation-ready dispatch moves the Feature into an active execution state before build work begins.
- [ ] A successful dispatch run does not overwrite newer Feature status changes when automation trace metadata is recorded.
- [ ] When dispatched implementation work finishes with all scoped tasks done, the Feature can advance to review-ready automatically or via an enforced workflow contract.
- [ ] Architect-review, implementation-ready, review-ready, and ship-routing dispatch paths share a consistent status-update enforcement mechanism or explicit role-specific contract.
- [ ] The Notion backlog schema used by automation supports Automation Trace writes in provisioned and upgraded workspaces.
## Non-Functional Requirements
- Backward compatible with existing automation command templates and notes-only mode.
- Additive-only Notion schema changes; do not require destructive migration.
- Status enforcement must be idempotent across repeated scans and re-dispatches.
- Keep automation behavior observable through existing trace fields and CLI outputs.
## Out of Scope
- Redesigning the full multi-agent workflow model beyond status-update enforcement.
- Replacing the current status-scanner automation architecture with a new orchestration system.
- Broad refactors to unrelated backlog, brief, or Notion client behavior.
## Open Questions
- None at architect sign-off. Ship-routing should reuse the same dispatcher-hook pattern with phase-specific exit rules, and the enforcement model will remain hybrid: dispatcher enforces minimum Feature transitions while role workflows continue to own task/backlog detail.
## Technical Approach
- Enforce minimum lifecycle transitions in the automation dispatcher layer, because that is the one path guaranteed to run for every dispatched session.
- On implementation entry, move the Feature from implementation-ready to in-progress before executing the dispatched command.
- After dispatch completion, re-read the latest backlog row before writing automation trace metadata so trace persistence cannot overwrite newer status changes made during the run.
- Apply phase-specific post-dispatch hooks: architect-review may advance the Feature when the brief reaches implementation-ready; implementation-ready may advance to review-ready once child tasks are done; review/ship phases may use the same pattern with their own exit conditions.
- Keep the mechanism additive and idempotent, and rely on agent upgrade/provision schema repair to guarantee the Automation Trace property exists in older Notion workspaces.
