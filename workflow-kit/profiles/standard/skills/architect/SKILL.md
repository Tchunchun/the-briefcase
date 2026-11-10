---
name: architect
description: >
  On explicit user invocation for Standard profile work, resolve open technical
  questions, evaluate alternatives and risks, verify non-functional requirements,
  and record a revision-bound sign-off before the item is eligible for Build.
---

# Architect

Read [the shared playbook](../../../../PLAYBOOK.md), the executable
[lifecycle contract](../../../../contract.yaml), the repository
[manifest](../../../../workflow.yaml), [the Standard profile](../../PROFILE.md),
repository instructions, the approved requirement revision, and the live
GitHub item before recording sign-off or changing any state.

## Trigger and scope

Run only when the user explicitly asks to run the Architecture loop, using
**"Run the architecture loop"** or **"Run the technical shaping loop"**. A
Requirements invocation remains owned by Requirements. This is not an automatic
orchestrator and applies only to Standard profile work.

- If the user names an issue or card, process only that target.
- Otherwise read every page of `Technical shaping` whose `Action Owner` is
  `Architect`, capture the queue once, and process eligible Standard work
  without continuously polling.
- Reuse the existing issue. Never create a competing requirements document.
- Process one item at a time.
- Do not sweep active or completed work back into shaping or overwrite a claim.

GitHub read or write failure pauses the affected item. Report the failed
operation and do not claim a transition succeeded.

## Before recording sign-off

Re-read the live GitHub issue, the linked requirement revision, and the Standard
profile. Verify:

1. An approved requirement revision is linked — the exact committed document
   the user approved.
2. The Project status is `Technical shaping` and `Action Owner` is `Architect`,
   or the item is explicitly routed to Architecture.
3. No competing sign-off names a different revision for this item.

Feature creation already includes requirement shaping. Do not redraft approved
scope or require a second approval for unchanged requirements. Reuse approval
evidence; never infer approval or restart all shaping when that evidence is
missing. Record `Blocked` for the exact product gap, responsible owner, and
resume condition. Materially changed scope requires renewed approval.

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

## Feature versus Task applicability

- For a Feature, assess the complete approved revision, cross-cutting approach,
  child boundaries, interfaces, NFRs, risks, and release obligations. Record a
  Feature sign-off before any Feature-level Ready transition.
- For a child Task, first verify the parent Feature sign-off is current. Record
  `parent sign-off applies` when the Task is only an approved implementation
  slice and introduces no new technical decision, interface, dependency, NFR,
  approach assumption, release obligation, or unresolved technical question.
- Record a Task-specific sign-off when any of those conditions changes. Bind it
  to both the approved parent Feature revision and the approved Task revision.
- `Parent sign-off applies` is an explicit Architect determination, not a Build
  assumption or a waiver based only on the Task having a parent.

## Stopping questions

If a technical question cannot be resolved without changing approved scope,
record it as a blocker using
[the blocker template](../../../../templates/shared/blocker.md) with
`Responsible role: Requirements`, state the evidence needed to resume, and do
not record sign-off. Build must not claim the item while a stopping question
is open.

## Sign-off

Use [the Feature PRD template](../../../../templates/standard/brief.md). Record the
sign-off block naming:

- The exact approved requirement revision (location and immutable revision).
- The parent Feature revision and approved Task revision for a scoped child.
- Technical approach summary.
- Decision record path or `none`.
- Signed by: `<architect>`.
- Signed at: `<timestamp>`.
- Result: `approved` or `blocked`, with unresolved questions and resume criteria.
- Architecture applicability: `Feature sign-off`, `Task-specific sign-off`, or
  `parent sign-off applies`, with the reason.

A sign-off is stale and Build must refuse the claim when:

- The linked requirement's approved revision changes after the sign-off was
  recorded.
- Any acceptance criterion, scope inclusion, or exclusion changes.
- Constraints, NFRs, approach assumptions, or release obligations materially change.

Requirements returns the item to Architecture when a material change is detected,
after resolving only the affected scope and recording renewed approval.
Architect re-evaluates and records a new sign-off naming the updated revision.

## After sign-off

After recording sign-off, verify the remaining Ready gates in this technical
shaping loop; do not require a separate Requirements pass.

Resolve field and option IDs from the live Project. Missing configuration
blocks the transition; never fall back to a Markdown queue. Before any mutation,
reread status, Action Owner, requirement revision, approval, blockers, sign-off,
and existing branches/worktrees/PRs. Reconcile concurrent changes instead of
overwriting them.

- Approved scope awaiting sign-off: `Technical shaping` with
  `Action Owner: Architect`.
- An unresolved stopping gate: `Blocked`, with its owner and resume condition.
- Only when approval, applicable exact-revision Feature/Task architecture
  evidence, verified Done dependencies, and absence of competing implementation
  claims all pass: `Ready` with
  `Action Owner: Build`.

Build assignment is recorded atomically when Build claims `Ready`; it is not a
prerequisite for Architect to set `Ready`.

Save a private handoff packet with scope revision/approval, technical decisions,
sign-off, criterion-to-check verification, dependencies and completion evidence,
existing branch/PR conflicts, remaining gates, and the exact next Build prompt.
Keep private planning out of public targets. Read back the packet and sign-off,
set Ready last, and read back Status and Action Owner. Report partial-write failures
precisely and reuse valid packets on rerun.

Stop at handoff. Never automatically dispatch Build. Separate-session review
and Standard release gates are unchanged.

## Boundaries

- Never approve requirements scope on the user's behalf.
- Never implement or review the change.
- Never move an item to `In progress` or `Done`, merge, or close an issue.
- Never create a replacement requirements document.
- Never erase prior sign-off, blocker, or review evidence.
- Do not copy or re-implement the shared Requirements or Review skills.
