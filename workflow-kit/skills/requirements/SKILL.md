---
name: requirements
description: >
  On explicit user invocation, shape GitHub work into one approved,
  revision-bound requirement, route Standard work through Architecture, and
  verify delivery evidence before Done.
---

# Requirements

Read [the shared playbook](../../PLAYBOOK.md), the active profile, the
repository instructions, and the live GitHub issue and Project item before
changing scope or state.

## Trigger and selection

Run only when the user explicitly asks to run the Requirements loop. This is
not a continuous scanner or automatic orchestrator.

- If the user names an issue, process it first.
- Otherwise query the configured Project for live `Inbox` and `Shaping` work.
- Reuse the existing issue and Project item. Search for duplicates before
  creating anything, and never publish private planning to a public target.
- Process one item at a time. Skip work owned by another active session and
  report the owner and resume condition.

Resolve Project field and option IDs from the live board. GitHub read or write
failure pauses the affected item. Never fall back to a Markdown status queue or
claim that an unverified transition succeeded.

## Shape one requirement

Record one canonical requirement location with:

1. Stable issue identity and parent links.
2. Context, scope, exclusions, and observable acceptance criteria.
3. A verification plan that maps each criterion to a check and owner.
4. Dependencies, unresolved questions, and privacy constraints.
5. The exact approved revision and the user's approval record for it.

Use [the requirement template](../../templates/shared/requirement.md). Issue
summaries may link to an approved committed document, but must not become a
second independently editable scope. A material scope change invalidates the
approval and returns the item to `Shaping`.

## Route to the Ready gate

- Lite has no Architect role. A stopping technical question moves the item to
  `Blocked` with a Requirements-owned question and resume condition.
- Standard routes approved scope to Architecture. It cannot become `Ready`
  until Architect signs the exact same requirement revision and resolves
  stopping technical questions.
- Before `Ready`, verify all blockers are Done, the current session or named
  Build owner accepts the assignment, and no competing claim, branch,
  worktree, or implementation PR exists.
- Re-read every write. If the item changed concurrently, stop and reconcile it
  instead of overwriting the newer state.

Requirements approval is not Build assignment, review acceptance, landing, or
release evidence. Stop at the recorded handoff; the user invokes the next role.

## Blocked work

Use [the blocker template](../../templates/shared/blocker.md). Preserve the
prior status and stage, name the responsible role, state the evidence needed to
resume, and revalidate all gates before restoring the item. There is no
unconditional `Blocked` to `Ready` shortcut.

## Delivery verification

On an explicit closeout invocation, use
[the delivery template](../../templates/shared/delivery.md) and re-read live
GitHub state. Mark an item `Done` and close its issue only when all applicable
conditions are verified:

1. Review accepted the approved requirement revision and exact implementation
   head in a separate session.
2. That accepted head landed on the intended base branch.
3. Required checks pass and the issue or parent Feature has complete scope and
   child coverage.
4. Standard has linked release/version/readiness evidence; Lite follows the
   application policy without inventing a Briefcase release record.
5. Issue closure and Project `Done` both succeed and are read back.

Accepted, landed, released, and deployed remain distinct. Deployment is never
inferred from `Done`. If any closeout gate is missing, keep the item `In review`
or record a specific `Blocked` packet; do not fabricate completion.

## Boundaries

- Never approve scope on the user's behalf.
- Never write architecture sign-off for Standard.
- Never implement or review the change.
- Never merge merely because review accepted; normal repository permissions
  and delivery policy govern landing.
- Never erase prior approval, blocker, review, or delivery evidence.
