# Staged handoff examples

These examples use the shared evidence packets. They demonstrate decisions;
they are not a second status queue.

Follow the shared playbook's document organization and repository policy.
In issue-centered repositories, these short handoffs are issue comments linking
the approved issue scope and Git design; no separate living handoff file is
needed. Product sign-off stays concise and its immutable evidence stays linked.

## Happy path

Requirements records the user's approval of revision `req-abc123` and moves the Feature to
`Technical shaping / Architect`. Architect signs that revision, verifies Done
dependencies and no competing implementation, then moves it to `Ready / Build`.
Build atomically records assignment and Claim Session while moving it to
`In progress`, implements in a dedicated worktree, and hands off PR head
`def456` as `In review / Review`. A separate Review session accepts `def456`,
merges it, verifies landing and release evidence, closes the task, and writes
`Done / None` last.

## Refused self-review

Session `build-7` produced PR head `def456` and is then asked to review it.
Result: refuse the verdict. Keep the item `In review` and require a separate
Review session. This applies even when the item is a bug or tech-debt change.

## Refused missing approval

The issue links requirement draft `req-abc123`, but no user approval record
exists. Result: do not move to `Ready` and do not claim Build work. Keep the
Lite item in `Requirement shaping`; for Standard, record `Blocked` with
`Action Owner: Requirements`, `Resume Status: Technical shaping`, and the
approval evidence needed to resume.

## Refused competing ownership

An item is `Ready`, but branch `task-one` and an open PR are already claimed by
session `build-2`. Result: a different session does not create another branch,
worktree, or PR. It skips the claim until an explicit resume assignment or
release of the existing claim is recorded and verified.
