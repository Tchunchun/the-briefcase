# Standard release record

- Work item: `<issue URL and stable ID>`
- Work item type: `<Feature | Task>`
- Profile: `Standard`
- Approved requirement revision: `<location and immutable revision>`
- Review verdict: `<link to revision-bound review record>`
- Accepted head: `<full commit SHA>`
- Landing evidence: `<merged PR and base commit>`

## Version

- Version impact: `<major | minor | patch | none, with rationale>`
- Version: `<resulting vX.Y.Z, or not applicable with an independent reason>`
- Version approval: `<approver, timestamp, and evidence link for the impact/applicability>`

Version applicability is independent of the release-note outcome. A note
exemption never waives version impact, checks, coverage, or readiness evidence.

## Scope coverage

- Feature: `<issue URL>`
- Task slice: `<approved Task revision and covered criteria | not applicable for Feature>`
- Child Tasks covered: `<required list for Feature | not applicable for Task>`
- Applicable coverage complete: `<yes | no — Task slice or full Feature, with missing scope>`

## Required checks

| Check | Command | Result |
|---|---|---|
| `<check name>` | `<exact command>` | `<pass | fail>` |

## Release note

`<Summary of what changed and why it matters to users, or:>`

Release note: N/A — approved no-release-note-required
Approval: `<approver, timestamp, and link to the approval record>`
Reason: `<why the note exemption is appropriate>`

## Environment and readiness

- Required environments: `<from the approved Feature; evidence per environment>`
- Readiness evidence: `<links and results, or justified non-applicability>`
- Remaining obligations: `<none, or explicit missing evidence/owner/resume condition>`

## Completion gate

- Task: `<own slice accepted, checks/dependencies complete, landing verified, and Task-allocated release obligations complete | not applicable>`
- Feature: `<all required child slices covered, Feature acceptance complete, landing verified, and version/release/readiness evidence complete | not applicable>`

---

This record links the accepted implementation head to the approved requirement
revision and version evidence. Deployment is a separate record and must not be
inferred from this release record or from Project `Done`.
