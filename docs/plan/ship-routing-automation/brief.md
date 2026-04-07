**Status: implementation-ready**
---
## Problem
After review acceptance, the final step to ship work still depends on manual routing. That leaves accepted work sitting idle even though the dashboard already knows it is ready for the final handoff.
## Goal
In a later phase, automatically route accepted work into the ship path when the post-review readiness signal is recorded.
## Acceptance Criteria
- [ ] The phase defines automation for the post-review accepted or ready-to-ship signal.
- [ ] Dispatch occurs only when accepted work newly enters the ship-routing signal.
- [ ] The ship flow receives enough context to prepare release notes and final delivery tasks.
- [ ] Duplicate dispatches are prevented for unchanged items.
- [ ] The design stays compatible with the earlier architect, implementation, and review automation phases.
## Non-Functional Requirements
- **Expected load / scale:** repeated status-trigger checks across normal single-project work; later phases should coexist with earlier automation without reprocessing every backlog item on each run
- **Latency / response time:** status detection and dispatch should feel near-immediate once the trigger signal is recorded, without adding heavy startup overhead
- **Availability / reliability:** dispatch must be deterministic, idempotent, and transparent enough that operators can tell whether a trigger fired or was intentionally skipped
- **Cost constraints:** no paid infrastructure or broad orchestration platform; stay within the existing Python/CLI/framework model unless the architect justifies otherwise
- **Compliance / data residency:** planning metadata only; no new sensitive data handling beyond current artifact backends
- **Other constraints:** must preserve role ownership, remain compatible with earlier automation phases, and keep post-review routing understandable to operators
## Out of Scope
- Earlier status automations.
- Redefining the review verdict model inside this phase.
- Replacing release-note ownership.
- Post-ship reporting beyond the routing needed to start ship work.
## Open Questions
- Canonical trigger is a Feature newly entering `review-accepted`, guarded by `Review Verdict: accepted`.
- Delivery-manager owns the final dispatch into ship work.
- Operator trace is a deterministic dispatch token plus timestamp written to Feature notes.
- No separate `ready-to-ship` status is needed in v1.
## Technical Approach
Implement this phase as another status-entry scanner in the broader automation roadmap, but use the explicit post-review state that already exists. The canonical signal should be a Feature row entering `review-accepted`, with `Review Verdict: accepted` checked as a guard so the automation never routes work based on status alone when acceptance data is inconsistent.
Dispatch should go to delivery-manager, not implementation directly. By this point in the workflow the system is handling a formal handoff from accepted review to release-note and ship preparation. Delivery-manager already owns route validation and is the right place to confirm that the accepted review packet exists before kicking off the final implementation-owned ship steps.
As in the earlier automation phases, idempotency should come from an operator-visible execution trace. Write a deterministic token and timestamp into Feature notes after dispatch so later scans can distinguish an unchanged accepted item from a new acceptance event. If a feature leaves `review-accepted` and later re-enters after a real workflow change, a new token may be generated for that new event.
Keep the implementation modular: scanning current backlog state, deciding whether a row has newly entered the trigger state, and dispatching plus logging should remain separate responsibilities. That preserves compatibility with earlier automation phases without forcing a large generalized orchestration framework.
This phase is useful but later in the value chain than architect and implementation entry automation, so it should be treated as low technical priority once the design is settled.
