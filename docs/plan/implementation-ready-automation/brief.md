**Status: implementation-ready**
---
## Problem
After architect sign-off, work still depends on someone manually noticing `implementation-ready` and invoking the implementation agent. That makes the dashboard descriptive rather than operational.
## Goal
In a later phase, detect when a Feature newly enters implementation-ready and trigger the implementation flow automatically while preserving implementation ownership and readiness checks.
## Acceptance Criteria
- [ ] The phase defines automation for Features entering `implementation-ready`.
- [ ] Dispatch occurs only on entry into `implementation-ready`.
- [ ] The implementation flow receives enough context to read the brief, backlog state, and existing tasks.
- [ ] Duplicate dispatches are prevented for unchanged items.
- [ ] The design remains compatible with the architect-review automation phase.
## Non-Functional Requirements
- **Expected load / scale:** repeated status-trigger checks across normal single-project work; later phases should coexist with earlier automation without reprocessing every backlog item on each run
- **Latency / response time:** status detection and dispatch should feel near-immediate once the trigger signal is recorded, without adding heavy startup overhead
- **Availability / reliability:** dispatch must be deterministic, idempotent, and transparent enough that operators can tell whether a trigger fired or was intentionally skipped
- **Cost constraints:** no paid infrastructure or broad orchestration platform; stay within the existing Python/CLI/framework model unless the architect justifies otherwise
- **Compliance / data residency:** planning metadata only; no new sensitive data handling beyond current artifact backends
- **Other constraints:** must preserve role ownership, remain compatible with the already-approved architect-review automation phase, and avoid making later phases depend on brittle hidden state
## Out of Scope
- Architect-review automation.
- Review automation.
- Ship routing automation.
- Auto-creating implementation scope beyond what the existing implementation agent owns.
## Open Questions
- Canonical trigger is a Backlog Feature row newly entering `implementation-ready`.
- Dispatch gate requires the linked brief to read `Status: implementation-ready` and the Feature to retain its brief link.
- Delivery-manager owns automated dispatch because it already validates readiness for the implementation handoff.
- Rerun occurs only after the Feature leaves `implementation-ready` and later re-enters it.
## Technical Approach
Build this phase on the same status-entry detection pattern established in architect-review automation, but use delivery-manager as the dispatch owner. The scanner should query Feature rows, detect new entry into `implementation-ready`, and treat the backlog row as the canonical trigger surface rather than relying on brief-body status alone.
Before dispatch, the automation should validate the minimum readiness packet already implied by the workflow: the linked brief exists, `agent brief read` returns `implementation-ready`, and the Feature still has the metadata needed to recover context. If those conditions are missing, the automation should record a visible blocker note instead of silently dispatching implementation.
After a valid trigger, the scanner should hand the feature to delivery-manager rather than implementation directly. Delivery-manager already owns the route between architect and implementation, so reusing it here preserves readiness checks and keeps the automation compatible with the orchestrated workflow model instead of bypassing it.
Idempotency should follow the Phase 1 pattern: write a deterministic dispatch token and timestamp back to the Feature row so unchanged items are skipped on later scans. A new token is allowed only when the Feature leaves `implementation-ready` and later re-enters, which cleanly models fresh architect sign-off after a return cycle.
Implementation should isolate scanning, gating, and dispatch/logging into separate modules so later phases can reuse the pattern. No new dependencies are required, and this remains medium priority because it meaningfully shortens the path from architect approval to active build work.
