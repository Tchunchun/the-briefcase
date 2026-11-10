# Briefcase Repository Backlog Policy

Effective 2026-11-09, by explicit user decision.

## Authority

Use [GitHub Project #5](https://github.com/users/Tchunchun/projects/5) as the
only active Briefcase backlog. Its fields own execution status, priority, work
type, stage, and review verdict. Card/issue discussion holds coordination
context. There is no parallel live Markdown backlog.

The source-code repository is `Tchunchun/the-briefcase`. It is public, while
the Project and the artifact repository are private. Keep private planning in
private `Tchunchun/thebriefcase-artifacts` issues or Project draft cards.
Do not publish private requirements to the public source repository without
approval. Existing issue-backed work stays linked to its existing issue.

Approved scope and verification stay in linked briefs in the Git artifact
repository. Brief document readiness is not a second execution backlog.
Code, implementation revisions, and merge evidence remain in Git and PRs.

## Repository-Specific Override

This policy overrides generic playbook and role instructions that would use
the Briefcase CLI to read/write backlog rows, capture new work in the legacy
inbox, or derive dispatch from the Markdown backlog in THIS repository.

- Search the live Project before creating new work. Reuse matching cards.
- Capture new ideas, tasks, feedback, and blockers in the Project.
- Read and update Project fields directly with authenticated GitHub tooling.
- Keep review acceptance distinct from shipment. Migration did not authorize
  promotion, completion, or implementation of any item.
- Do not run `backlog upsert`, recreate a Markdown table, or dispatch from
  `automate` commands that scan the retired local backlog.
- `backlog list` is not a GitHub query. Its empty local result is not proof
  that the live backlog is empty.
- Report access or update failures explicitly and pause affected work. Never
  silently switch status authority to a local file.

The configured `backend: git` remains valid for briefs, decisions, release
notes, and historical artifacts. No `backend: github` was introduced; the
framework does not yet have a native GitHub Projects storage adapter.
Consumer templates, supported backends, and other repositories are unchanged.

## Standard Board Contract

Status is the sole execution axis: Inbox, User requirement shaping, Technical
shaping, Ready, In progress, In review, Blocked, Done. Stage is Requirements,
Architecture, Build, Review, or Deliver. Review Verdict is Pending, Accepted,
Changes requested, or Blocked.

User requirement shaping owns user needs, scope, acceptance criteria, and
product approval. Technical shaping owns the technical approach, applicable
architecture sign-off, and remaining Build readiness gates. Stage identifies
the current role within those phases; splitting Shaping does not waive any
Ready gate or change Lite's workflow.

Ready requires approved scope, applicable architecture sign-off, satisfied
dependencies, and an accepted assignment. All implementation requires
separate-session review. Historical acceptance is not current-revision
acceptance or verified landing. Done additionally requires full scope coverage,
intended-base landing, and applicable Standard release evidence.

Use native parent/sub-issue and blocked-by relationships for issue-backed work.
Legacy Status, Legacy Lane, Legacy Review Verdict, and Legacy Route State are
migration history only. No auto-close-to-Done rule is enabled.

## Repository Review Loop

This is the user-authorized review and closeout procedure for this repository's
Standard board. It overrides generic role instructions that reserve Done for
Implementation or the product session. It does not change installed consumer
workflows, Lite ownership, or unresolved unified-product decisions.

### Entry and authority

- **"Run the review loop"** means inspect all **In review** cards on the active
  Project, including private draft cards. Read every result page; do not treat
  the first page as the complete queue. Process each item independently and
  stop when the captured queue has been assessed, rather than continuously
  polling for new work.
- **"Run the review loop for PR #123"**, an issue URL, or a Project card
  identifies a single target. Resolve its repository and linked board item;
  never guess from an issue number shared by public and private repositories.
  Do not sweep unrelated items when a target is supplied.
- The reviewer must be a session separate from implementation. A session
  that implemented an item hands it off instead of accepting or closing it.
  Historical review notes are context, not acceptance of the current revision.
- Invoking this loop authorizes recording the verdict and closeout evidence,
  updating that item's Project fields, merging its passing PR under the gates
  below, and closing its issue **only when all completion gates below pass**.
  A normal review-loop run is action-enabled: after a pass, merge and close out
  eligible work without requesting another manual handoff or confirmation.
  An explicitly read-only review reports the proposed actions without writes.
  This does not authorize implementation fixes, scope changes, releases,
  protection bypasses, or publication of private planning.
  Product owns scope; Build owns fixes and delivery artifacts; Review owns
  the verdict and verified closeout.
- Use authenticated GitHub tooling directly. Read the current board field
  IDs/options instead of hard-coding them. Access failures pause affected work
  and must be reported; there is no local execution-status fallback.
  With `gh project item-edit`, field updates use the Project item ID (`PVTI_`),
  while draft-body updates use the content ID (`DI_`) and must also supply the
  unchanged title. Resolve both from GitHub and preserve the existing body.

### Review each item

1. Read the card, issue discussion, approved requirement revision, dependencies,
   and existing review/delivery evidence. Treat requirement changes since an
   old acceptance as new scope needing review. Do not review a new PRD as if
   it had already been approved.
2. Resolve implementation evidence. Follow recorded PRs and commits, then
   search the source repository's open, merged, and closed PRs if links are
   missing. Match actual changes to the approved scope, not merely a similar
   PR title. Record verified PR links on the private card. A private draft
   needs no new public issue to be reviewed or completed.
3. Review the exact implementation revision against every acceptance criterion,
   using the Review skill's quality checks. Record the base, reviewed SHA,
   criterion-by-criterion evidence, required check results, and blockers.
   Missing or unperformed required checks prevent acceptance. Reuse earlier
   evidence only after verifying its revision and scope are still applicable.
4. Verify landing separately from acceptance. For a passing open PR, follow
   **Merge a passing PR** below rather than stopping at an Accepted verdict.
   For a merged PR, confirm its intended base and that the accepted changes
   actually landed; accommodate squash/rebase merges by comparing the landed
   changes, not just original commit ancestry. A closed-unmerged PR is not
   landing. For work integrated without a PR, require a recorded implementation
   revision, independent review, and equivalent evidence on the intended base.
   No PR alone is neither proof of completion nor proof that work is unfinished.
5. Check full item coverage, required dependencies, and applicable Standard
   release/version records. A partial PR cannot complete a larger issue.
   Never close a parent simply because one child finished. Record why a release
   gate is not applicable when no release is required; do not invent evidence
   or publish a release as part of review.
6. Choose the outcome below. Before any mutation, reread the target's status,
   scope revision, PR head, and landing evidence. If they changed during review,
   refresh the review or report the conflict rather than overwriting newer work.

### Merge a passing PR

1. Require full approved item coverage, independent acceptance of the exact PR
   head, satisfied dependencies, and all applicable pre-merge delivery gates.
   Read the live PR's head and intended base, draft state, mergeability, required
   CI checks, eligible approvals, unresolved conversations, and branch
   protections/rulesets. Pending, failed, missing, or stale required evidence is
   not a pass. A green local test run alone cannot substitute for required CI
   or another eligible account's approval. Leave blocked work open with its
   owner and unblock condition.
2. Save the review evidence before merging. Check automatic issue-closing
   references: merging must not prematurely close a larger, partially delivered,
   or release-gated issue. Resolve that gate or have Build correct the closing
   references before merge. Do not waive scope or release requirements merely
   to close the task.
3. Reread the approved scope revision and PR head immediately before merge.
   Use an expected-head guard such as `gh pr merge --match-head-commit` with the
   reviewed SHA so a concurrent push cannot slip into the merge. A changed
   head requires renewed review; do not retry against an unreviewed revision.
   Use the documented repository merge strategy. If none is documented, prefer
   an enabled squash merge, then an enabled merge commit, then an enabled
   rebase merge; if none is permitted, report the blocker. Never use `--admin`,
   disable protections, force-push, resolve conflicts, or manufacture approval
   to get a merge through.
4. Perform the merge through authenticated GitHub tooling without another
   confirmation once these gates pass. Respect any required merge queue. A
   queued merge or enabled auto-merge is not a completed merge: keep the task
   In review / Deliver / Accepted, record the queue/CI gate, and stop until
   GitHub confirms the merge. If the operation is rejected, report the actual
   reason and owner; never substitute issue closure for a failed merge.
5. Read back merged state, merge/landed revision, and intended base, and verify
   that the accepted changes landed. Recheck full item coverage and applicable
   post-merge release evidence before closeout. If delivery must happen after
   merge, keep the task open until that gate passes. For multiple required PRs,
   verify every required landing before closing the item.

### Outcomes and completion gates

| Evidence | Status | Stage | Review Verdict | Action |
|---|---|---|---|---|
| Current revision passes review; accepted work not yet landed | In review | Deliver | Accepted | Merge the eligible PR under the merge gates, verify landing, then continue closeout; if queued or gated, record the remaining action and keep the issue open. |
| Accepted work landed, but required release evidence is pending | In review | Deliver | Accepted | Hand the missing delivery action to Build; keep the issue open. |
| Fixable implementation findings within approved scope | In progress if a fix owner is assigned; otherwise In review | Build if assigned; otherwise Review | Changes requested | Record actionable findings and hand back the existing branch/PR; do not implement fixes in the reviewer session. |
| Missing scope approval, implementation/PR evidence, required checks, independent review, or landing proof | Blocked | Review | Blocked | Record the missing evidence, responsible owner, and explicit unblock condition. |
| Only part of the item landed | In progress if remaining work is assigned; otherwise Blocked | Build | Pending | Keep the issue open and identify uncovered criteria and the next owner. |
| Full approved scope independently accepted at the verified revision, required checks/dependencies satisfied, intended-base landing verified, and applicable release evidence present | Done | Deliver | Accepted | Record closeout evidence, close the linked issue if any, and verify the final board state. |

The normal passing path is **review -> merge -> verify landing/delivery -> close
issue and mark Done**. An accepted PR remains In review only while a merge,
integration, or delivery gate is pending; never merge it just to empty the column.
If there is no authorized work left to review, report an empty queue without
inventing a task. Do not fabricate a PR, a new acceptance, or a release record
to reconcile a legacy card.

### Record and verify closeout

Before completing an item, persist this packet in its private issue discussion
or draft-card body, preserving existing content and historical notes:

```text
Review closeout: <timestamp with timezone>
Item: <Project card and issue URL, if any>
Approved scope: <requirement link and revision>
Reviewed implementation: <PR URL(s), base, reviewed SHA(s)>
Acceptance evidence: <each criterion, checks/results, independent reviewer>
Merge evidence: <expected head, method, result or queue/blocker>
Landing evidence: <intended base and landed revision(s)>
Release evidence: <required records, or reason not applicable>
Coverage and dependencies: <full coverage and satisfied prerequisites>
Verdict: <Accepted / Changes requested / Blocked / Pending for remaining scope>
Next action: <closeout, delivery gate, fix owner, or unblock condition>
```

Keep private scope and evidence in the private planning repository/Project.
Any comment on a public implementation PR or issue must contain only
public-safe implementation facts, not private requirement text or links.

For eligible completion, first save the packet, merge any eligible open PR and
verify its landing and delivery gates, then close an open linked issue
with reason **completed**, and update Review Verdict, Stage, and Status to
**Accepted**, **Deliver**, and **Done**, setting Done last. Draft cards have no
issue to close. An already-closed issue still requires all gates; its closed
state is not completion evidence. If it was closed as not planned, report the
conflict for resolution rather than silently treating it as completed or
reopening it. Read back the saved packet, issue state/close
reason where applicable, and all three board fields before reporting success.
If any write fails, report precisely which writes succeeded and which remain;
do not claim Done or silently fall back to Markdown. On rerun, inspect existing
evidence and finish only the missing verified updates without duplicating
closeout records or reopening completed issues.
If merge succeeded but issue/board updates failed, preserve and report that
landing; do not attempt to merge again or roll back the merge on rerun.

Finish with one result per item: verdict, final status, implementation/landing
links, checks, merge result or queue state, whether its issue was closed, and
remaining blocker/owner. Rerun **"Run the review loop"** to verify a queued merge
or finish accepted work after a pending delivery gate is resolved.

## Migration Record

[Project #4](https://github.com/users/Tchunchun/projects/4) is closed historical
evidence. Project #5 alone owns current execution state. Existing issue
identities and private draft content were preserved; migration did not approve
scope or certify delivery. Legacy fields are historical, not workflow gates.
