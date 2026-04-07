## Problem
Even with the delivery-manager role added, users still need to manually invoke implementation and review agents. This breaks the goal of a single operational interface and leaves orchestration gaps when users forget or sequence steps inconsistently.
## Goal
Enable a delivery-manager-led execution mode where the user interacts with only delivery-manager, and delivery-manager delegates to implementation and review subagents through the existing skills/playbook framework.
## Acceptance Criteria
- [ ] A documented orchestrated mode allows users to interact only with delivery-manager for implementation and delivery flow
- [ ] Delivery-manager delegates implementation work to the existing implementation skill (no replacement or duplicated implementation logic)
- [ ] Delivery-manager delegates quality validation to the existing review skill (no replacement or duplicated review logic)
- [ ] Routing from review outcome is deterministic: `accepted` -> ship path, `changes-requested` -> implementation fix cycle
- [ ] Existing artifact ownership remains intact (implementation owns `tasks.md`, backlog status, `src/`, `tests/`, release notes, and user docs; review owns findings/verdict)
- [ ] Delivery-manager remains orchestration-only and does not write code or alter review decisions
- [ ] The design explicitly uses existing framework primitives (`skills/PLAYBOOK.md` + role `SKILL.md` contracts), with no custom hand-rolled agent framework
- [ ] Backward compatibility is preserved: existing manual invocation flow still works
## Out of Scope
- Replacing implementation or review skill responsibilities
- Auto-writing scope/architecture outside existing ideation and architect flow
- Introducing a new artifact store or new external workflow engine
- Requiring users to change existing four-role projects immediately
## Open Questions
- Where should delegated subagent execution traces be recorded: `tasks.md` notes, backlog notes, or both?
- Should orchestrated mode be default-on, default-off, or controlled by a project flag in `skills/PLAYBOOK.md`?
- What is the minimum retry policy when a delegated subagent run fails (retry count and escalation path)?
- How should delivery-manager surface partial progress to users during long implementation runs?
## Technical Approach
*Resolved by architect agent — 2026-03-16*
### Orchestration Model (No Hand-Rolled Framework)
Implement orchestrated mode by composing existing workflow primitives only:
- `skills/PLAYBOOK.md` routing rules
- existing role skills (`implementation`, `review`)
- `delivery-manager` as orchestrator
No new agent framework, scheduler, or external orchestration service is introduced.
### Delegation Contract
Delivery-manager becomes the sole user-facing entry point during build/review/ship for opted-in projects.
For each phase transition, delivery-manager must:
1. run the transition checklist,
2. append a handoff packet,
3. dispatch to the target role skill,
4. record route result (`routed` or `blocked`).
Subagent responsibilities remain unchanged:
- Implementation owns `tasks.md`, backlog status fields, `src/`, `tests/`, release notes, and `docs/user/`.
- Review owns findings severity and verdict.
- Delivery-manager may append coordination notes only where allowed by PLAYBOOK.
### State and Trace Storage
Use existing artifacts as source of truth (no new files):
- Primary execution trace: `docs/plan/{feature}/tasks.md` (`Handoff Packet`, `Review Findings`, `Review Verdict`, Notes)
- Cross-feature visibility: coordination notes in `docs/plan/_shared/backlog.md`
Decision: use both `tasks.md` and backlog notes, with `tasks.md` as canonical per-feature trace.
### Mode Toggle and Backward Compatibility
Add a PLAYBOOK-level project mode toggle:
- `orchestrated-mode: true` -> delivery-manager is primary interface.
- `orchestrated-mode: false` -> legacy manual invocation remains valid.
Default for new projects: `false` to avoid breaking current usage.
Recommendation: teams can enable `true` once delivery-manager workflow is adopted.
### Retry and Failure Handling
For delegated subagent execution failure:
- Retry up to 1 immediate attempt if failure is transient (tool/session interruption).
- If second attempt fails, set transition to `blocked` and emit escalation packet with unblock requirements.
- Escalation target:
  - Architect for architecture/ambiguity blockers
  - User for priority/scope/approval blockers
This satisfies reliability NFR without hidden loops.
### Progress Reporting for Long Runs
Delivery-manager posts periodic plain-language status updates at each milestone:
- `dispatched`
- `in progress`
- `blocked` (with explicit reason and next action)
- `returned` (with summary)
No new telemetry system is required; status is text plus handoff packets.
### Deterministic Review Routing
Route strictly by review verdict:
- `accepted` -> implementation ship path
- `changes-requested` -> implementation fix cycle
Delivery-manager must not reinterpret or override review outcomes.
### Dependency and Cost Impact
No new dependencies are introduced beyond the current stack (`Python 3.11+`, role skill docs, markdown artifacts).
Estimated incremental cost: $0/month.
Licensing impact: none.
---
