# Lite profile

Lite uses the [shared playbook](../../PLAYBOOK.md) and shared
[Requirements](../../skills/requirements/SKILL.md),
[Build](../../skills/build/SKILL.md), and [Review](../../skills/review/SKILL.md).
Profiles reference these definitions rather than copying them.

One independently verifiable task links its concise approved requirement
revision. There is no Architect role, Feature/Task hierarchy prerequisite, or
Standard release record requirement. The application's own release policy
still applies.

In issue-centered repositories, the issue description has User requirements and
Technical design sections. Requirements may leave Technical design empty or
include simple inline details appropriate to the requirement. No separate Git
design document or technical sign-off is required.

A stopping technical question becomes a Requirements-owned blocker with the
affected revision, question, owner, prior stage, and resume condition. Revalidate
all shared Ready gates after resolution; do not jump directly from Blocked to
Ready or invent an Architect prerequisite.

Separate-session review of the exact implementation head, verified intended-base
landing, full scope coverage, and applicable application checks are still required.
Build must link the PR through the canonical issue's native Development
relationship and verify the Project's `Linked pull requests` before handoff.
Review picks up that linked PR, verifies the approved requirements revision, and
checks any inline technical details. In issue-centered repositories, compare
the live issue requirements against their approved snapshot and the inline
design against the reviewed content. An empty Technical design section does
not block review or require a not-applicable rationale; do not invent an
Architect gate. Revalidate the native link before accepting the exact head.
Accepted, landed, released, and deployed are distinct. GitHub failure pauses
affected work without a local status fallback.
