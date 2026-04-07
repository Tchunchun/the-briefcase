**Status: draft**
## Problem
Consumer users should not have to manually call each agent to keep work moving. Now that Feature backlog status is captured on the dashboard, the framework can use status transitions as the trigger surface for routing work to the right agent, but that automation does not exist yet.
## Goal
Introduce phased status-driven automation so the dashboard becomes the operational entry point: users update Feature status, and the framework triggers the correct agent flow behind the scenes.
## Acceptance Criteria
- [ ] Phase 1 defines and implements automation for Features entering `architect-review`.
- [ ] Phase 1 triggers only on entry into `architect-review`, dispatches the architect flow with the minimum required context, and avoids duplicate dispatches for unchanged items.
- [ ] Phase 1 records a routing signal, note, or execution trace so operators can tell that architect review was triggered.
- [ ] The brief explicitly defines later phases for `implementation-ready`, `review-ready`, and post-review accepted/ship routing so the automation roadmap is visible from the start.
- [ ] The phased design preserves role ownership: status changes trigger the framework, but architect, implementation, review, and ship responsibilities remain with their existing role agents.
- [ ] The design is extensible enough that later phases can be added without redesigning the trigger model or abandoning the dashboard as the source of truth.
## Out of Scope
- Implementing all status automations in Phase 1.
- Allowing automation to bypass role-specific checks or auto-approve work.
- Replacing the five-role workflow with a new orchestration model.
- Building broad retry, escalation, or scheduling infrastructure beyond what is needed to support the first phase safely.
## Open Questions
- Phase 1: should the `architect-review` trigger dispatch the architect agent directly, or route through delivery-manager so orchestration remains centralized?
- Phase 1: what is the canonical signal that a Feature has newly entered a status so duplicate dispatches can be prevented?
- Phase 2: should `implementation-ready` and `review-ready` dispatch immediately on status entry, or should they support a manual hold/release flag?
- Phase 3: should post-review accepted work use a dedicated Feature status like `ready-to-ship`, or a separate review verdict field that then triggers ship automation?
- What minimal execution log should be persisted across all phases so users can inspect whether an automation fired successfully?
## Technical Approach
*Owned by architect agent.*
