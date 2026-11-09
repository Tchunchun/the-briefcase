---
name: review
description: >
  On explicit user invocation in a session separate from Build, review the
  current implementation PR against the approved requirement revision, record
  evidence and findings, and issue a revision-bound verdict.
---

# Review

Read [the shared playbook](../../PLAYBOOK.md), the active profile, repository
instructions, approved requirement revision, live Project item, and current PR
before reviewing.

## Trigger and independence

Run only when the user explicitly asks to run the Review loop. If the user
names a PR or issue, review it first; otherwise consider every live `In review`
item with a ready implementation PR.

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
5. Standard Architecture sign-off names the same requirement revision.

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

## Handoff and boundaries

- Never review your own implementation.
- Never expand or rewrite approved scope to match the code.
- Never create a replacement issue or PR for an ordinary fix cycle.
- Never treat `Accepted` as landed, released, deployed, or `Done`.
- Review owns the independent verdict, not delivery closeout. Requirements
  verifies landing, coverage, release evidence, issue closure, and Project
  `Done` on a separate explicit invocation.
