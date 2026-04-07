**Status: implementation-ready**
---
## Problem
Once implementation is complete, consumer users should not have to manually call the review agent. Without automation, `review-ready` remains only a board label instead of a review trigger.
## Goal
In a later phase, detect when a Feature newly enters review-ready and trigger the review flow automatically with the required brief and backlog context.
## Acceptance Criteria
- [ ] The phase defines automation for Features entering `review-ready`.
- [ ] Dispatch occurs only on entry into `review-ready`.
- [ ] The review flow receives enough context to validate the feature against the brief and backlog state.
- [ ] Duplicate dispatches are prevented for unchanged items.
- [ ] The design remains compatible with earlier architect and implementation automation phases.
## Non-Functional Requirements
- **Expected load / scale:** repeated status-trigger checks across normal single-project work; later phases should coexist with earlier automation without reprocessing every backlog item on each run
- **Latency / response time:** status detection and dispatch should feel near-immediate once the trigger signal is recorded, without adding heavy startup overhead
- **Availability / reliability:** dispatch must be deterministic, idempotent, and transparent enough that operators can tell whether a trigger fired or was intentionally skipped
- **Cost constraints:** no paid infrastructure or broad orchestration platform; stay within the existing Python/CLI/framework model unless the architect justifies otherwise
- **Compliance / data residency:** planning metadata only; no new sensitive data handling beyond current artifact backends
- **Other constraints:** must preserve role ownership, remain compatible with earlier automation phases, and avoid making later phases depend on brittle hidden state
## Out of Scope
- Architect-review automation.
- Implementation-ready automation.
- Ship routing after review acceptance.
- Changing review ownership or verdict rules.
## Open Questions
- No hold flag in v1; first prove the base status-entry flow.
- Minimum evidence contract is all child tasks done plus a short review packet in Feature notes summarizing tests run and known caveats.
- Delivery-manager validates the packet and dispatches review.
- Re-review should happen by moving the Feature back to `in-progress` during fixes and later re-entering `review-ready`.
## Technical Approach
Implement review automation as a status-entry scanner for Features entering `review-ready`, but do not treat the status change as sufficient evidence on its own. This phase should require a lightweight review packet that implementation writes into Feature notes, including at minimum the test scope run, the date or timestamp of that run, and any known caveats the reviewer should inspect.
The scanner should use the backlog Feature row as the canonical trigger and then hand off to delivery-manager for validation. Delivery-manager should confirm that all child Task rows are done, the review packet exists, and the feature is not already carrying an accepted or pending dispatch token for the same entry event. That keeps the automation aligned with the current handoff model instead of bypassing it.
Duplicate prevention should mirror the earlier automation phases: after dispatch, write a deterministic token and timestamp into Feature notes. As long as the Feature stays in `review-ready` with the same token, later scans should skip it. Re-review after `changes-requested` should be modeled by implementation moving the Feature back to `in-progress` during the fix cycle and then returning it to `review-ready`, which gives the scanner a real new entry event.
Keep the implementation modular so the phase can share scanning and logging patterns with implementation-ready and ship-routing automation while still owning its own gating logic. No new dependencies are required. This is useful but not as urgent as the earlier workflow-entry automations, so it should be treated as low technical priority.
