# Standard Feature PRD

- Work item: `<issue URL and stable ID>`
- Profile: `Standard`
- Parent/source: `<linked initiative or parent; none with reason>`
- Canonical requirement: `<location and immutable revision>`
- Requirement approval: `<approver, timestamp, and approval link>`

---

Use this template for the canonical Feature PRD, or link its scope sections to
the one existing canonical PRD at the approved revision. Requirements owns those
sections and their approval; Architect owns the technical assessment and sign-off.
Never create an independently editable second scope or store Project status here.

Follow the shared playbook's document organization and repository policy.
For issue-centered repositories, use the product sections below in the issue
description's User requirements section with the shared requirement template's
four-entry product sign-off.
Use the technical sections in the Git design, linking the approved issue scope
and immutable snapshot rather than copying product requirements. Add a direct
design link in the issue's Technical design section. Short handoffs are issue
comments, not separate living documents. Keep snapshot hashes and migration
history in linked Git evidence.
This combined template does not require a second editable specification.

## Context and expected experience

- Problem and outcome: `<current behavior, motivation, desired outcome>`
- Actors: `<affected users>`
- Before/after experience: `<observable example, or canonical section link>`

## Scope and exclusions

- Included: `<scope or canonical section link>`
- Excluded: `<boundaries and preserved behavior>`

## Acceptance and verification

| Criterion | Observable result | Check and environment | Owner |
|---|---|---|---|
| `<AC-ID>` | `<positive/failure/regression outcome>` | `<command or evidence>` | `<role>` |

## Constraints and compatibility

- Invariants and NFRs: `<measurable constraints or canonical section link>`
- Compatibility/migration: `<preserved behavior and migration obligations>`
- Cost/licensing: `<dependencies, expected cost and license constraints; none with reason>`
- Dependencies and open questions: `<native issue links, question owner and resume condition>`

## Technical approach

`<Chosen approach: patterns, libraries, and key constraints from the repository's
engineering rules that this approach must satisfy. Address each NFR that has an
architectural implication.>`

## Alternatives considered

| Alternative | Why rejected |
|---|---|
| `<Option A>` | `<reason>` |
| `<Option B>` | `<reason>` |

Record at least one alternative when the chosen approach involves a meaningful
trade-off or introduces a new dependency.

## Risk assessment

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| `<risk>` | `<low/med/high>` | `<low/med/high>` | `<mitigation or acceptance rationale>` |

## NFR verification

| NFR | Requirement | How verified |
|---|---|---|
| `<NFR name>` | `<stated requirement>` | `<check, benchmark, or accepted rationale>` |

## Architect sign-off

- Work item type: `<Feature | Task>`
- Architecture applicability: `<Feature sign-off | Task-specific sign-off | parent sign-off applies, with reason>`
- Approved requirement revision: `<same location and revision as "Canonical requirement" above>`
- Approved Task revision: `<child scope revision when applicable; otherwise none>`
- Decision record: `<path to ADR, e.g. docs/plan/_reference/adr/ADR-NNN.md, or "none">`
- Signed by: `<approver>`
- Signed at: `<timestamp>`
- Result: `<approved | blocked; unresolved questions and resume criteria>`

This sign-off is bound to the exact requirement revision listed above.
A material change to acceptance criteria, scope inclusions, or exclusions
invalidates this sign-off and requires a new Architecture review.
The same applies to constraints, NFRs, approach assumptions, and release obligations.
For a child Task, `parent sign-off applies` is valid only when Architect records
that the approved Task slice introduces none of those changes or a new technical
decision, interface, dependency, or unresolved technical question.

## Decisions and child Tasks

- Decisions: `<durable decision record links, or none with rationale>`
- Children: `<Task issue links, each with its approved slice and parent revision>`

Child Tasks reference the approved parent scope; they do not copy the whole PRD
or redefine it. A completed child does not complete the Feature.

## Release obligations

- Required checks: `<commands and expected results>`
- Version impact: `<declared impact and resulting version, or justified applicability>`
- Release-note expectation: `<required note or explicitly approved exemption>`
- Supported environments/readiness: `<required evidence and owner>`

Use the [release record](release.md). A release-note exemption does not waive
version applicability, checks, coverage, or readiness evidence.
