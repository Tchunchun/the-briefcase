# Standard profile

Standard uses the shared workflow contract and Build skill with architecture,
Feature/Task hierarchy, and release governance.

## Requirements authority

Requirements owns product shaping and revision-bound approval. Approved
Features move to `Technical shaping` with `Action Owner: Architect`. A Feature
created with an already approved revision may enter Technical shaping directly,
but Requirements and Architect remain distinct roles and invocations.

Each Task links one canonical approved Feature PRD revision and its own scoped
acceptance criteria and verification. Issue text may summarize or link that
scope but must not become a second independently editable requirements source.

## Architecture gate

Before `Ready`, Architect records sign-off naming the exact approved Feature
PRD revision, technical approach, resolved questions, relevant decisions,
risks, and NFR verification. A material requirements change makes that sign-off
stale and returns the item to Architecture.
Missing approval or a product-scope gap blocks the item for targeted product
clarification; never manufacture approval or routinely reshape valid requirements.

Build must refuse a Standard claim when sign-off is missing, names a different
revision, or leaves a stopping technical question unresolved.

Invoke [Architect](skills/architect/SKILL.md) explicitly and use the
[Feature PRD template](../../templates/standard/brief.md). Material changes to
scope, AC, constraints, NFRs, approach assumptions, or release obligations
invalidate affected approval/sign-off, not only a changed document label.

## Task and Feature coordination

- A Task references its parent Feature and approved scope revision.
- Native blockers must be Done before a Task is claimed.
- A completed child Task does not make its Feature Done.
- Review and delivery verify complete Feature coverage without duplicating
  execution status in the PRD or release record.

Architect moves technically eligible work to `Ready` with `Action Owner: Build`.
Build assignment is recorded atomically when Build claims `Ready` and moves it
to `In progress`; assignment is not a prerequisite for `Ready`.

## Release gate

Accepted work remains `In review` until Review merges its reviewed head, verifies
landing and applicable delivery evidence, closes the task, and sets `Done`.
There is no separate Deliver stage. Feature completion additionally requires
complete child coverage and applicable version/release evidence. Deployment is
separate.

Use the [release record](../../templates/standard/release.md). An approved
no-release-note-required result waives only the note; version impact and all
other applicable delivery evidence must still be verified.

Use the shared [Requirements](../../skills/requirements/SKILL.md),
[Build](../../skills/build/SKILL.md), and [Review](../../skills/review/SKILL.md)
skills. This profile adds gates; it does not copy or replace the shared skills.
