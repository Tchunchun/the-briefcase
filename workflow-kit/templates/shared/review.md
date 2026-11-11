# Review record

- Work item: `<issue URL and stable ID>`
- Pull request: `<PR URL>`
- Approved requirement: `<location and immutable revision>`
- Native PR relationship: `<canonical issue Development and Project Linked pull requests readback>`
- Technical design: `<Standard: Git link and immutable revision | Lite: issue section and reviewed inline content, or empty>`
- Architecture sign-off: `<current applicable Git sign-off | not applicable for Lite>`
- Reviewed head: `<full commit SHA>`
- Intended base: `<branch>`
- Reviewer session: `<identity; separate from Build>`
- Formal GitHub approval available: `<yes | no, with limitation>`
- Status / Action Owner: `<In review / Review>`

## Criterion evidence

| Criterion | Evidence at reviewed head | Result |
|---|---|---|
| `<AC-01>` | `<test, behavior, or diff link>` | `<pass | fail>` |

## Design conformance

| Design decision / constraint / NFR | Evidence at reviewed head | Result |
|---|---|---|
| `<requirement from the applicable linked or inline design>` | `<test, behavior, or diff link>` | `<pass | fail>` |

For Lite, record the reviewed inline content or that Technical design is empty;
an empty section needs no rationale or conformance rows. Do not invent a Git
design or Architect prerequisite. Missing required Standard design
or sign-off blocks the verdict.

## Checks and findings

- Checks: `<exact commands and results>`
- Findings: `<severity, location, and action; or none>`
- Coverage/dependencies: `<complete | missing evidence>`

## Verdict

`<Accepted | Changes requested | Blocked>`

Reason: `<evidence-backed summary>`

Any new PR head invalidates this verdict until reviewed again.

For an accepted eligible PR, Review records merge and landing evidence, closes
the task, and sets `Done / None` only after every completion gate passes.
