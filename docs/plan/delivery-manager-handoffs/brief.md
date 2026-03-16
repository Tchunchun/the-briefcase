# Delivery Manager Handoffs (v1)

**Status: implementation-ready**

---

## Problem
The current workflow requires the user to manually coordinate handoffs between implementation and review agents. This creates extra overhead, inconsistent transitions, and risk of missed context or incomplete readiness checks at phase boundaries.

## Goal
Introduce a delivery-manager role that owns handoff orchestration so existing role owners can focus on their core responsibilities while flow, status, and blocking issues are managed consistently.

## Acceptance Criteria
- [ ] A new `delivery-manager` role is defined in the agent system with explicit responsibilities for coordinating handoffs across phases
- [ ] The role's scope is limited to orchestration (readiness checks, status tracking, escalation, and handoff packaging), not code implementation or acceptance decisions
- [ ] Handoff entry and exit criteria are documented for each transition: ideation -> architect, architect -> implementation, implementation -> review, review -> implementation (fix cycle), and review -> ship
- [ ] A standard handoff packet format is defined (required artifacts, status signals, unresolved questions, blockers, and next-owner action list)
- [ ] Escalation rules are documented for blocked handoffs (missing artifacts, unclear ownership, failing acceptance criteria, or conflicting scope)
- [ ] Existing ownership boundaries in `skills/PLAYBOOK.md` remain explicit and intact for ideation, architect, implementation, and review roles
- [ ] The new role can be introduced without breaking existing projects that still run the four-role workflow

## Non-Functional Requirements

- **Expected load / scale:** Single-user and small-team projects with multiple concurrent feature briefs
- **Latency / response time:** Handoff preparation and readiness checks should add minimal overhead (target under 2 minutes per transition in normal flow)
- **Availability / reliability:** Handoff tracking should be deterministic and resilient to partial updates; blocked states must be explicit
- **Cost constraints:** No required paid tools or external services to use the role
- **Compliance / data residency:** No additional data classes introduced beyond existing project artifacts
- **Other constraints:** Must preserve current role ownership model and avoid role ambiguity

## Out of Scope
- Replacing implementation or review decisions with delivery-manager decisions
- Changing technical architecture for product code
- Automatically generating implementation tasks or code
- Redesigning the full agent model beyond adding orchestration support

## Open Questions
- Should delivery-manager be a fully separate skill (`skills/delivery-manager/SKILL.md`) or a protocol layer inside `skills/PLAYBOOK.md`?
- Where should handoff state be stored as source of truth (existing `docs/plan/_shared/backlog.md`, a new shared artifact, or brief/task status fields)?
- What minimum artifact completeness is required before each handoff is allowed?
- What is the canonical signal that review is "accepted" versus "changes requested" for downstream routing?
- How should this role behave in single-agent sessions where one person may temporarily perform multiple roles?

## Technical Approach
*Resolved by architect agent — 2026-03-16*

### Role and Routing Model

Add `delivery-manager` as a fifth role with orchestration-only authority. This role is responsible for phase-transition coordination but does not own product scope, technical architecture, implementation, or acceptance decisions.

Routing update to `skills/PLAYBOOK.md`:
- Add `Delivery Manager Agent` in Agent Routing.
- Insert orchestration checkpoints into the Handoff Sequence between all major phases.
- Keep original ownership rows for ideation, architect, implementation, and review unchanged.

### Skill Packaging Decision

Implement `delivery-manager` as a dedicated skill at `skills/delivery-manager/SKILL.md` and reference it from `skills/PLAYBOOK.md`.

Rationale:
- Keeps orchestration behavior explicit and discoverable.
- Avoids overloading existing role skills with cross-cutting coordination logic.
- Supports incremental adoption by projects that may choose to enable or skip this role.

### Source of Truth for Handoff State

Do not introduce a new persistent handoff file in v1. Use existing artifacts:
- `docs/plan/{feature}/brief.md`: scope state and architecture readiness (`draft`/`implementation-ready`)
- `docs/plan/{feature}/tasks.md`: execution state and review-response tracking
- `docs/plan/_shared/backlog.md`: cross-feature status summary and blockers

Delivery manager writes only structured status notes to existing owner-approved status fields/sections defined in PLAYBOOK updates. This preserves backward compatibility and avoids ownership sprawl.

### Handoff Packet Contract (v1)

For each transition, delivery manager compiles a packet with:
- Transition name and timestamp
- Source owner, destination owner
- Required artifact links
- Readiness checklist result (`pass`/`blocked`)
- Open blockers and escalation target
- Explicit "next-owner action list"

Minimum required packet content by transition:
- Ideation -> Architect: `brief.md` exists, Status `draft`, Open Questions present or explicitly none
- Architect -> Implementation: `brief.md` Status `implementation-ready`, Technical Approach completed, unresolved architectural blockers = none
- Implementation -> Review: `tasks.md` reflects completed build scope, tests noted, backlog row updated
- Review -> Implementation (fix cycle): review findings summarized with severity and actionable items
- Review -> Ship: acceptance recorded and release-note readiness confirmed

### Review Outcome Signal

Canonical outcomes for downstream routing:
- `accepted`: no blocking findings, ship path allowed
- `changes-requested`: one or more blocking findings, returns to implementation

These outcomes are recorded in the review-owned output and mirrored by delivery-manager in backlog notes for cross-feature visibility.

### Single-Agent Session Behavior

If one person is operating multiple roles, delivery-manager still runs as an explicit checkpoint function:
- enforce checklist before transition,
- record route decision,
- mark blockers instead of silently proceeding.

This preserves process integrity without requiring multiple active people.

### Compatibility and Cost

- No new runtime dependencies are required for v1.
- No paid tooling is required.
- Existing four-role projects remain valid: delivery-manager is additive and can be optional behind a PLAYBOOK toggle ("enabled: true/false").

### Implementation Notes for Follow-On Work

Implementation-ready changes are expected in:
- `skills/PLAYBOOK.md` (routing, handoff sequence, collaboration protocol updates)
- `skills/delivery-manager/SKILL.md` (new role definition and operating checklist)
- Optional template updates if a standardized handoff note block is added to `template/tasks.md` or `template/brief.md`

---

## Notes

- Drafted from ideation scope to address explicit handoff coordination pain.
- Architect should resolve Open Questions and define where orchestration state lives.
- Implementation should start only after architect sets `Status: implementation-ready`.
