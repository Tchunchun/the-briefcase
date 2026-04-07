**Status: implementation-ready**
## Problem
Once a Feature reaches architect-review, consumer users should not have to manually invoke the architect agent. The dashboard already captures that status, but there is no automation to detect the transition and begin architect work.
## Goal
Detect when a Feature newly enters architect-review and trigger the architect review flow automatically, with enough context and safeguards to avoid duplicate or premature dispatch.
## Acceptance Criteria
- [ ] A watcher detects when a Feature newly enters `architect-review`.
- [ ] The automation triggers only on status entry, not on every scan of unchanged architect-review items.
- [ ] The architect flow receives the feature identifier and enough context to read the brief and related backlog state.
- [ ] Duplicate dispatches are prevented for unchanged items.
- [ ] The automation records a routing signal, note, or execution trace visible to operators.
- [ ] This phase fits under the broader status-driven automation roadmap without requiring later phases to share the same implementation details.
## Out of Scope
- Automating `implementation-ready`, `review-ready`, or ship routing in this phase.
- Auto-approving briefs or bypassing architect ownership.
- Replacing existing role boundaries.
- Building generalized orchestration infrastructure beyond what this phase needs.
## Open Questions
- Direct architect dispatch is recommended for Phase 1; do not route through delivery-manager yet.
- The canonical entry-transition signal should be the Backlog Feature row entering `architect-review`.
- The minimal operator log should be a deterministic dispatch token plus timestamp recorded on the Feature row notes.
- A manual hold flag is not recommended for Phase 1 unless implementation uncovers a concrete operator need.
## Technical Approach
Phase 1 should be implemented as a narrowly scoped status-entry scanner that treats the Backlog Feature row as the canonical trigger surface. The scanner should query Feature items, identify rows whose `Feature Status` is `architect-review`, and detect only newly entered items by comparing the current state against a persisted execution marker rather than re-dispatching on every scan. Because the brief body can drift from backlog status, brief page content must be treated as supporting context only, not as the trigger source.
Dispatch should go directly to the architect flow in this phase rather than through delivery-manager. Delivery-manager's current contract is centered on handoff validation and routing between established role transitions, especially around implementation and review. Reusing it here would broaden scope before the automation pattern is proven. The dispatch payload should include the feature title or slug, backlog item ID, brief URL, brief name, and any parent linkage needed to recover the surrounding initiative context.
To prevent duplicate execution, the scanner should write a deterministic trace back to the Feature row after dispatch. The minimum viable trace is an execution marker stored in operator-visible metadata, such as a timestamped note plus a machine-readable dispatch token derived from the backlog item ID and the current architect-review entry event. On later scans, the automation should skip any item that is still in `architect-review` but already has the matching dispatch token recorded. If the item leaves architect-review and later re-enters, the automation may emit a new token for that new entry event.
Operator visibility should stay simple in Phase 1. The automation should record that architect dispatch happened, when it happened, and which feature/brief it targeted. A note on the Feature row is sufficient if it is deterministic enough for operators to distinguish a fresh dispatch from a prior one. Route State may be used only if it clearly reflects automation state without overloading delivery-manager semantics; otherwise, leave routing vocabulary unchanged and keep the trace in notes.
This phase should be implemented behind a dedicated CLI entry point or service module that can later be composed into broader status-driven automation, but it should not require a generalized orchestration framework. The implementation should isolate three responsibilities: scanning current backlog state, deciding whether an item has newly entered architect-review, and dispatching/logging the architect invocation. That separation will let later phases reuse the pattern without forcing them to share the same persistence or dispatch mechanism.
Phase 1 should not introduce an explicit manual hold flag unless a concrete operator need appears during implementation. The first version can stay safe by being additive, idempotent, and observable. If manual suppression becomes necessary later, it can be added as a separate workflow control once the base status-entry pattern is validated.
**Status: implementation-ready**
## 
