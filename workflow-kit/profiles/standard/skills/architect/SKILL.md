---
name: architect
description: >
  On explicit user invocation for Standard profile work, resolve open technical
  questions, evaluate alternatives and risks, verify non-functional requirements,
  and record a revision-bound sign-off before the item is eligible for Build.
---

# Architect

Read [the shared playbook](../../../../PLAYBOOK.md), [the Standard profile](../../PROFILE.md),
repository instructions, the approved requirement revision, and the live GitHub
item before recording sign-off or changing any state.

## Trigger and scope

Run only when the user explicitly asks to run the Architecture loop. This is not
an automatic orchestrator and applies only to Standard profile work.

- If the user names an issue, process it first.
- Otherwise query the configured Project for live `Shaping` Standard work awaiting
  Architecture.
- Reuse the existing issue. Never create a competing requirements document.
- Process one item at a time.

GitHub read or write failure pauses the affected item. Report the failed
operation and do not claim a transition succeeded.

## Before recording sign-off

Re-read the live GitHub issue, the linked requirement revision, and the Standard
profile. Verify:

1. An approved requirement revision is linked — the exact committed document
   the user approved.
2. The Project status is `Shaping` or the item is explicitly routed to
   Architecture.
3. No competing sign-off names a different revision for this item.

## Technical assessment

For the linked requirement revision, evaluate:

1. **Technical approach** — Identify the approach most consistent with the
   repository's engineering rules, non-functional requirements, and constraints.
   State the chosen approach, the key patterns or libraries, and the constraints
   it must satisfy.

2. **Alternatives considered** — List alternatives that were seriously evaluated.
   For each, state why it was rejected. Record at least one alternative when the
   chosen approach involves a meaningful trade-off or new dependency.

3. **Risk assessment** — Identify implementation risks, integration risks, and
   known unknowns. For each risk, state its likelihood, impact, and the
   mitigation or acceptance rationale.

4. **NFR verification** — For each non-functional requirement in the approved
   revision, state whether the technical approach satisfies it and how it will
   be verified. If an NFR is unresolvable with the current scope, record it as a
   stopping question for Requirements.

5. **Decision record** — Log any significant new decision (new technology,
   meaningful reversal, or cross-cutting change) as an ADR at
   `docs/plan/_reference/adr/ADR-NNN.md` and record the path in the sign-off.
   For minor decisions, `none` is acceptable.

## Stopping questions

If a technical question cannot be resolved without changing approved scope,
record it as a blocker using
[the blocker template](../../../../templates/shared/blocker.md) with
`Responsible role: Requirements`, state the evidence needed to resume, and do
not record sign-off. Build must not claim the item while a stopping question
is open.

## Sign-off

Use [the Standard brief template](../../../../templates/standard/brief.md). Record the
sign-off block naming:

- The exact approved requirement revision (location and immutable revision).
- The parent Feature revision and approved Task revision for a scoped child.
- Technical approach summary.
- Decision record path or `none`.
- Signed by: `<architect>`.
- Signed at: `<timestamp>`.
- Result: `approved` or `blocked`, with unresolved questions and resume criteria.

A sign-off is stale and Build must refuse the claim when:

- The linked requirement's approved revision changes after the sign-off was
  recorded.
- Any acceptance criterion, scope inclusion, or exclusion changes.
- Constraints, NFRs, approach assumptions, or release obligations materially change.

Requirements returns the item to Architecture when a material change is detected.
Architect re-evaluates and records a new sign-off naming the updated revision.

## After sign-off

After recording sign-off, the item is eligible for the Ready gate under Standard
profile rules. Architecture does not move the item to `Ready` — Requirements
verifies the remaining gate conditions and routes it.

Re-read the sign-off after writing it. If the recorded value differs from the
intended sign-off, reconcile before reporting success.

## Boundaries

- Never approve requirements scope on the user's behalf.
- Never implement or review the change.
- Never move an item to `Ready`, `In progress`, or `Done`.
- Never create a replacement requirements document.
- Never erase prior sign-off, blocker, or review evidence.
- Do not copy or re-implement the shared Requirements or Review skills.
