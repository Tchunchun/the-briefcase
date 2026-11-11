---
name: requirements
description: >
  On explicit user invocation, shape GitHub work into one approved,
  revision-bound requirement and route Standard work through Architecture or
  Lite work to Build.
---

# Requirements

Read [the shared playbook](../../PLAYBOOK.md), the executable
[lifecycle contract](../../contract.yaml), the repository
[manifest](../../workflow.yaml), the active profile, repository instructions,
and the live GitHub issue and Project item before changing scope or state.

## Document organization

Follow the shared playbook's document organization and the repository policy.
For issue-centered repositories, write user requirements and acceptance criteria
in the canonical issue description. Keep product sign-off to four entries:
approver, approval timestamp, approved scope with a pinned snapshot link, and
approval evidence. Git snapshots retain hashes and migration history; do not
repeat that audit detail in the readable sign-off or create a separate living
approval document. Use an issue comment for the short handoff.
Never publish private planning without explicit approval.
For PO status work, apply the shared playbook's read-only PO status guidance.
Do not treat a role owner or historical pending label as a new product decision,
or a status request as permission to reshape or approve scope.

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

Before every Project mutation, follow the playbook's mandatory live preflight,
transition evaluation, and readback procedure. Requirements may evaluate only
`begin-requirement-shaping`, `standard-approved-at-creation`,
`route-standard-scope`, `ready-lite-work`, `block-work`, or
`resume-blocked-work`. A denied decision means no write.

## Naming contract — Idea to Feature

When promoting an Idea to a Feature, or creating a new Feature from scratch,
apply this contract before writing the requirement body. A title and one-liner
that pass this check let the PO understand the card without opening it.

**Title** (3–7 words): name the user outcome, not the method or the activity.
Prefer "Ship work faster from approval to merge" over "Improve pipeline velocity".
Avoid leading verbs that describe internal work ("Build", "Implement", "Test")
unless the deliverable genuinely is a build artefact the user touches.

**One-liner**: complete the sentence `<role> can <do X> without <pain Y>`.
This goes in the card body immediately after the title. It identifies who
benefits and what friction disappears. If you cannot complete it, the Feature
scope is not ready to record.

**Excludes** (at least one explicit boundary): name one thing this Feature
does NOT cover. This is the most important field for preventing shaping creep
and surfacing scope disagreements early.

**Ready when**: the simplest observable result that lets the PO say it is done.
One sentence. Not a test command — a human-readable outcome.

Record all four as a named block at the top of the requirement document, before
the full scope and acceptance criteria:

```
Title:       <user outcome, 3–7 words>
One-liner:   <role> can <do X> without <pain Y>
Excludes:    <at least one explicit boundary>
Ready when:  <simplest observable result>
```

A Feature that cannot fill in all four lines is not ready for shaping.
Raise the gap as a product question rather than inventing an answer.

## Shape one requirement

Record one canonical requirement location with:

1. Stable issue identity and parent links.
2. Context, scope, exclusions, and observable acceptance criteria.
3. A verification plan that maps each criterion to a check and owner.
4. Dependencies, unresolved questions, and privacy constraints.
5. The exact approved revision and the user's approval record for it.

Use [the requirement template](../../templates/shared/requirement.md) at the
repository's canonical location. In issue-centered repositories, preserve the
approved issue requirements block in an immutable Git snapshot; that snapshot is
historical evidence, not a second independently editable scope. Otherwise,
issue summaries link to the configured approved document. A material scope change invalidates the
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

When transitioning an item to `Blocked`, set two Project fields **before** the
status write:

- `Blocking reason`: one short phrase naming the gap and owner, e.g.
  `Product decision needed: scope boundary on mode switching (owner: PO)`.
- `Resume Status`: the status to restore when the blocker is resolved (the
  status the item held immediately before `Blocked`).

When the blocker is resolved and the item transitions out of `Blocked`, clear
`Blocking reason` (set to empty) and clear `Resume Status`. Revalidate all gates
before moving the item to its restored status.

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
- Never merge or close the change; the `closeout_owner` configured in
  [`workflow.yaml`](../../workflow.yaml) owns verified closeout.
- Never erase prior approval, blocker, review, or delivery evidence.
