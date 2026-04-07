**Status: implementation-ready**
---
## Problem
The workflow shakedown test (v0.7.0) surfaced 9 concrete gaps in the automation layer. Ship-phase automation is effectively broken: ship-dispatch is unreachable because it targets review-accepted but the workflow moves to done first, no post-dispatch hooks exist for ship phases, and release_note_link/route_state have no automation pathway. Additionally, gating checks are missing or incomplete for architect-review and implementation-ready dispatches, review_verdict is never written by automation, and task-done validation is deferred without feedback. These gaps mean the workflow relies on manual discipline for its most critical transitions.
## Goal
Close all 9 gaps identified in the shakedown so that the dispatch-driven workflow is reliable end-to-end without manual workarounds at ship, review, and routing boundaries.
## Acceptance Criteria
- [ ] **Gap 1 — Ship-phase post-dispatch hooks:** ship-routing and ship-dispatch CLI commands execute post-dispatch hooks that update Feature status and relevant fields after dispatch completes.
- [ ] **Gap 2 — release_note_link automation:** The ship wrap-up automation sets release_note_link on the Feature row when a release note is created, rather than relying on manual entry.
- [ ] **Gap 3 — route_state automation:** Delivery-manager dispatch commands (or their post-hooks) set route_state to routed/blocked/returned as appropriate at each handoff boundary.
- [ ] **Gap 4 — Ship CLI integration tests:** ship-routing and ship-dispatch have end-to-end CLI integration tests covering dispatch, post-hooks, and idempotency — matching the coverage level of implementation-ready and review-ready.
- [ ] **Gap 5 — review_verdict write path:** The review-ready post-dispatch hook (or review automation) sets review_verdict on the Feature row, rather than relying on manual skill execution.
- [ ] **Gap 6 — Task-done validation:** The review-ready gating check validates that all child Tasks are done before dispatching, or emits a clear warning/block with the list of incomplete tasks.
- [ ] **Gap 7 — architect-review gating check:** The architect-review automation validates that the linked brief exists and is in draft status before dispatching.
- [ ] **Gap 8 — implementation-ready brief status check:** The implementation-ready gating check validates that the linked brief's status field is implementation-ready, not just that the brief exists.
- [ ] **Gap 9 — ship-dispatch target status fix:** ship-dispatch targets review-accepted (the correct pre-ship status) and the ship workflow sequences correctly so ship-dispatch fires before the Feature moves to done.
## Non-Functional Requirements
- **Backward compatibility:** All changes must be additive to the existing scanner/hook architecture. No breaking changes to the StatusEntryScanner contract.
- **Test coverage:** Each gap fix must include unit tests and CLI integration tests per _project/testing-strategy.md.
- **Idempotency preserved:** All new automation hooks must remain idempotent — re-running must produce no state change or duplicate rows.
- **Cost:** No new dependencies or external services. All fixes are internal Python code.
## Out of Scope
- Fully automated E2E test suite replacing the manual shakedown script.
- Delivery-manager orchestrated mode implementation beyond route_state automation.
- New workflow phases or status values not in the current PLAYBOOK.
- Cleanup of [shakedown] canary artifacts (separate task).
## Open Questions
None — all gaps are concrete and well-characterized from shakedown evidence.
## Technical Approach
Keep the existing scanner plus phase-hook architecture and close the gaps additively.
1. Add phase-specific gates. Architect-review must resolve a linked brief and require brief status `draft`. Implementation-ready must require the resolved brief status to already be `implementation-ready`. Review-ready must inspect child Task rows by parent relation or feature fallback and block with an explicit incomplete-task list when any Task is not `done`.
2. Extend dispatch lifecycle hooks. Successful dispatches write `route_state=routed`. Failed gate checks write `route_state=blocked`. Review rejection and fix-cycle return paths write `route_state=returned` while moving the Feature back to `in-progress`. Ship-routing and ship-dispatch get explicit post-dispatch hooks rather than relying on manual backlog edits.
3. Support structured dispatch outcomes without changing the shell-command model. `_run_command_template` should continue to execute arbitrary commands, but when stdout is valid JSON it should surface fields such as `review_verdict`, `release_note_link`, `feature_status`, and `release_version` to post-dispatch hooks. Hooks should prefer explicit structured fields and fall back to refreshed store state to preserve idempotency.
4. Add ship wrap-up field automation. Ship-dispatch continues to trigger from `review-accepted` before the implementation ship step moves the Feature to `done`. After dispatch, the hook should mirror any discovered release note URL onto the Feature row, either from structured command output or from newly created release note pages. It must not claim ownership of the `done` transition itself.
5. Lock behavior with tests. Add unit coverage for the new gates, `route_state` transitions, review-return path, ship post-hooks, and structured command parsing. Add CLI integration coverage for ship-routing and ship-dispatch dispatch behavior, post-hooks, blocked cases, and idempotent reruns.
