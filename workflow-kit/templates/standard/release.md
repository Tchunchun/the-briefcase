# Standard release record

- Work item: `<issue URL and stable ID>`
- Profile: `Standard`
- Approved requirement revision: `<location and immutable revision>`
- Review verdict: `<link to revision-bound review record>`
- Accepted head: `<full commit SHA>`
- Landing evidence: `<merged PR and base commit>`

## Version

- Version: `<vX.Y.Z or N/A — approved no-release-note-required>`
- Version approval: `<approver, timestamp, and link to the approval record; or "not applicable">`

## Scope coverage

- Feature: `<issue URL>`
- Child Tasks covered: `<list of issue URLs or "none">`
- Coverage complete: `<yes | no — if no, list what is missing>`

## Required checks

| Check | Command | Result |
|---|---|---|
| `<check name>` | `<exact command>` | `<pass | fail>` |

## Release note

`<Summary of what changed and why it matters to users, or:>`

Release note: N/A — approved no-release-note-required
Approval: `<approver, timestamp, and link to the approval record>`

---

This record links the accepted implementation head to the approved requirement
revision and version evidence. Deployment is a separate record and must not be
inferred from this release record or from Project `Done`.
