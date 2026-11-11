---
name: build
description: >
  On explicit user invocation, claim eligible Ready work from the authoritative
  GitHub Project, implement it in dedicated branches and worktrees, run the
  approved checks, and open or update implementation pull requests for a
  separate Review session.
---

# Build

Read [the shared playbook](../../PLAYBOOK.md), the executable
[lifecycle contract](../../contract.yaml), the repository
[manifest](../../workflow.yaml), the active profile, repository instructions,
and the approved requirement before changing state or code.

## Document organization

Follow the shared playbook's document organization and the repository policy.
For issue-centered repositories, read requirements and the concise four-entry
product sign-off from the canonical issue description. Read its Technical
design section: Standard uses the linked Git architecture/design document;
Lite uses any simple inline details and permits an empty section.
Compare the live requirements block with the approved
snapshot before claiming; do not trust an "Approved" label alone or recreate
approval, scope, or hashes in another document. Record the short Review handoff
as an issue comment, linking the exact tested PR head and detailed evidence.
Keep execution status, Action Owner, and claim in the Project.
For PO status work, apply the shared playbook's read-only PO status guidance:
decision-first output, metadata reuse with complete evidence, current approval
precedence, and one cohesive collector/utility/test slice. Verify the actual
read-only boundary, not just instruction wording.

## Trigger and assignment

Run only when the user explicitly asks to run the Build loop. This is not a
continuous scanner or background scheduler.

- If the user names an issue, consider it first.
- Then query the configured Project for every item whose live `Status` is
  `Ready` and `Action Owner` is `Build`.
- The invocation authorizes this session to attempt claims, not to bypass any
  gate. Process eligible items one at a time and continue until no eligible
  Ready work remains.
- Skip ineligible items and report the failed gate, responsible role, and
  resume condition. Do not move skipped work to `In progress`.

Before every Project mutation, follow the playbook's mandatory live preflight,
transition evaluation, and readback procedure. Build may evaluate only
`claim-build-work`, `handoff-for-review`, `block-work`, or
`resume-blocked-work`. Record Assignee and Claim Session only as effects of an
allowed `claim-build-work` decision. A denied decision means no write.

## Before every claim

Use `gh` to re-read the repository, Project, issue, native blockers, assignment,
branches, worktrees, and open PRs. Resolve field and option IDs from the live
Project; never hard-code IDs from another installation.

An item is eligible only when all applicable checks pass:

1. The Project status is still `Ready`.
2. One canonical requirements revision is linked and approved.
3. The active profile's gates pass. Standard Feature work requires its own
   current Feature sign-off. Standard Task work requires current parent Feature
   sign-off plus recorded architecture applicability: either `parent sign-off
   applies` or a current Task-specific sign-off bound to both revisions.
4. Every native blocker is `Done` with its required evidence. For a Task,
   verify its `Parent issue` link names the correct Feature and that the
   Feature's approved requirement revision is the one this Task's scope
   references.
5. No other active session, branch, worktree, or implementation PR owns the
   item. Existing work may be reused only under an explicit resume assignment.
6. Required GitHub reads and writes are available.

If a requirement revision changed after approval or Standard sign-off, refuse
the claim and return it to the responsible Requirements or Architect role.

## Claim and readback

For one eligible item at a time:

1. Assign the item to the current Build actor and record the Claim Session,
   branch, worktree, and any resumed PR on the issue or configured claim fields.
2. Move the Project status from `Ready` to `In progress` before editing code.
3. Keep `Action Owner: Build` and re-read assignment, claim, owner, and status.
   If any differs from the intended values, stop and reconcile the concurrent
   change; do not start coding.
4. Create a dedicated branch and worktree from the configured base revision.
   Reuse the existing branch and worktree only for an explicitly assigned
   resumption.

## Build and verify

Implement only the approved scope. Follow the repository's engineering and
test rules and run every check recorded in the requirement. Record exact
commands, results, and the tested commit.

If work needs a scope decision, record the question and resume condition, move
the item to `Blocked`, and continue with independent eligible Ready work. Send
scope questions to Requirements and Standard technical questions to Architect.
Before writing `Blocked`, set `Blocking reason` to a short phrase naming the
question and owner, and set `Resume Status` to `In progress`. Clear both when
the item is resumed.

If any required GitHub operation fails, stop affected work. Do not fall back to
Markdown status, fabricate a claim, or report a transition as successful.

## Required PR handoff

This handoff is mandatory for both Standard and Lite. After the implementation
and checks pass:

1. Commit the verified change and push the task branch.
2. Open an implementation PR against the configured base, or update the
   existing PR for an assigned review-fix resumption.
3. Link the intended PR from the canonical requirements issue's native
   Development relationship, selecting the PR repository for cross-repository
   links. Reuse an existing correct link; do not replace a competing session's
   link or publish private planning references in a public PR description.
4. Verify through GitHub readback that the PR is open, its head is the pushed
   tested commit, its base is correct, and the issue and evidence are linked.
   Read back the issue relationship and Project `Linked pull requests` field
   before handoff. A URL in Notes, a PR description, or a handoff comment is
   not proof of that native relationship; do not create a custom PR text field.
5. Save and read back a short issue-comment handoff with the PR URL, exact
   tested head, approved requirements location/revision, checks/evidence, and
   applicable design baseline. Standard requires the Git design revision and
   current applicable architecture evidence. Lite records its inline technical
   details, if any; an empty Technical design section is valid without a
   separate Git document, not-applicable rationale, or Architect gate.
6. Only after those readbacks succeed, evaluate `handoff-for-review` with
   verified `implementation-pr`, `native-pr-link`, and `required-checks`
   evidence, then move `In progress` to `In review`, set
   `Action Owner: Review`, and hand the PR to a separate Review session.

A local commit, an unpushed branch, a draft description without a PR, or a
failed PR write is not a review handoff. Keep the item `In progress`, or mark
it `Blocked` when a stopping condition exists, and report how to resume.
A missing or failed native link also prevents handoff even if the PR exists
and its checks pass. Never assert `native-pr-link` without live readback.

Expected successful output:

```text
Ready candidates: 3
Claimed: <issue URL>
Status: Ready -> In progress
Branch: <task branch>
Checks: passed
Pull request: <PR URL>
Native PR link: verified
Status: In progress -> In review
```

## Review fixes

When Review requests in-scope changes, an explicit Build invocation resumes the
same item, branch, and PR. Move it to `In progress`, address every blocking
finding, rerun affected checks, push the new commit, and verify the updated PR
head. Recheck the native issue/PR relationship and refresh the issue-comment
handoff for that head before evaluating `handoff-for-review`, then return it to `In review`.
The new head requires a fresh Review verdict.

## Boundaries

- Never review your own implementation.
- Never merge or enable auto-merge.
- Never move an item to `Done` or close its issue.
- Never create a replacement issue or PR for an ordinary fix cycle.
- Never expand scope to make the implementation match a finding.
- Never treat Accepted, landed, released, or deployed as synonyms.

The `closeout_owner` configured in [`workflow.yaml`](../../workflow.yaml)
performs eligible merge and verified closeout. Build never assumes that role.
