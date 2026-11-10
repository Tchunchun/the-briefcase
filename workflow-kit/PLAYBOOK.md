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
- Each item links exactly one approved requirements revision. Lite uses a
  concise task document. Standard uses a Feature PRD and Task scope linked to
  that approved parent revision.
- Review must run in a session separate from the Build session and bind its
  verdict to both the approved requirements revision and the exact PR head.
- GitHub read or write failure pauses affected work. Report the failed
  operation and do not claim a transition succeeded.

## Lifecycle

Public stages are Capture, Requirements, Ready gate, Build, Review, Deliver,
and Done. Standard inserts Architecture after Requirements.

The Project statuses are `Inbox`, `Shaping`, `Ready`, `In progress`,
`In review`, `Blocked`, and `Done`. Stages and statuses are separate fields.
Accepted work remains `In review` until delivery gates pass.

## Evidence authority

| Evidence | Authority |
|---|---|
| Identity and discussion | GitHub issue URL and number |
| Execution state | Configured Project `Status` |
| Approved scope | One linked committed requirements revision |
| Architecture | Sign-off naming that same requirements revision |
| Assignment and dependencies | Native issue links plus a recorded claim |
| Implementation | Branch, commits, checks, and implementation PR |
| Review | Separate-session verdict for the exact PR head |
| Landing | Merge and intended-base commit evidence |
| Standard release | Required release/version/readiness record |

## Role routing

- Requirements owns scope approval and verifies closeout.
- Architect owns Standard technical decisions and revision-bound sign-off.
- Build owns implementation, checks, the implementation PR, and review fixes.
- Review independently verifies the current PR head and owns the verdict.
- Repository permissions govern merge. No role may infer deployment from Done.

Use the shared [Requirements](skills/requirements/SKILL.md),
[Build](skills/build/SKILL.md), and [Review](skills/review/SKILL.md) skills by
direct user invocation. There is no automatic role handoff. Apply the selected
profile's additional gates: [Lite](profiles/lite/PROFILE.md) or
[Standard](profiles/standard/PROFILE.md). Standard adds the
[Architect skill](profiles/standard/skills/architect/SKILL.md); Lite does not.

Reusable records live under [templates/shared](templates/shared). They are
evidence packets, not another execution queue. See the
[staged handoff examples](examples/handoffs.md) for successful and refused
transitions.
