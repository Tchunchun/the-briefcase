# Standard profile

Standard uses the shared workflow contract and Build skill with architecture,
Feature/Task hierarchy, and release governance.

## Requirements authority

Each Task links one canonical approved Feature PRD revision and its own scoped
acceptance criteria and verification. Issue text may summarize or link that
scope but must not become a second independently editable requirements source.

## Architecture gate

Before `Ready`, Architect records sign-off naming the exact approved Feature
PRD revision, technical approach, resolved questions, relevant decisions,
risks, and NFR verification. A material requirements change makes that sign-off
stale and returns the item to Architecture.

Build must refuse a Standard claim when sign-off is missing, names a different
revision, or leaves a stopping technical question unresolved.

Invoke [Architect](skills/architect/SKILL.md) explicitly and use the
[full Feature brief](../../templates/standard/brief.md). Material changes to
scope, AC, constraints, NFRs, approach assumptions, or release obligations
invalidate affected approval/sign-off, not only a changed document label.

## Task and Feature coordination

- A Task references its parent Feature and approved scope revision.
- Native blockers must be Done before a Task is claimed.
- A completed child Task does not make its Feature Done.
- Review and delivery verify complete Feature coverage without duplicating
  execution status in the PRD or release record.

## Release gate

Accepted work remains `In review` until its reviewed head lands on the intended
base and the Feature has complete scope coverage, required checks, applicable
version evidence, and a linked release record. Deployment is separate.

Use the [release record](../../templates/standard/release.md). An approved
no-release-note-required result waives only the note; version impact and all
other applicable delivery evidence must still be verified.

Use the shared [Requirements](../../skills/requirements/SKILL.md),
[Build](../../skills/build/SKILL.md), and [Review](../../skills/review/SKILL.md)
skills. This profile adds gates; it does not copy or replace the shared skills.
