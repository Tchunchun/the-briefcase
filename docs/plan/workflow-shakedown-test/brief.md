**Status: implementation-ready**
---
## Problem
We have implemented individual workflow automations and storage-level tests, but we do not yet have a single planning artifact that defines how to validate the full ideation-to-ship workflow on the active Notion backend. Without a deliberate shakedown, gaps in handoffs, status mappings, automation routing, or recovery paths can survive until real feature work depends on them.
## Goal
Run a dispatch-driven end-to-end workflow test on a new isolated test feature, exercising all phases from ideation through ship, surface gaps before broader rollout, and produce a concrete field-level checklist reviewed together before execution.
## Acceptance Criteria
- [ ] **Happy-path dispatch run:** All phases (ideation → architect → implementation → review → ship) are driven by dispatch commands for a new isolated test feature. At each phase boundary, the following fields are explicitly verified: brief Status, Feature Status, Review Verdict, Route State, and trace notes presence. At ship, Release Note Link is set and Feature Status is done.
- [ ] **Failure-path / fix-cycle dispatch run:** Review returns changes-requested. Dispatch routes back to implementation. Verified fields: Review Verdict = changes-requested, Route State = routed, Feature Status = in-progress. After the fix, review re-runs via dispatch and Review Verdict flips to accepted with Feature Status = review-accepted.
- [ ] **Guardrail / invalid transition test:** An invalid or premature state transition is attempted (e.g., dispatching to implementation before architect sign-off). Verified outcome: Route State = blocked, a trace note capturing the block reason is present, and no duplicate backlog rows are created.
- [ ] **Field-level state audit at every phase boundary:** At each of the five handoff points (ideation handoff, architect handoff, implementation handoff, review handoff, ship), all applicable fields are checked: brief Status, Feature Status, Review Verdict, Route State, trace notes presence, and Release Note Link (where applicable).
- [ ] **Idempotency verified:** Re-running any dispatch command on an already-transitioned feature produces no state change and creates no duplicate backlog rows. Automation behavior is confirmed idempotent.
- [ ] **Known gaps documented before execution:** Gaps observed from the current implementation and test suite are captured in the brief prior to running the shakedown, so the review session starts from a concrete risk list rather than discovery during execution.
## Non-Functional Requirements
- **Expected load / scale:** Single test feature packet and one deliberate failure branch; no bulk migration or high-volume automation needed.
- **Latency / response time:** Best-effort for live Notion operations; the workflow may require short waits between status changes and reads.
- **Availability / reliability:** The test should be runnable in the active Notion workspace without disrupting shipped items; use clearly isolated test titles prefixed with [shakedown] for easy identification and cleanup.
- **Cost constraints:** Keep the exercise lightweight and limited to one planned packet plus one fix-cycle branch.
- **Compliance / auditability:** Each state change should remain visible in Notion history and CLI-readable artifacts so the review can reconstruct what happened.
- **Other constraints:** The operator script produced during architect review must be precise enough to serve as a repeatable regression script for future framework versions. Prefer validating the existing workflow over adding new framework code first; the purpose is to expose gaps, not mask them.
## Out of Scope
- Implementing fixes found during the shakedown in the same session.
- Adding new workflow phases beyond the current PLAYBOOK.
- Broad regression coverage for every existing feature in the backlog.
- Converting this proposal into a fully automated E2E suite before the manual shakedown is reviewed.
## Open Questions
None — all open questions resolved.
## Technical Approach
### Approach
Operator-driven CLI walkthrough against live Notion. No new framework code — the purpose is to expose gaps, not mask them.
### Test Isolation
All artifacts use [shakedown] prefix. A single test feature [shakedown] canary flows through the full lifecycle. Stub implementation uses a minimal src/shakedown/ + tests/shakedown/ with a trivial passing test. Cleanup is manual deletion of [shakedown]-prefixed rows after completion.
### Known Gaps (Pre-Execution Risk List)
Audited from current automation modules and test suite — these are concrete risks the shakedown should surface and document:
1. No post-dispatch hooks for ship phases — ship-routing and ship-dispatch CLI commands dispatch but never update Feature status or set required fields after dispatch.
2. release_note_link is orphaned — no automation writes it; relies entirely on manual skill execution during ship.
3. route_state is orphaned — no automation pathway to mark delivery-manager routing decisions; manual-only.
4. No CLI integration tests for shipping — ship-routing and ship-dispatch commands are untested end-to-end through the CLI layer.
5. review_verdict write path is manual-only — automation modules gate on review_verdict (fix-cycle, ship-routing, ship-dispatch) but none write it.
6. Task-done validation deferred without verification — review-ready gating defers task-done check to delivery-manager but provides no feedback mechanism.
7. architect-review automation has no gating check — no validation that the brief is actually ready before dispatching to architect.
8. implementation-ready gate checks brief existence but not brief status — a feature could be dispatched even if the brief status has not been updated.
### Operator Script
#### Phase 0-1: Ideation to Brief Draft
agent inbox add --type idea --text "[shakedown] canary" --notes "Shakedown test feature"
agent brief write shakedown-canary --status draft --problem "Shakedown test" --goal "Validate workflow" --change-summary "Initial shakedown brief"
agent backlog upsert --title "[shakedown] canary" --type Idea --status exploring
agent backlog upsert --title "[shakedown] canary" --type Feature --status architect-review --brief-link "<brief-url>"
Assert after Phase 0-1: Brief Status = draft, Feature Status = architect-review, Review Verdict = empty, Route State = empty, Idea Status = exploring.
#### Phase 1.5: Architect Sign-Off
Guardrail test first — attempt premature dispatch:
agent automate implementation-ready --dry-run
Assert: dispatched_count = 0 (feature not yet implementation-ready).
Then sign off:
agent brief write shakedown-canary --status implementation-ready --change-summary "Architect sign-off for shakedown"
agent backlog upsert --title "[shakedown] canary" --type Feature --status implementation-ready
agent backlog upsert --title "[shakedown] canary" --type Idea --status promoted
agent automate implementation-ready --notes-only
Assert after Phase 1.5: Brief Status = implementation-ready, Feature Status = implementation-ready, Automation Trace contains dispatch token, Idea Status = promoted.
Idempotency test:
agent automate implementation-ready --notes-only
Assert: dispatched_count = 0, no duplicate rows.
#### Phase 2-3: Implementation to Review-Ready
agent backlog upsert --title "[shakedown] canary" --type Feature --status in-progress
agent backlog upsert --title "[shakedown] canary task 1" --type Task --status to-do --priority Medium
agent backlog upsert --title "[shakedown] canary task 1" --type Task --status in-progress
Create stub code: src/shakedown/__init__.py (empty) and tests/shakedown/unit/test_canary.py (single passing test).
python3 -m pytest tests/shakedown/
agent backlog upsert --title "[shakedown] canary task 1" --type Task --status done --notes "Tests: 1/1 pass"
agent backlog upsert --title "[shakedown] canary" --type Feature --status review-ready
agent automate review-ready --notes-only
Assert after Phase 2-3: Feature Status = review-ready, Task Status = done, Automation Trace updated with review-ready dispatch.
#### Phase 4a: Review to Changes Requested (Failure Path)
agent backlog upsert --title "[shakedown] canary" --type Feature --review-verdict changes-requested
agent automate fix-cycle-dispatch --notes-only
Assert after Phase 4a: Review Verdict = changes-requested, Automation Trace contains fix-cycle dispatch.
#### Phase 4b: Fix Cycle to Re-Review to Accepted
agent backlog upsert --title "[shakedown] canary" --type Feature --status in-progress
agent backlog upsert --title "[shakedown] canary" --type Feature --status review-ready
agent backlog upsert --title "[shakedown] canary" --type Feature --review-verdict accepted
agent backlog upsert --title "[shakedown] canary" --type Feature --status review-accepted
agent automate ship-routing --notes-only
Assert after Phase 4b: Review Verdict = accepted, Feature Status = review-accepted, Automation Trace contains ship-routing dispatch.
#### Phase 5: Ship
agent release write --version v-shakedown --notes "Shakedown canary release note"
agent backlog upsert --title "[shakedown] canary" --type Feature --status done --release-note-link "<release-note-url>" --notes "Shipped [shakedown] canary"
agent automate ship-dispatch --notes-only
agent backlog upsert --title "[shakedown] canary" --type Idea --status shipped --notes "Shipped via shakedown"
Assert after Phase 5: Feature Status = done, Release Note Link = set, Idea Status = shipped, Automation Trace contains ship-dispatch.
### Field-Level Audit Matrix
Post-ideation: Brief=draft, Feature=architect-review, Verdict=-, Route=-, Trace=-, ReleaseLink=-
Post-architect: Brief=impl-ready, Feature=impl-ready, Verdict=-, Route=-, Trace=dispatch token, ReleaseLink=-
Post-impl: Brief=impl-ready, Feature=review-ready, Verdict=-, Route=-, Trace=updated, ReleaseLink=-
Post-review-fail: Brief=impl-ready, Feature=review-ready, Verdict=changes-requested, Route=-, Trace=fix-cycle token, ReleaseLink=-
Post-review-pass: Brief=impl-ready, Feature=review-accepted, Verdict=accepted, Route=-, Trace=ship-routing token, ReleaseLink=-
Post-ship: Brief=impl-ready, Feature=done, Verdict=accepted, Route=-, Trace=ship-dispatch token, ReleaseLink=set
Note: Route State expected empty throughout — known gap #3. The shakedown will confirm this gap exists in practice.
