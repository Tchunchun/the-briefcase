# Briefcase Workflow Kit

This directory is the additive source for the new GitHub-first Briefcase
product. It is not an installed workflow by itself. The existing `install.sh`,
`src/`, `skills/`, `template/`, and `lite/` paths are legacy and must remain
behaviorally unchanged unless a separately approved migration says otherwise.

## Product contract

- Users invoke Requirements, Architect (Standard only), Build, and Review
  directly. There is no background scheduler or automatic role orchestration.
- GitHub Issues identify work and hold discussion.
- The configured GitHub Project `Status` field is the only execution state.
  Never create or consult a competing Markdown status queue.
- The Project `Action Owner` field is the automation dispatch authority. Status
  describes lifecycle position; Action Owner names the role that must act next.
- Each item links exactly one approved requirements revision. Lite uses a
  concise task document. Standard uses a Feature PRD and Task scope linked to
  that approved parent revision.
- Review must run in a session separate from the Build session and bind its
  verdict to both the approved requirements revision and the exact PR head.
- [`workflow.yaml`](workflow.yaml) is the single configuration point for the
  closeout owner. Profiles, skills, and repository policy may add stricter
  gates, but must not select a different role independently.
- GitHub read or write failure pauses affected work. Report the failed
  operation and do not claim a transition succeeded.

## Lifecycle and ownership

The shared statuses are `Inbox`, `Requirement shaping`, `Technical shaping`,
`Ready`, `In progress`, `In review`, `Blocked`, and `Done`. Lite skips
`Technical shaping`; Standard uses it for revision-bound Architect sign-off.
There is no separate Deliver status, stage, or agent. The configured closeout
owner merges an accepted PR, verifies landing and applicable delivery evidence,
closes the task, and sets `Done` last. The current configured owner is Review.

Normal dispatch is deterministic:

| Status | Action Owner |
|---|---|
| Inbox | Requirements |
| Requirement shaping | Requirements |
| Technical shaping | Architect |
| Ready | Build |
| In progress | Build |
| In review | Review |
| Blocked | Explicit owner recorded in the blocker packet |
| Done | None |

`Stage` is optional reporting metadata and never controls dispatch. If retained
during migration, it must agree with Action Owner for active work. A blocked
item also records `Resume Status`; clearing the blocker never skips validation
of the resumed state's gates.

## Evidence authority

| Evidence | Authority |
|---|---|
| Identity and discussion | GitHub issue URL and number |
| Execution state | Configured Project `Status` |
| Approved scope | One linked committed requirements revision |
| Architecture | Sign-off naming that same requirements revision |
| Next role | Project `Action Owner` |
| Assignment and dependencies | Native issue links, Assignee, and recorded claim session |
| Implementation | Branch, commits, checks, and implementation PR |
| Review | Separate-session verdict for the exact PR head |
| Landing | Merge and intended-base commit evidence |
| Standard release | Required release/version/readiness record |

## Role routing

The current agent roster is **Requirements, Architect (Standard only), Build,
and Review**. Lite uses three roles: Requirements, Build, and Review.

| Role | Responsibility | Skill |
|---|---|---|
| Requirements | Shapes scope and records explicit user approval | [Requirements](skills/requirements/SKILL.md) |
| Architect (Standard only) | Owns technical shaping and sign-off against the approved requirements revision | [Architect](profiles/standard/skills/architect/SKILL.md) |
| Build | Owns implementation, checks, the implementation PR, and review fixes | [Build](skills/build/SKILL.md) |
| Review | Independently verifies the current PR head, merges eligible work, verifies landing, and closes it Done | [Review](skills/review/SKILL.md) |

These are not the legacy Ideation, Architect, Implementation, Review, and
Delivery Manager agents. Requirements replaces the scope-shaping entry point;
Build is the implementation entry point. There is no Delivery Manager role,
automatic dispatch, or self-review exception in this workflow.

Repository instructions may add stricter gates but must not assign the same
status to a second active role or override `closeout_owner` outside
[`workflow.yaml`](workflow.yaml). The configured Review role owns merge and
verified closeout; normal repository permissions and delivery gates still
govern merge. No role may infer deployment from Done.

Use the shared [Requirements](skills/requirements/SKILL.md),
[Build](skills/build/SKILL.md), and [Review](skills/review/SKILL.md) skills by
direct user invocation. There is no automatic role handoff. Apply the selected
profile's additional gates: [Lite](profiles/lite/PROFILE.md) or
[Standard](profiles/standard/PROFILE.md). Standard adds the
[Architect skill](profiles/standard/skills/architect/SKILL.md); Lite does not.
Requirements and Architect remain distinct entry points. Requirements owns
product shaping; Architect owns technical shaping. An already approved Standard
Feature may enter Technical shaping directly, but a Requirements invocation
never silently becomes an Architect invocation.

Reusable records live under [templates/shared](templates/shared). They are
evidence packets, not another execution queue. See the
[staged handoff examples](examples/handoffs.md) for successful and refused
transitions.
