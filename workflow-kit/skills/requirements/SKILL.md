---
name: requirements
description: >
  On explicit user invocation, shape GitHub work into one approved,
  revision-bound requirement and route Standard work through Architecture or
  Lite work to Build.
---

# Requirements

Read [the shared playbook](../../PLAYBOOK.md), the active profile, the
repository instructions, and the live GitHub issue and Project item before
changing scope or state.

## Trigger and selection

Requirements remains the product-shaping entry point in both profiles. For an
already approved Standard Feature, report that product shaping is complete and
hand it to [Architect](../../profiles/standard/skills/architect/SKILL.md); never
silently execute the Architecture loop from a Requirements invocation.

Run only when the user explicitly asks to run the Requirements loop. This is
not a continuous scanner or automatic orchestrator.

- If the user names an issue, process it first.
- Otherwise query the configured Project for live `Inbox` and
  `Requirement shaping` work whose `Action Owner` is `Requirements`.
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
approval. Lite returns to `Requirement shaping`; Standard records `Blocked`
for the specific product decision, then returns to `Technical shaping` for
renewed sign-off.

## Route to the Ready gate

- Lite has no Architect role. A stopping technical question moves the item to
  `Blocked` with a Requirements-owned question and resume condition.
- Standard moves approved scope to `Technical shaping` with
  `Action Owner: Architect`. It cannot become `Ready` until Architect signs the
  exact same requirement revision and resolves stopping technical questions.
- Lite moves approved work to `Ready` with `Action Owner: Build` after blockers
  and other readiness gates pass. Build assignment is recorded during the
  later claim, not as a prerequisite for `Ready`.
- Re-read every write. If the item changed concurrently, stop and reconcile it
  instead of overwriting the newer state.

Requirements approval is not Architecture sign-off, Build assignment, review
acceptance, landing, or release evidence. Stop at the recorded handoff; the
user invokes the next role.

## Blocked work

Use [the blocker template](../../templates/shared/blocker.md). Preserve the
prior status, set `Action Owner` to the role that must act, record `Resume
Status`, state the evidence needed to resume, and revalidate all gates before
restoring the item. There is no unconditional `Blocked` transition.

## Boundaries

- Never approve scope on the user's behalf.
- Never write architecture sign-off for Standard.
- Never implement or review the change.
- Never merge or close the change; Review owns verified closeout.
- Never erase prior approval, blocker, review, or delivery evidence.
