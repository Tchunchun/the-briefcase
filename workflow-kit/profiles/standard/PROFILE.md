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

Use [the shared Build skill](../../skills/build/SKILL.md). This profile adds
gates; it does not copy or replace the shared skill.
