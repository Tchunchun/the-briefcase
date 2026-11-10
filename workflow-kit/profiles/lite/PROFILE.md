# Lite profile

Lite uses the [shared playbook](../../PLAYBOOK.md) and shared
[Requirements](../../skills/requirements/SKILL.md),
[Build](../../skills/build/SKILL.md), and [Review](../../skills/review/SKILL.md).
Profiles reference these definitions rather than copying them.

One independently verifiable task links its concise approved requirement
revision. There is no Architect role, Feature/Task hierarchy prerequisite, or
Standard release record requirement. The application's own release policy
still applies.

A stopping technical question becomes a Requirements-owned blocker with the
affected revision, question, owner, prior stage, and resume condition. Revalidate
all shared Ready gates after resolution; do not jump directly from Blocked to
Ready or invent an Architect prerequisite.

Separate-session review of the exact implementation head, verified intended-base
landing, full scope coverage, and applicable application checks are still required.
Accepted, landed, released, and deployed are distinct. GitHub failure pauses
affected work without a local status fallback.
