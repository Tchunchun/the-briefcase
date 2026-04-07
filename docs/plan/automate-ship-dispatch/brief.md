**Status: implementation-ready**
---
## Problem
When the review agent accepts a feature and sets Feature Status review-accepted plus Review Verdict accepted, the implementation agent must be re-dispatched to write release notes and move the feature to done. This Review-to-Ship handoff is defined in the delivery-manager skill but has no corresponding agent automate command. Features that pass review can sit at review-accepted without triggering the ship wrap-up step.
## Goal
agent automate ship-dispatch detects features with Feature Status review-accepted and Review Verdict accepted, emits a dispatch payload targeting the implementation agent for ship wrap-up, and optionally shells out to a configurable command. Pre/post dispatch hooks in the dispatcher update Feature status automatically (review-accepted to done after ship completes).
## Acceptance Criteria
- [ ] New scanner class ShipDispatchAutomationService in src/core/automation/ship_dispatch.py using StatusEntryScanner with target_status=review-accepted
- [ ] Gating check validates Review Verdict is accepted and a matching brief exists before dispatch
- [ ] CLI subcommand agent automate ship-dispatch with --dry-run, --notes-only, and --dispatch-command options
- [ ] Dispatch payload includes feature_title, feature_id, brief_name, brief_link, dispatch_token, and command_hint
- [ ] Automation trace marker [auto-ship-dispatch] written to Automation Trace field; duplicate dispatches prevented for unchanged items
- [ ] Pre-dispatch hook: no status change needed (feature stays at review-accepted until ship completes)
- [ ] Post-dispatch hook: after successful dispatch, move Feature from review-accepted to done when release note link is present
- [ ] AGENT_SHIP_COMMAND env var used as default dispatch command template
- [ ] Unit tests for scanner, gating, and trace behavior
- [ ] CLI integration test for end-to-end dispatch flow
## Non-Functional Requirements
- **Expected load / scale:** low-frequency workflow scans over review-accepted Features awaiting ship wrap-up
- **Latency / response time:** dispatch detection should remain comparable to the existing automate subcommands and add only lightweight gating checks
- **Availability / reliability:** dispatch must be idempotent for unchanged rows and must not move a Feature to done unless ship completion evidence exists
- **Cost constraints:** no new services or background workers; remain inside the current Python CLI + storage backend model
- **Compliance / data residency:** planning metadata only; release-note linkage and shipped status must remain traceable in existing artifacts
- **Other constraints:** stay consistent with the existing automation service pattern and avoid reintroducing the prior title-drift duplicate in the ship-dispatch lane
## Out of Scope
- Earlier-phase automations (architect-review, implementation-ready, review-ready)
- Release note content generation (owned by implementation agent)
- Modifying the review verdict model
- Post-ship reporting beyond routing
## Open Questions
none
## Technical Approach
Implement a new ShipDispatchAutomationService in src/core/automation/ship_dispatch.py using StatusEntryScanner with target_status=review-accepted, marker_prefix=[auto-ship-dispatch], and token_prefix=shipdsp. Gate dispatch on both review_verdict=accepted and successful brief resolution. Keep D-045 intact by routing this phase to delivery-manager via agent automate ship-dispatch rather than dispatching implementation directly, so the existing Review -> Ship readiness check remains centralized. The command should support --dry-run, --notes-only, and --dispatch-command with AGENT_SHIP_COMMAND as the default template, and emit the standard payload fields (feature_title, feature_id, brief_name, brief_link, dispatch_token, command_hint). Do not add a post-dispatch hook that moves the Feature to done: implementation still owns release-note creation and the final review-accepted -> done transition after ship wrap-up. Validation should add unit coverage for verdict gating, brief resolution, trace idempotence, and CLI integration for routed dispatch behavior only.
