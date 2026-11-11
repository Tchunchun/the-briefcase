# Briefcase Workflow Kit

This directory is the additive source for the new GitHub-first Briefcase
product. It is not an installed workflow by itself. The existing `install.sh`,
`src/`, `skills/`, `template/`, and `lite/` paths are legacy and must remain
behaviorally unchanged unless a separately approved migration says otherwise.

## Repository bootstrap boundary

The Briefcase repository may build this kit without using the kit on that same
work. During its bootstrap phase, requests to build, repair, document, or test
`workflow-kit/` are ordinary repository development unless the user explicitly
says **"Use Standard mode for <target>"**, **"Use Lite mode for <target>"**, or
invokes a named role or loop. Words such as "build", "implement", "fix", or
"review", and an issue or Project link on their own, do not activate a profile
or role.

Bootstrap work continues to use the repository's authoritative GitHub Project
and normal code safeguards; this boundary is not permission to create a second
backlog or bypass tests and PR protections. Dogfooding is prospective and
target-specific. It begins only on explicit activation for named pilot work and
does not retroactively apply workflow evidence or transitions to existing kit
development. The repository backlog policy controls the exact bootstrap scope;
consumer repositories are unaffected.

## Product contract

- Users invoke Requirements, Architect (Standard only), Build, and Review
  directly. There is no background scheduler or automatic role orchestration.
- GitHub Issues identify work and hold discussion.
- The configured GitHub Project `Status` field is the only execution state.
  Never create or consult a competing Markdown status queue.
- The Project `Action Owner` field is the automation dispatch authority. Status
  describes lifecycle position; Action Owner names the role that must act next.
- Each item links exactly one approved requirements revision. Lite uses a
  concise task document. Standard uses a Feature PRD and Task scope linked to
  that approved parent revision.
- Review must run in a session separate from the Build session and bind its
  verdict to both the approved requirements revision and the exact PR head.
- [`contract.yaml`](contract.yaml) is the executable lifecycle authority for
  statuses, owners, legal transitions, and required evidence. This playbook and
  the role skills explain that contract but must not redefine it.
- [`workflow.yaml`](workflow.yaml) is the single configuration point for the
  repository, Project field names, profile, artifact location, merge strategy,
  and closeout owner. It stores names, not credentials, GitHub IDs, live item
  state, assignments, verdicts, or delivery evidence.
- GitHub read or write failure pauses affected work. Report the failed
  operation and do not claim a transition succeeded.

## Document organization

Follow the repository's document organization policy before choosing artifact
locations. Where it selects an issue-centered layout, that policy overrides
generic references here to a requirements document or handoff packet:

- The canonical issue description holds user requirements, acceptance criteria,
  product sign-off, and direct links to the Git technical design.
- Keep product sign-off to four entries: approver, approval timestamp, approved
  scope with a pinned snapshot link, and approval evidence. Do not invent approval.
- Git holds technical design, technical sign-off, detailed verification,
  technical decisions, and immutable approval snapshots. Keep hashes and migration
  history there, not in the issue's readable sign-off.
- Short handoffs are issue comments with scope/design versions, readiness
  evidence, remaining concerns, and the next invocation. Preserve any required
  transition decision with the comment; link detailed evidence instead of
  duplicating specifications or creating a separate living handoff document.
- The Project alone owns execution status, Action Owner, and claim.

Before technical sign-off, Build claim, or Review acceptance, compare the live
issue requirements block with its approved snapshot. Material scope changes
require renewed approval and applicable technical sign-off; edits to navigation
or sign-off presentation alone do not. Existing approvals survive a location-only
migration when the exact scope and original approval evidence are preserved.

Respect visibility: private planning is not published to a public issue without
explicit approval. Reuse an existing appropriate issue and Project card.
Repositories without an issue-centered policy retain their configured canonical
document locations; this does not migrate Lite or legacy installed consumers.

## Read-only PO status guidance

These are implementation and assessment constraints for the standalone PO
status utility, not a workflow role or permission to start Build. A status-only
request never authorizes a lifecycle transition, claim, handoff, or GitHub write.

1. **Decision-first presentation:** report observation time and coverage, then
   explicit pending product decisions, blockers, and moving work grouped as
   Ready, In progress, and In review. Use concise source-linked bullets and
   recorded owners. Short prose is not a coverage cap; never silently omit
   relevant work. Mark empty sections only after a complete read.
2. **Efficient complete reads:** resolve Project/schema metadata once per
   invocation and batch necessary source reads. Paginate every connection needed
   to identify or resolve decisions; do not filter evidence solely by Status,
   Action Owner, or keywords. Report incomplete/inaccessible sources explicitly.
   Do not add persistent caches, polling, or a scheduler.
3. **Current approval evidence:** use the canonical issue's current product
   sign-off and approved scope binding before interpreting archived draft
   labels. Check discussion through the latest relevant resolution. A role
   owner or old pending label alone is not a product decision; conflicting or
   ambiguous evidence remains unconfirmed, never silently resolved.
4. **Lean delivery:** keep the collector, utility instructions, discoverability,
   and focused tests in one cohesive slice. Use a simple evidence shape with
   explicit coverage and errors; avoid new orchestration, stores, services,
   planning documents, or abstractions without a demonstrated need. Preserve
   all approved verification and release obligations.

Verify output order, complete nested pagination, metadata reuse, later approval
resolutions, incomplete reads, and zero attempted writes on success, failure,
and repeat invocation. Keep utility observations separate from workflow evidence
written while developing it; design review is not implementation acceptance.

## Lifecycle and ownership

The shared statuses are `Inbox`, `Requirement shaping`, `Technical shaping`,
`Ready`, `In progress`, `In review`, `Blocked`, and `Done`. Lite skips
`Technical shaping`; Standard uses it for revision-bound Architect sign-off.
There is no separate Deliver status, stage, or agent. The configured closeout
owner merges an accepted PR, verifies landing and applicable delivery evidence,
closes the task, and sets `Done` last. The current configured owner is Review.

Normal dispatch is deterministic:

| Status | Action Owner |
|---|---|
| Inbox | Requirements |
| Requirement shaping | Requirements |
| Technical shaping | Architect |
| Ready | Build |
| In progress | Build |
| In review | Review |
| Blocked | Explicit owner recorded in the blocker packet |
| Done | None |

`Legacy Stage` is historical migration metadata and never controls dispatch. A
blocked item records `Resume Status`; clearing the blocker never skips
validation of the resumed state's gates.

## Configuration and preflight

New instances start from the [manifest template](templates/workflow.yaml),
which includes `project.fields.pull_request: Linked pull requests` for Standard
and Lite. Use GitHub's native Development relationship and Project field,
not a custom PR text field. Link cross-repository PRs from the issue sidebar.
Native issue auto-closure never substitutes for the Project Done gates.

Validate the local contract and manifest without GitHub access:

```bash
python3 workflow-kit/runtime.py --offline
```

Before the first pilot, after configuration changes, and when live schema drift
is suspected, run the live preflight:

```bash
python3 workflow-kit/runtime.py
```

The preflight reads authentication, repository access, the configured base
branch and merge strategy, artifact-repository access, Project update
permission, fields, and option names. It never creates, edits, or deletes
GitHub data. A failure reports the configured and live mismatch and ends with
`No changes were made.` Resolve GitHub field and option IDs only after a
passing preflight and immediately before an authorized item mutation.

See [the installation path](INSTALLATION.md). The root `install.sh` remains the
legacy installer; a workflow-kit installer is deferred until a named pilot
passes capture through verified closeout.

## Mandatory transition gate

Every role must fail closed through the executable contract before a Project
write that changes Status, Action Owner, Resume Status, Review Verdict,
Assignee, or Claim Session:

1. Re-read the live item and all evidence required by the intended transition.
2. Run the intended transition live with `--transition`, the contract status
   key, profile, work type, actor, current Action Owner, and one `--evidence`
   flag for each verified gate. The command performs the live preflight before
   evaluating the transition; `--offline` is insufficient for a Project
   mutation. For example:

   ```bash
   python3 workflow-kit/runtime.py \
     --transition claim-build-work \
     --status ready --profile standard --work-type Task \
     --actor Build --action-owner Build \
     --evidence claim-writable --evidence no-competing-work
   ```

3. Preserve the machine-readable decision with the handoff or closeout packet.
   A denied evaluation or failed preflight means no Project write.
4. Apply only the evaluated transition, then read back every changed field.
   Re-evaluate the read-back state for status-changing transitions; separately
   verify declared effects such as Review Verdict, Assignee, and Claim Session.

Evidence flags are assertions backed by live reads and linked records; they are
not permission to infer or manufacture evidence. The evaluator never mutates
GitHub and does not replace expected-head merge guards or post-write readback.

## Board configuration

Required GitHub Projects fields and views — including the Dependency map
(Roadmap layout grouped by Parent issue), the `Blocking reason` text field, and
the dependency relationship protocol — are specified in
[board-setup.md](board-setup.md). Follow that reference when creating a new
board or auditing an existing one. The `Blocking reason` field must be filled
whenever an item transitions to `Blocked` and cleared on unblock.

## Evidence authority

| Evidence | Authority |
|---|---|
| Identity and discussion | GitHub issue URL and number |
| Execution state | Configured Project `Status` |
| Approved scope | One linked committed requirements revision |
| Architecture | Sign-off naming that same requirements revision |
| Next role | Project `Action Owner` |
| Assignment and dependencies | Native issue links, Assignee, and recorded claim session |
| Implementation | Branch, commits, checks, and implementation PR |
| Review | Separate-session verdict for the exact PR head |
| Landing | Merge and intended-base commit evidence |
| Standard release | Required release/version/readiness record |

## Role routing

The current agent roster is **Requirements, Architect (Standard only), Build,
and Review**. Lite uses three roles: Requirements, Build, and Review.

| Role | Responsibility | Skill |
|---|---|---|
| Requirements | Shapes scope and records explicit user approval | [Requirements](skills/requirements/SKILL.md) |
| Architect (Standard only) | Owns technical shaping and sign-off against the approved requirements revision | [Architect](profiles/standard/skills/architect/SKILL.md) |
| Build | Owns implementation, checks, the implementation PR, and review fixes | [Build](skills/build/SKILL.md) |
| Review | Independently verifies the current PR head, merges eligible work, verifies landing, and closes it Done | [Review](skills/review/SKILL.md) |

These are not the legacy Ideation, Architect, Implementation, Review, and
Delivery Manager agents. Requirements replaces the scope-shaping entry point;
Build is the implementation entry point. There is no Delivery Manager role,
automatic dispatch, or self-review exception in this workflow.

Repository instructions may add stricter gates but must not assign the same
status to a second active role or override `closeout_owner` outside
[`workflow.yaml`](workflow.yaml). The configured Review role owns merge and
verified closeout; normal repository permissions and delivery gates still
govern merge. No role may infer deployment from Done.

Use the shared [Requirements](skills/requirements/SKILL.md),
[Build](skills/build/SKILL.md), and [Review](skills/review/SKILL.md) skills by
direct user invocation. There is no automatic role handoff. Apply the selected
profile's additional gates: [Lite](profiles/lite/PROFILE.md) or
[Standard](profiles/standard/PROFILE.md). Standard adds the
[Architect skill](profiles/standard/skills/architect/SKILL.md); Lite does not.
Requirements and Architect remain distinct entry points. Requirements owns
product shaping; Architect owns technical shaping. An already approved Standard
Feature may enter Technical shaping directly, but a Requirements invocation
never silently becomes an Architect invocation.

Reusable records live under [templates/shared](templates/shared). They are
evidence packets, not another execution queue. See the
[staged handoff examples](examples/handoffs.md) for successful and refused
transitions.
