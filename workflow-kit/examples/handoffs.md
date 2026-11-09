# Staged handoff examples

These examples use the shared evidence packets. They demonstrate decisions;
they are not a second status queue.

## Happy path

Requirement `req-abc123` is approved. Standard Architect signs `req-abc123`,
all blockers are Done, and session `build-7` has no competing branch or PR.
Build records its claim, reads back `In progress`, implements in a dedicated
worktree, and hands off PR head `def456`. A separate Review session accepts
`def456` against `req-abc123`. Requirements later verifies that `def456` landed
on the intended base with complete checks, scope coverage, and Standard release
evidence before closing the issue and reading back Project `Done`.

## Refused self-review

Session `build-7` produced PR head `def456` and is then asked to review it.
Result: refuse the verdict. Keep the item `In review` and require a separate
Review session. This applies even when the item is a bug or tech-debt change.

## Refused missing approval

The issue links requirement draft `req-abc123`, but no user approval record
exists. Result: do not move to `Ready` and do not claim Build work. Keep the
item `Shaping` or record a blocker owned by Requirements with the approval
evidence needed to resume.

## Refused competing ownership

An item is `Ready`, but branch `task-one` and an open PR are already claimed by
session `build-2`. Result: a different session does not create another branch,
worktree, or PR. It skips the claim until an explicit resume assignment or
release of the existing claim is recorded and verified.
