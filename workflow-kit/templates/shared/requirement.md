# Requirement packet

- Work item: `<issue URL and stable ID>`
- Profile: `<Lite | Standard>`
- Parent: `<Feature or none>`
- Canonical requirement: `<location and immutable revision>`
- Project: `<link; authoritative execution status, Action Owner, and claim>`

Follow the shared playbook's document organization and repository policy.
For issue-centered repositories, put this requirement in the issue description,
use a delimited requirements block and an immutable approval snapshot, and link
the Git technical design. Do not create a second editable requirements document.
Keep detailed verification and technical decisions in Git; short handoffs are
issue comments. Repositories with other configured locations retain them.

## Context and outcome

`<problem, affected user, and observable outcome>`

## Scope

- `<included behavior>`

## Exclusions

- `<explicitly excluded behavior>`

## Acceptance and verification

| Criterion | Observable result | Check | Owner |
|---|---|---|---|
| `<AC-01>` | `<result>` | `<command or inspection>` | `<role>` |

## Dependencies and questions

- Blockers: `<issue links or none>`
- Open questions: `<questions or none>`
- Privacy/visibility: `<target and constraint>`

## Product sign-off

- Approved by: `<actual product approver; pending until explicitly approved>`
- Approved on: `<approval timestamp>`
- Approved scope: `<requirements link and pinned approved snapshot link>`
- Evidence: `<user approval or approval-record link>`

Keep hashes and migration history in linked Git evidence, not in this section.
Never record approval on the user's behalf.

Material scope changes require a new approved revision.
