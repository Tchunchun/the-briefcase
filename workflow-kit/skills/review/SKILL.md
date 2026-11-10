---
name: review
description: >
  On explicit user invocation in a session separate from Build, review the
  current implementation PR against the approved requirement revision, record
  evidence and findings, issue a revision-bound verdict, and merge and close
  eligible accepted work.
---

# Review

Read [the shared playbook](../../PLAYBOOK.md), the executable
[lifecycle contract](../../contract.yaml), the repository
[manifest](../../workflow.yaml), the active profile, repository instructions,
approved requirement revision, live Project item, and current PR before
reviewing. Confirm the manifest names Review as `closeout_owner` before merging,
closing an issue, or setting Done. Any other value is invalid configuration;
stop before the verdict or mutation rather than silently changing role semantics.

## Trigger and independence

Run only when the user explicitly asks to run the Review loop. If the user
names a PR or issue, review it first; otherwise consider every live `In review`
item whose `Action Owner` is `Review` and that has a ready implementation PR.

The Review session must be separate from the session that produced the code.
This applies to features, bugs, tech debt, documentation, and workflow assets.
If the current session built the head, refuse self-review and report that a new
session must review it. A GitHub account that cannot formally approve its own
PR may record an evidence-backed review comment, but must disclose that
limitation rather than fabricate an approval.

## Evidence gate

Before evaluating behavior, verify:

1. One approved requirement revision is linked.
2. The PR is open, reviewable, and targets the intended base.
3. The recorded implementation head equals the live PR head.
4. The issue, Project item, checks, dependencies, and parent scope are readable.
5. Standard architecture evidence is applicable and current: Feature work has
   Feature sign-off; Task work has current parent Feature sign-off plus either
   `parent sign-off applies` or a Task-specific sign-off naming both revisions.

Missing or stale evidence blocks a verdict. GitHub read or write failure pauses
the affected review; never fall back to Markdown status.

## Review the exact head

Use [the review template](../../templates/shared/review.md). For every
acceptance criterion, record concrete evidence from the exact PR head. Inspect
the diff, run the required checks, verify no out-of-scope behavior or legacy
regression, and confirm the expected user experience. Review complete issue
coverage, not merely the files changed by the PR.

Verdicts:

- `Accepted`: every criterion is met, required checks pass, and no blocking
  finding remains. Bind acceptance to the approved requirement revision and
  exact PR head.
- `Changes requested`: in-scope implementation defects have actionable
  findings. Keep the same issue, branch, and PR; Build resumes explicitly.
- `Blocked`: scope, approval, architecture, access, or evidence is missing and
  the responsible upstream role must act.

Any new commit invalidates the prior acceptance until the new head is reviewed.
Re-read the recorded verdict after writing it.

## Merge and closeout

For `Accepted`, reread the approved scope and exact PR head immediately before
merge. Require complete item coverage, satisfied dependencies, required checks,
eligible approvals, mergeability, and the applicable Standard delivery gate.
For a Task, verify its own approved slice and Task-allocated release obligations;
the Task does not wait for sibling Tasks or Feature completion. For a Feature,
verify all required child slices and Feature-level version, release-note,
environment, and readiness evidence.
Merge with an expected-head guard; never bypass protections or accept a changed
head without renewed review.

After GitHub confirms the merge, verify the accepted changes landed on the
intended base. Close the linked task, set `Status: Done`, and set
`Action Owner: None`, writing `Done` last and reading every mutation back. There
is no separate Deliver stage. If merge or post-merge evidence is pending, keep
`In review` with `Action Owner: Review`. If external action is required, record
`Blocked`, the responsible Action Owner, Resume Status, and resume condition.

For `Changes requested`, move the item to `In progress` with
`Action Owner: Build` and reuse the same branch and PR. Product-scope blockers
go to Requirements; technical-design blockers go to Architect.

## Handoff and boundaries

- Never review your own implementation.
- Never expand or rewrite approved scope to match the code.
- Never create a replacement issue or PR for an ordinary fix cycle.
- Never treat `Accepted` as landed, released, deployed, or `Done`.
- Never merge when required checks, approvals, scope coverage, or release
  evidence are missing.
- Deployment remains separate and is never inferred from `Done`.
