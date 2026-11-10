# Briefcase Repository Backlog Policy

Effective 2026-11-09, by explicit user decision.

## Authority

Use [GitHub Project #5](https://github.com/users/Tchunchun/projects/5) as the
only active Briefcase backlog. Its fields own execution status, priority, work
type, Action Owner, and review verdict. `Legacy Stage` is migration history
only. Card/issue discussion holds
coordination context. There is no parallel live Markdown backlog.

The source-code repository is `Tchunchun/the-briefcase`. It is public, while
the Project and the artifact repository are private. Keep private planning in
private `Tchunchun/thebriefcase-artifacts` issues or Project draft cards.
Do not publish private requirements to the public source repository without approval.
Existing issue-backed work stays linked to its existing issue.

Approved scope and verification stay in linked, revision-bound requirements
documents in the Git artifact repository: Feature PRDs and scoped Task documents.
Document readiness is not a second execution backlog.
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

The configured `backend: git` remains valid for requirements documents, decisions, release
notes, and historical artifacts. No `backend: github` was introduced; the
framework does not yet have a native GitHub Projects storage adapter.
Consumer templates, supported backends, and other repositories are unchanged.

## Standard Board Contract

Status is the execution axis: Inbox, Requirement shaping, Technical shaping,
Ready, In progress, In review, Blocked, Done. `Action Owner` is the dispatch
authority: Requirements, Architect, Build, Review, or None. `Legacy Stage` is
retained only as historical migration metadata; automation must never dispatch
from it. Review Verdict is Pending, Accepted, Changes requested, or Blocked.

Requirements owns product scope and approval. Architect owns technical shaping
and revision-bound sign-off. Ready requires approved scope, current applicable
sign-off, satisfied dependencies, and no competing implementation claim. Build
records Assignee and Claim Session atomically when moving Ready to In progress;
assignment is not a prerequisite for Ready. All implementation requires
separate-session review. Historical acceptance is not current-revision
acceptance or verified landing. Done additionally requires full scope coverage,
intended-base landing, and applicable Standard release evidence.

Normal ownership is deterministic: Inbox and Requirement shaping belong to
Requirements; Technical shaping to Architect; Ready and In progress to Build;
In review to Review; Done to None. Blocked records an explicit Action Owner and
Resume Status. There is no Deliver stage or agent.

Closeout ownership is selected only by
[`workflow-kit/workflow.yaml`](../workflow-kit/workflow.yaml); this repository
adds gates but does not redefine the owner. The configured owner is Review.

Feature architecture covers the approved parent revision, cross-cutting
approach, child boundaries, interfaces, NFRs, risks, and release obligations.
A child Task must record either `parent sign-off applies` or a Task-specific
sign-off bound to both the parent and Task revisions. Task-specific sign-off is
required when the slice adds or changes a technical decision, interface,
dependency, NFR, approach assumption, release obligation, or unresolved
technical question.

A Task reaches Done independently when its approved slice is accepted on the
exact head, required checks and dependencies pass, landing is verified, and its
allocated release obligations are complete. A Feature reaches Done only when
all required child slices are Done or explicitly covered, Feature acceptance
passes, landing is complete, and applicable version, release-note, environment,
and readiness evidence is complete.

### Required Project fields

| Field | Type | Purpose |
|---|---|---|
| Status | single select | Lifecycle position and queue column |
| Action Owner | single select | Requirements, Architect, Build, Review, or None; automation dispatch authority |
| Assignees | native people field | Human or service account that accepted the work |
| Claim Session | text | Session ID, timestamp, branch, worktree, and PR reference |
| Resume Status | single select | Required for Blocked; the status whose gates must be revalidated |
| Review Verdict | single select | Pending, Accepted, Changes requested, or Blocked |
| Work Type | single select | Idea, Feature, or Task |

Status transitions update Action Owner in the same operation sequence and read
both fields back. A mismatch between Status and Action Owner is a blocker, not
permission to guess the intended owner.

### Executable contract and preflight

[`workflow-kit/contract.yaml`](../workflow-kit/contract.yaml) is the
machine-readable transition authority. The Markdown policy and role skills may
add repository-specific safety detail but must not contradict its statuses,
owners, transitions, or evidence gates. Repository instance names live in
[`workflow-kit/workflow.yaml`](../workflow-kit/workflow.yaml); it contains no
credentials, GitHub IDs, item state, claims, verdicts, or delivery evidence.

Run `python3 workflow-kit/runtime.py --offline` after editing either file. Run
the live, read-only `python3 workflow-kit/runtime.py` before the first named
pilot, after Project schema changes, and whenever drift is suspected. A failed
preflight blocks affected workflow operations. It never authorizes field
creation, option renaming, backlog conversion, or any other repair mutation.

Immediately before a role changes Status, Action Owner, Resume Status, Review
Verdict, Assignee, or Claim Session, it must reread the live item and pass the
corresponding transition through `workflow-kit/runtime.py --transition ...`
with live preflight enabled. Preserve the decision with the evidence packet,
perform only the evaluated write, and read every changed field back. A denied
decision, missing gate, preflight failure, or readback mismatch blocks the
mutation; `--offline` is never sufficient for a live Project write.

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
- A Requirements invocation remains owned by Requirements. Already approved
  Standard work is handed to Architect rather than silently changing roles.
- With no target, read all pages of Technical shaping cards owned by Architect, capture
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
3. Use the configured Git artifact transport for requirements documents and history; keep linked
   PRDs/task documents at their established authoritative locations. Preserve
   existing sections and revision history. The Project alone owns execution
   status; a requirements document's readiness field is not a parallel backlog.
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
   Check existing claims, branches and PRs. Do not overwrite another session's
   claim. Build records assignment when it later claims Ready.

### Readiness and handoff

| Evidence | Status | Action Owner | Next action |
|---|---|---|---|
| Approved scope awaits technical review | Technical shaping | Architect | Resolve technical questions and record sign-off. |
| Missing approval or a material scope gap | Blocked | Requirements | Request the missing product decision and record Resume Status. |
| An unresolved technical decision prevents progress | Blocked | Architect | Record the decision owner and Resume Status. |
| A dependency, access failure, or conflicting claim prevents progress | Blocked | Explicit responsible role | Record the unblock condition and Resume Status. |
| Approved revision, current sign-off, satisfied dependencies, and no competing claim | Ready | Build | Save the handoff packet and offer the exact Build prompt; stop. |

Do not move In progress, In review, or Done work back to shaping
on a sweep.
For explicitly targeted scope changes to active work, coordinate with its
current owner, preserve implementation/review history, and invalidate only
evidence affected by the new revision. Resolving a blocker does not itself
make work Ready: recheck every gate.

Before any mutation, reread the target's status, Action Owner, requirement revision,
approval, dependencies, and existing claims. Refresh or report concurrent changes rather than
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
Action Owner: <Requirements | Architect | Build | Review | None>
Assignment: <existing assignee/claim/branch/PR, or unassigned>
Readiness: <each gate, remaining blockers, owner and unblock condition>
Next action: <technical decision request, product clarification, or exact Build prompt>
```

Save and read back the packet before field updates. Set Ready last, only after
all gates pass, and read back the saved evidence and final Status/Action Owner. Do not
set Review Verdict to Accepted for requirements approval. Access or partial-write
failures pause affected work: report which writes succeeded and which remain;
there is no legacy inbox/backlog fallback. Reruns reuse current packets when
their scope revision and gates remain valid, appending only new evidence rather
than duplicating records.

Finish with one result per target: authoritative scope revision, approval and
architecture state, dependencies, assignment, verified Status/Action Owner, remaining
decision/owner, and next prompt. Stop at this handoff. Do not start implementation,
merge, release, or close issues as part of the technical shaping loop.

## Repository Review Loop

This is the user-authorized review and closeout procedure for this repository's
Standard board. Review owns the verdict, merge, landing verification, task
closure, and final Done transition. There is no separate Deliver stage.

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
   In review / Review / Accepted, record the queue/CI gate, and stop until
   GitHub confirms the merge. If the operation is rejected, report the actual
   reason and owner; never substitute issue closure for a failed merge.
5. Read back merged state, merge/landed revision, and intended base, and verify
   that the accepted changes landed. Recheck full item coverage and applicable
   post-merge release evidence before closeout. If delivery must happen after
   merge, keep the task open until that gate passes. For multiple required PRs,
   verify every required landing before closing the item.

### Outcomes and completion gates

| Evidence | Status | Action Owner | Review Verdict | Action |
|---|---|---|---|---|
| Current revision passes review; accepted work not yet landed | In review | Review | Accepted | Merge the eligible PR, verify landing, and continue closeout. |
| Accepted work landed, but required release evidence is pending | In review | Review | Accepted | Keep the task open and record the missing evidence owner. |
| Fixable implementation findings within approved scope | In progress | Build | Changes requested | Record findings and hand back the existing branch/PR. |
| Missing scope approval, implementation/PR evidence, required checks, independent review, or landing proof | Blocked | Review | Blocked | Record the missing evidence, responsible owner, and explicit unblock condition. |
| Only part of the item landed | In progress if remaining work is assigned; otherwise Blocked | Build | Pending | Keep the issue open and identify uncovered criteria and the next owner. |
| Full scope accepted, checks/dependencies satisfied, landing verified, and applicable release evidence present | Done | None | Accepted | Close the linked task and verify final state. |

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
with reason **completed**, and update Review Verdict, Action Owner, and Status to
**Accepted**, **None**, and **Done**, setting Done last. Draft cards have no
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

On 2026-11-10 the user approved the explicit ownership model in this policy.
Requirement shaping and Technical shaping are separate statuses; Action Owner
is the dispatch authority; Architect remains the technical authority; Build
claims assignment during Ready to In progress; Review merges and closes without
a Deliver stage. This supersedes earlier assignment-before-Ready and
Requirements-owned-closeout text. Live Project migration is a separate verified
operation: add the required fields, map existing cards, read back every value,
and only then remove or retire legacy Stage-based dispatch.

### Pending live Project reconciliation

The repository contract in this PR does not by itself mutate Project #5. On
2026-11-10 the live Project README and schema were reconciled to the eight
Status values, deterministic Action Owner mapping, Build claim-at-Ready rule,
Review closeout ownership, and absence of a Deliver stage. `Shaping` retained
its option ID and was renamed `Technical shaping`; `Requirement shaping`,
`Action Owner`, `Claim Session`, and `Resume Status` were added. `Stage` was
renamed `Legacy Stage` so it cannot be mistaken for dispatch authority.

Legacy cards must not be promoted merely because their former blocker text is
stale. Re-evaluate their current requirement revision, architecture
applicability, dependencies, claim, PR head, verdict, and landing evidence;
record the correct Status, Action Owner, Resume Status, and Review Verdict. Keep
the old body/history as evidence and append one reconciliation note rather than
rewriting provenance. The migration is complete only when no active card relies
on Legacy Stage for dispatch and a fresh board query reports no Status/Action Owner
mismatches.

The stale draft cards `Review Merge and Close Verified Work` and `Prepare
Standard Requirements Before Building` were reconciled to `Done / None /
Accepted` using independently reviewed PR #27, exact reviewed head
`8889a20f3c536f4226bdfd61869108bdfb1488e7`, and landed main revision
`b3b7aa14f7d9271b6596ac723e45466f5d6ab43c`. Their historical bodies remain
unchanged and the immutable reconciliation evidence is recorded in Notes.
