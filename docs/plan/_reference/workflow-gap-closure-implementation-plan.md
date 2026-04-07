# Workflow Gap Closure Implementation Plan

## Objective

Complete the framework's Notion-first operational workflow without moving engineering governance or source-controlled implementation artifacts out of the local repository.

## Boundary

### Keep In Local Git

- `src/`, `tests/`, scripts, and framework code
- `skills/` and install/runtime framework files
- `_project/tech-stack.md`
- `_project/testing-strategy.md`
- `_project/definition-of-done.md`
- Code-adjacent ADRs and repo governance docs

### Keep In Notion

- Ideas and feature requirements
- Briefs
- Feature and task execution tracking
- Review and routing state
- Release notes
- User-facing operational docs and guides

## Problems To Solve

1. Existing Notion brief updates are lossy and do not safely persist body edits.
2. PM artifacts cannot be reliably linked because brief URLs/IDs are not exposed cleanly through the CLI.
3. Review outcomes are not modeled as durable workflow state.
4. Lifecycle closure from idea through shipped work is under-specified for Notion artifacts.
5. Skills and playbook instructions still blur the line between operational artifacts and engineering-governance artifacts.

## Recommended Scope

Treat this as a workflow-completion feature for PM and operational artifacts only.

Do not move `_project/tech-stack.md`, `_project/testing-strategy.md`, `_project/definition-of-done.md`, source code, tests, or framework-owned ADRs into Notion.

## Phased Implementation Plan

### Phase 1: Fix Brief Persistence

Goal: make Notion briefs safe to use as the source of truth for requirement updates.

Work:

1. Fix Notion brief writes so updating an existing brief replaces or synchronizes the page body, not only the title.
2. Preserve all required brief sections:
   - Status
   - Problem
   - Goal
   - Acceptance Criteria
   - Non-Functional Requirements
   - Out of Scope
   - Open Questions
   - Technical Approach
3. Ensure `briefcase brief read` and `briefcase brief write` round-trip the same structure.
4. Add tests covering create, update, and re-read behavior for Notion briefs.

Exit criteria:

- Existing Notion briefs can be edited safely.
- `workflow-gap-closure` can be updated in Notion without losing body content.

### Phase 2: Make PM Artifact Linking Durable

Goal: allow agents to connect Ideas, Features, Tasks, briefs, and release artifacts without manual URL hunting.

Work:

1. Update brief CLI responses to expose durable metadata needed for linking:
   - Notion page ID
   - brief URL
2. Standardize how backlog rows store and update:
   - brief link
   - parent relation
   - any future release/review links
3. Document the expected linking model:
   - Idea -> Feature
   - Feature -> Task
   - Feature -> Brief
   - Feature -> Release Notes

Exit criteria:

- Ideation and implementation can attach PM artifact links using supported CLI behavior.
- Skills no longer instruct unsupported linking steps.

### Phase 3: Add Structured Review And Routing State

Goal: make review and handoff outcomes queryable and routable without relying only on free-form notes.

Work:

1. Decide the minimum structured model for review state.
   Recommended starting point:
   - Feature retains execution status
   - review verdict is stored in a dedicated field or explicit artifact
2. Decide how delivery-manager records route state.
   Recommended starting point:
   - keep handoff packet as structured notes or a lightweight artifact
   - keep route result queryable (`routed`, `blocked`, `returned`)
3. Update review and delivery-manager skills to match the chosen model.

Exit criteria:

- Review output can drive fix-cycle vs ship routing without ambiguous notes parsing.
- Delivery-manager handoff decisions are durable and inspectable.

### Phase 4: Clarify Lifecycle Closure

Goal: define a clean, end-to-end state model for Notion-resident operational artifacts.

Work:

1. Define explicit lifecycle rules for:
   - Idea
   - Feature
   - Task
   - Review verdict
2. Decide terminal states deliberately instead of mixing operational meanings.
   Recommended principle:
   - use execution states for work progression
   - use review verdict for acceptance
   - use ship/release state for release completion
3. Update schema, playbook, and skill instructions to match the same lifecycle vocabulary.

Exit criteria:

- A team can trace a feature from idea capture to shipped release without guessing from notes.
- State names are consistent across schema, CLI, and skill instructions.

### Phase 5: Align Docs And Skills To The Boundary

Goal: remove ambiguity about what belongs in Notion vs local Git.

Work:

1. Update `skills/PLAYBOOK.md` to state:
   - Notion is for PM/ops artifacts
   - local Git is for engineering governance and implementation assets
2. Update role skills so they do not imply `_project/` governance docs belong in Notion.
3. Ensure release notes and user/operational docs are treated as Notion-resident artifacts once the release-note migration is complete.
4. Keep local engineering docs explicitly read-only from the perspective of PM workflow orchestration.

Exit criteria:

- The operational boundary is explicit and consistent everywhere.
- New contributors can tell where each artifact belongs without inference.

## Implementation Order

1. Phase 1: Fix Brief Persistence
2. Phase 2: Make PM Artifact Linking Durable
3. Phase 3: Add Structured Review And Routing State
4. Phase 4: Clarify Lifecycle Closure
5. Phase 5: Align Docs And Skills To The Boundary

## Risks And Mitigations

- Risk: schema churn breaks current tests
  - Mitigation: stage schema changes after brief persistence is stable and keep compatibility shims where practical.

- Risk: release-note work overlaps this effort
  - Mitigation: treat release notes as a dependent PM artifact and integrate only the linking/state pieces here.

- Risk: Notion and local docs diverge during transition
  - Mitigation: keep local reference docs temporary and migrate the final operational truth into supported Notion artifacts once brief persistence is fixed.

## Immediate Next Step

Ship the brief-persistence bug fix first. Until that is fixed, the Notion-backed planning workflow cannot be trusted as the editable source of truth for briefs.
