# Briefcase Repository Backlog Policy

Effective 2026-11-09, by explicit user decision.

## Authority

Use [GitHub Project #5](https://github.com/users/Tchunchun/projects/5) as the
only active Briefcase backlog. Its fields own execution status, priority, work
type, stage, and review verdict. Card/issue discussion holds
coordination context. There is no parallel live Markdown backlog.

The source-code repository is `Tchunchun/the-briefcase`. It is public, while
the Project and the artifact repository are private. Keep private planning in
private `Tchunchun/thebriefcase-artifacts` issues or Project draft cards.
Do not publish private requirements to the public source repository without approval.
Existing issue-backed work stays linked to its existing issue.

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

Feature creation includes user needs, scope, acceptance criteria, and product
approval. Added Standard features proceed directly to Technical shaping, then
implementation; they do not repeat requirement shaping. Technical shaping owns
the technical approach, applicable architecture sign-off, and remaining Build
readiness gates. The existing User requirement shaping option is historical or
exception-only, not a mandatory phase. Do not bulk-move existing cards or change
board options merely to apply this policy. No Ready gate or Lite behavior changes.

Ready requires approved scope, applicable architecture sign-off, satisfied
dependencies, and an accepted assignment. All implementation requires
separate-session review. Historical acceptance is not current-revision
acceptance or verified landing. Done additionally requires full scope coverage,
intended-base landing, and applicable Standard release evidence.

Use native parent/sub-issue and blocked-by relationships for issue-backed work.
The unified initiative is public source issue #18; detailed feature/task issues
remain private. A private parent/child reference is not permission to publish
its content. Legacy Status, Legacy Lane, Legacy Review Verdict, and Legacy
Route State are migration history only. No auto-close-to-Done rule is enabled.

<a id="repository-requirements-loop"></a>

## Repository Technical Shaping Loop

This is the Architect entry point for this repository's Standard board,
not an implementation of the proposed unified workflow or a change to installed
consumer/Lite instructions. It overrides legacy ideation/architect automation
that would promote backlog rows or continue directly into Build.

### Entry and authority

- **"Run the technical shaping loop for <topic>"**, **"Run the architecture loop"**,
  an issue URL, or a Project card
  targets that work only. Resolve the repository and card; never infer public
  versus private ownership from an issue number alone. Search all result pages
  for existing scope, children, dependencies, and competing work before creating
  anything. Reuse matching items rather than duplicating them.
- **"Run the requirements loop"** is a compatibility alias for this Standard
  technical shaping loop. It must not restart product shaping for an added feature.
- With no target, read all pages of Inbox and Technical shaping cards, capture
  that queue once, and process eligible features against their existing approved
  scope. Report missing evidence and decisions. Do not select or approve unrelated scope,
  continually poll, or claim every card as assigned work.
- Read the current card/issue discussion, linked requirements and their
  revisions, approved amendments, product decisions, and relevant implementation.
  An older brief is provenance when an approved PRD supersedes it. Record one
  authoritative requirement reference and precedence; conflicting sources block
  readiness rather than being silently reconciled.
- Product owns problem, scope, acceptance criteria, verification intent,
  and approval at feature creation. Architect reuses that evidence rather than
  rewriting or reapproving it, and owns technical approach and sign-off.
  Build owns implementation and evidence; a separate Review session accepts
  the implementation revision. Requirements approval is not Review acceptance,
  shipment, or permission to close an issue.
- A request to prepare work authorizes shaping and recording proposals, not
  inventing product approval or approving unrelated decisions. Record explicit
  user approval against the exact scope revision; preserve unresolved decisions
  with their owner and unblock condition.

### Reuse approved scope and shape the technical approach

1. Locate the feature's authoritative approved immutable revision and approval
   record. Read its scope, criteria, constraints, and preserved behavior; do not
   redraft them. Feature creation is the product-shaping boundary, not permission
   to infer approval when its evidence is missing.
2. Inspect relevant implementation and architecture. Define the technical
   approach, interfaces, dependencies, risks, and implementation breakdown.
   Map existing criteria and NFRs to concrete checks, expected results, and
   environments without changing product intent. Split independently deliverable
   work into linked children referencing the approved parent scope.
3. Use the configured Git artifact CLI for briefs and history; keep linked
   PRDs/task documents at their established authoritative locations. Preserve
   existing sections and revision history. The Project alone owns execution
   status; a brief's document-readiness field is not a parallel backlog.
   Keep private requirements and approval evidence in the private artifact
   repository or Project, never in public implementation issues or PRs.
4. Reuse approval identity/date and the approved immutable revision. Only missing,
   contradictory, or materially changed requirements need product clarification:
   record the exact gap, owner, and unblock condition without restarting full
   requirement shaping. A later material scope change needs renewed
   approval and applicable technical sign-off; do not reuse stale evidence.
5. Architect records sign-off against the approved revision, or an explicit reason that
   architecture is not applicable. A legacy lane alone cannot waive a required
   Standard gate or the separate-session implementation review.
6. Resolve dependencies from their authoritative cards and verify Done evidence.
   Record the intended owner/session and its accepted assignment, checking
   existing claims, branches and PRs. Do not overwrite another session's claim
   or mistake a suggested Build prompt for an accepted assignment.

### Readiness and handoff

| Evidence | Status | Stage | Next action |
|---|---|---|---|
| Added feature has approved scope and awaits technical review | Technical shaping | Architecture | Reuse the approved revision and resolve technical questions; do not repeat requirement shaping. |
| Missing approval or a material scope gap | Blocked | Requirements | Request only the missing product decision and revision-bound evidence; no Build dispatch. |
| Approval/sign-off complete, but no accepted assignment | Technical shaping | Build | Offer the exact target and prerequisites; do not claim Ready. |
| An unresolved decision, dependency, access failure, or conflicting claim prevents progress | Blocked | Stage where blocked | Record responsible owner and explicit unblock condition. |
| Approved revision, applicable sign-off, satisfied dependencies, and accepted assignment verified | Ready | Build | Save the handoff packet and offer the exact Build prompt; stop. |

Do not move In progress, In review, or Done work back to shaping
on a sweep.
For explicitly targeted scope changes to active work, coordinate with its
current owner, preserve implementation/review history, and invalidate only
evidence affected by the new revision. Resolving a blocker does not itself
make work Ready: recheck every gate.

Before any mutation, reread the target's status, requirement revision, approval,
dependencies, and assignment. Refresh or report concurrent changes rather than
overwriting newer work. Resolve current Project field IDs/options from GitHub.
For drafts, field edits use the Project item ID (`PVTI_`); body edits use the
content ID (`DI_`) and preserve the title and existing body.

Persist this packet in the private issue discussion or draft-card body:

```text
Technical shaping handoff: <timestamp with timezone>
Item: <Project card and issue URL, if any>
Scope: <authoritative requirement link and immutable revision; precedence>
Approval: <product owner, date, exact approved revision, or pending>
Verification: <criterion-to-check mapping, expected results, environment>
Architecture: <sign-off and revision, justified not applicable, or open questions>
Dependencies: <linked cards, verified completion evidence, or explicit none>
Assignment: <accepted owner/session and existing branch/PR, or unassigned>
Readiness: <each gate, remaining blockers, owner and unblock condition>
Next action: <technical decision request, product clarification, or exact Build prompt>
```

Save and read back the packet before field updates. Set Ready last, only after
all gates pass, and read back the saved evidence and final Status/Stage. Do not
set Review Verdict to Accepted for requirements approval. Access or partial-write
failures pause affected work: report which writes succeeded and which remain;
there is no legacy inbox/backlog fallback. Reruns reuse current packets when
their scope revision and gates remain valid, appending only new evidence rather
than duplicating records.

Finish with one result per target: authoritative scope revision, approval and
architecture state, dependencies, assignment, verified Status/Stage, remaining
decision/owner, and next prompt. Stop at this handoff. Do not start implementation,
merge, release, or close issues as part of the technical shaping loop.

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
   For a merged PR, confirm its
   intended base and that the accepted changes actually landed; accommodate
   squash/rebase merges by comparing the landed changes, not just original
   commit ancestry. A closed-unmerged PR is not landing. For work integrated
   without a PR, require a recorded implementation revision, independent
   review, and equivalent evidence on the intended base. No PR alone is
   neither proof of completion nor proof that the work is unfinished.
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

All five nonterminal rows in the Markdown table were matched to existing
private Project cards. Their work type, status, priority, brief links, notes,
and existing review/routing metadata were preserved. Original row data is
included in each migrated card as explicitly historical migration evidence.
No new cards or public issues were required.

The source table contained four open Features, one exploring Idea, and 190
completed rows (63 Features and 127 Tasks). It contained no unfinished Task
rows. Other GitHub-only work was left intact.

The complete table is retained in the
[read-only snapshot](../docs/plan/_shared/archive/backlog-before-github-2026-11-09.md).
The [former backlog path](../docs/plan/_shared/backlog.md) now only redirects
to GitHub. Completed history and the legacy inbox are not active queues.

On 2026-11-09 the user requested a new Standard board and migration of Project
#4. All 26 source items were preserved with source-to-target identifiers,
historical fields, requirement links, and mapped relationships. Source issue
identities were reused; private draft content stayed private. The user's
conversion of the unified initiative into source issue #18 was preserved.
The contradictory implementation-ready feedback issue was mapped to Shaping;
accepted legacy items remain In review, never implicitly Done.
The initiative's concurrent requirements-review update was also preserved:
it remains Blocked pending product decisions and technical sign-off. Its
candidate coding handoff is not an approval or a second backlog.

[Project #4](https://github.com/users/Tchunchun/projects/4) is closed historical
evidence. The source snapshot and ID map are retained in the private artifact
repository under `docs/plan/_shared/archive/`. Preparing new PRD tasks does not
approve open product decisions or complete the reusable migration feature.

On 2026-11-09 the user requested splitting Standard's Shaping column into
User requirement shaping and Technical shaping. All three existing Shaping
cards were at Stage Architecture and retained their existing status option ID,
renamed Technical shaping. User requirement shaping was inserted immediately
before it. Other status option IDs, card fields, and Lite behavior were
preserved.
