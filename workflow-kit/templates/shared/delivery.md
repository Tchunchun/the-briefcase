# Delivery record

- Work item: `<issue URL and stable ID>`
- Approved requirement: `<location and immutable revision>`
- Accepted head: `<full commit SHA>`
- Review verdict: `<link to revision-bound review record>`
- Intended base: `<branch>`
- Landing evidence: `<merged PR and base commit>`
- Required checks: `<commands/check runs and results>`
- Work item type: `<Feature | Task>`
- Applicable coverage: `<Task's own approved slice | Feature scope and all required child slices>`
- Standard release evidence: `<release/version/readiness link | not applicable for Lite>`
- Deployment: `<separate record | not claimed>`

## Closeout

- Action Owner: `<Review until complete | None when Done>`
- Issue closure verified: `<yes | no>`
- Project `Done` verified: `<yes | no>`
- Remaining obligations: `<none | explicit blocker and owner>`

There is no separate Deliver stage. The configured closeout owner does not mark
`Done` unless acceptance, landing, applicable coverage, checks, and applicable
release evidence are all verified. A Task may complete independently after its
own gate passes; Feature completion additionally requires full required child
coverage and Feature-level release evidence.
