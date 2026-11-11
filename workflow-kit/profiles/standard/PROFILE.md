# Standard profile

Standard uses the shared workflow contract and Build skill with architecture,
Feature/Task hierarchy, and release governance.

## Requirements authority

Requirements owns product shaping and revision-bound approval. Approved
Features move to `Technical shaping` with `Action Owner: Architect`. A Feature
created with an already approved revision may enter Technical shaping directly,
but Requirements and Architect remain distinct roles and invocations.

Each Task links one canonical approved Feature PRD revision and its own scoped
acceptance criteria and verification. Follow the shared playbook's document
organization and repository policy: an issue-centered repository uses the parent
issue's approved scope snapshot for that revision, with product requirements
and concise sign-off in the issue and technical design/sign-off in Git.
Otherwise issue text summarizes or links the configured canonical document.
Never create a second independently editable requirements source.
The issue description has User requirements and Technical design sections;
Technical design links to the Git architecture/design document, including its
revision-bound technical sign-off. Do not replace that document with inline
technical notes.

## Feature and Task architecture gates

Before a Feature is `Ready`, Architect records sign-off naming the exact
approved Feature PRD revision, technical approach, resolved questions, relevant
decisions, risks, NFR verification, child-work boundaries, and Feature release
obligations. A material requirements change makes that sign-off stale and
returns the affected work to Architecture.
Missing approval or a product-scope gap blocks the item for targeted product
clarification; never manufacture approval or routinely reshape valid requirements.

A child Task inherits the current parent Feature sign-off. It needs a separate
Task architecture assessment only when its approved slice introduces a new
technical decision, changes an interface, dependency, NFR, approach assumption,
or release obligation, or leaves a technical question unresolved. Architect
records either the Task-specific sign-off or `parent sign-off applies`, naming
both the parent and Task revisions. Build must refuse a Standard claim when the
applicable evidence is missing, stale, names a different revision, or leaves a
stopping technical question unresolved.

Invoke [Architect](skills/architect/SKILL.md) explicitly and use the
[Feature PRD template](../../templates/standard/brief.md). Material changes to
scope, AC, constraints, NFRs, approach assumptions, or release obligations
invalidate affected approval/sign-off, not only a changed document label.

## Task and Feature coordination

- A Task references its parent Feature and approved scope revision.
- A Task records architecture applicability as `parent sign-off applies` or
  links its own Task-specific Architect sign-off.
- Native blockers must be Done before a Task is claimed.
- A Task can become Done after its own approved slice is independently accepted,
  merged, landed, and its Task-level gates pass; it does not wait for sibling
  Tasks or Feature release completion.
- A completed child Task does not make its Feature Done. Feature Done requires
  every required child slice to be Done or otherwise covered with approved
  evidence, all Feature acceptance criteria satisfied, and applicable Feature
  version, release-note, environment, and readiness evidence complete.
- Review and closeout verify the applicable Task or Feature gate without
  duplicating execution status in the PRD or release record.

Architect moves technically eligible work to `Ready` with `Action Owner: Build`.
Build assignment is recorded atomically when Build claims `Ready` and moves it
to `In progress`; assignment is not a prerequisite for `Ready`.

## Delivery gates

Build must link the implementation PR through the canonical issue's native
Development relationship and verify the Project's `Linked pull requests` before
handoff. Separate-session Review picks up that linked PR and checks its exact
head against the approved scope and applicable Git design/sign-off,
including inherited parent architecture for Tasks. Missing or stale evidence
blocks acceptance.

Accepted work remains `In review` until the closeout owner configured in
[`workflow.yaml`](../../workflow.yaml) merges its reviewed head, verifies
landing and applicable delivery evidence, closes the item, and sets `Done`.
There is no separate Deliver stage.
Native Development links may auto-close an issue on merge. Review verifies
that closure and all remaining landing/release gates before Project Done;
issue closure alone does not satisfy this profile.

| Work item | Done gate |
|---|---|
| Task | Its approved slice is accepted on the exact head, required Task checks and dependencies pass, landing is verified, and any release obligation allocated to the Task is complete. |
| Feature | All required child slices are Done or covered by explicit accepted evidence, Feature-level acceptance passes, landing is complete, and applicable version, release-note, environment, and readiness evidence is complete. |

Deployment is separate from both gates and is never inferred from Done.

Use the [release record](../../templates/standard/release.md). An approved
no-release-note-required result waives only the note; version impact and all
other applicable delivery evidence must still be verified.

Use the shared [Requirements](../../skills/requirements/SKILL.md),
[Build](../../skills/build/SKILL.md), and [Review](../../skills/review/SKILL.md)
skills. This profile adds gates; it does not copy or replace the shared skills.
