# Requirement packet

- Work item: `<issue URL and stable ID>`
- Profile: `<Lite | Standard>`
- Parent: `<Feature or none>`
- Canonical requirement: `<location and immutable revision>`
- Project: `<link; authoritative execution status, Action Owner, and claim>`

Follow the shared playbook's document organization and repository policy.
For issue-centered repositories, put this requirement in the issue description,
use a delimited requirements block and an immutable approval snapshot.
Standard links a Git technical design; Lite may leave Technical design empty
or include simple inline details at Requirements' discretion.
Do not create a second editable requirements document.
Keep Standard's detailed verification and technical decisions in Git; short
handoffs are issue comments. Repositories with other configured locations retain them.

## User requirements

<!-- approved-requirements:start -->

### Context and outcome

`<problem, affected user, and observable outcome>`

### Scope

- `<included behavior>`

### Exclusions

- `<explicitly excluded behavior>`

### Acceptance and verification

| Criterion | Observable result | Check | Owner |
|---|---|---|---|
| `<AC-01>` | `<result>` | `<command or inspection>` | `<role>` |

### Dependencies and questions

- Blockers: `<issue links or none>`
- Open questions: `<questions or none>`
- Privacy/visibility: `<target and constraint>`

<!-- approved-requirements:end -->

## Product sign-off

- Approved by: `<actual product approver; pending until explicitly approved>`
- Approved on: `<approval timestamp>`
- Approved scope: `<requirements link and pinned approved snapshot link>`
- Evidence: `<user approval or approval-record link>`

Keep hashes and migration history in linked Git evidence, not in this section.
Never record approval on the user's behalf.

Material scope changes require a new approved revision.

## Technical design

For Standard, replace this guidance with the Git architecture/design document
link, including its technical sign-off. For Lite, Requirements removes this
guidance and either leaves the section empty or writes simple technical details.
An empty Lite section requires no not-applicable rationale, separate Git design,
or Architect sign-off. Inline notes must not change approved scope or constraints.
