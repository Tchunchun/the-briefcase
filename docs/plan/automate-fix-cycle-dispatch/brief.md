**Status: implementation-ready**
---
## Problem
When a review returns changes-requested verdict, the implementation agent must be re-dispatched for a fix cycle. Currently there is no automated way to detect this state and re-route. The delivery manager skill defines the Review to Implementation Fix Cycle checklist, but no agent automate command covers it. Features can sit at review-ready plus changes-requested indefinitely without triggering any action.
## Goal
agent automate fix-cycle-dispatch detects features with Feature Status review-ready and Review Verdict changes-requested, emits a dispatch payload targeting the implementation agent for the fix cycle, and optionally shells out to a configurable command — distinguishing this re-dispatch from the initial review-dispatch by reading both status axes.
## Acceptance Criteria
- [ ] agent automate fix-cycle-dispatch detects Feature rows with status=review-ready AND review_verdict=changes-requested and emits one dispatch payload per qualifying row.
- [ ] Features at review-ready with review_verdict=accepted or review_verdict=pending are NOT dispatched.
- [ ] Features at review-ready with review_verdict=changes-requested are dispatched exactly once per entry (idempotent: second scan of the same row with no status change produces dispatched_count=0).
- [ ] Dispatch payload includes feature_title, feature_id, brief_name, command_hint, dispatch_token, and detected_at.
- [ ] --notes-only mode writes trace metadata without executing a shell command.
- [ ] --dry-run mode computes dispatches without writing any trace metadata.
- [ ] --dispatch-command or AGENT_FIX_CYCLE_COMMAND env var is used to shell out to the implementation agent.
- [ ] Dispatching advances Feature status from review-ready to in-progress via pre-dispatch hook.
## Non-Functional Requirements
- Consistent with existing automation service pattern (StatusEntryScanner + thin service wrapper).
- Backward compatible: no changes to existing automate subcommands.
- Idempotent: re-scanning without a status change must not re-dispatch.
- Marker prefix and token prefix must not collide with existing automation markers.
## Out of Scope
- Dispatching the ship path (review_verdict=accepted).
- Modifying the review agent behavior.
- Full multi-agent orchestration redesign.
## Open Questions
## Technical Approach
- Add src/core/automation/fix_cycle.py mirroring architect_review.py / review_ready.py: thin wrapper around StatusEntryScanner with target_status='review-ready', marker_prefix='[auto-fix-cycle]', token_prefix='fixcycle', and a gating_check that rejects rows where review_verdict \!= 'changes-requested'.
- Add automate fix-cycle CLI command to src/cli/commands/automate.py following the same pattern as automate-review-ready: reads AGENT_FIX_CYCLE_COMMAND env var, passes phase='fix-cycle' to _build_dispatcher.
- Add pre-dispatch hook for phase='fix-cycle' in _run_pre_dispatch_hooks: moves Feature from review-ready to in-progress before executing the shell command.
- No new dependencies. No schema changes (automation_trace field already exists).
