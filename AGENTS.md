# AGENTS.md

Read [the current workflow playbook](workflow-kit/PLAYBOOK.md) and
[this repository's backlog policy](_project/backlog-policy.md) before taking
any action. The repository policy takes precedence where it defines a
repository-specific procedure, including Review-owned merge and closeout.

The current roles are **Requirements, Architect (Standard only), Build, and
Review**. Lite uses Requirements, Build, and Review. Users invoke the roles
directly; there is no Delivery Manager or automatic role orchestration.

## Bootstrap Phase

The repository is currently building the workflow kit before dogfooding it.
Changes whose primary purpose is to build, repair, document, or test
`workflow-kit/` do **not** invoke the kit's Requirements, Architect, Build, or
Review workflows unless the user explicitly says **"Use Standard mode for
<target>"**, **"Use Lite mode for <target>"**, or invokes a named role or loop.
Ordinary requests such as "build", "implement", "fix", "review this code", or
an issue/Project link are not workflow-mode activation by themselves.

Bootstrap work still uses GitHub Project #5 as the only backlog and follows
normal repository testing and PR safeguards; it does not create a parallel
queue. Dogfooding begins only after explicit user activation, applies
prospectively to the named pilot work, and does not retrofit existing kit work.
Until the user explicitly ends this phase, direct kit-development requests are
handled as ordinary repository work without Standard/Lite role packets, gates,
or status transitions inferred from the kit.

This repository also maintains the legacy five-role framework, CLI tooling,
and storage integrations. [The legacy playbook](skills/PLAYBOOK.md) and its
role skills remain the source for `install.sh` consumers, not the active
repository agent roster. The installer rewrites legacy skill paths to
`.briefcase/skills/`; it does not install `workflow-kit/`.

## This Repository's Backlog

Read [_project/backlog-policy.md](_project/backlog-policy.md).
[GitHub Project #5](https://github.com/users/Tchunchun/projects/5) is the only
active backlog and owns execution status. This repository-specific policy
overrides generic playbook instructions to use CLI backlog rows, the legacy
inbox, or backlog-scanning automation. Use GitHub directly; do not recreate or
update the retired Markdown backlog. If access fails, report it and pause
affected work rather than silently falling back to local status.
Create planning issues in private `Tchunchun/thebriefcase-artifacts` and keep
them on Project #5. Code, branches, and PRs belong in public
`Tchunchun/the-briefcase`; do not publish private planning in PR descriptions
or comments.

Standard uses distinct Requirement shaping and Technical shaping queues.
`Action Owner` is the automation dispatch authority: Requirements, Architect,
Build, Review, or None. Stage is reporting-only and does not dispatch work.
Legacy fields are historical only.

When the user explicitly activates Standard mode for a target, including by
saying **"Run the technical shaping loop for <target>"** or **"Run the
architecture loop for <target>"**, follow the
[repository technical shaping loop](_project/backlog-policy.md#repository-technical-shaping-loop).
Requirements and Architect remain distinct roles and invocations. Architect
owns technical sign-off; Requirements owns product scope and approval. Ready
requires approved scope, current sign-off, satisfied dependencies, and no
competing implementation claim. Build records assignment when it claims Ready.
Stop at handoff; never automatically dispatch Build.

When the user explicitly activates a workflow mode for a target, including by
saying **"Run the review loop"** for a named target, follow the
[repository review loop](_project/backlog-policy.md#repository-review-loop).
After bootstrap is explicitly ended, with no target inspect `In review` work
owned by Review. An independent Review session merges a passing PR, verifies
landing and applicable delivery gates, then closes the task and marks it Done.
There is no separate Deliver stage. Required checks, approvals, and branch
protections still apply; queued or gated work stays open. Explicitly
read-only reviews do not mutate.

For this repository, the canonical planning issue description holds user
requirements, acceptance criteria, product sign-off, and a Technical design
section. Standard links that section to the Git architecture/design document.
Lite leaves it empty or includes simple inline technical details, as determined
by Requirements; no separate Git design or Architect phase is required.
Git holds technical design, technical sign-off, verification details, and
decisions for Standard, plus immutable approval snapshots for both profiles.
Short handoffs are issue comments,
not separate living documents. See the
[document organization policy](_project/backlog-policy.md#document-organization)
for revision binding, privacy, and historical-document migration.
The Project alone owns execution status, owner, and claim.
Use GitHub's native Development links and Project `Linked pull requests` field,
not a custom PR field or Notes. Build verifies the native link before handoff;
Review verifies the linked PR and exact head. Native issue auto-closure on merge
does not authorize Project Done before all landing and delivery gates pass.
Prefer native GitHub fields and relationships; check their cross-repository
capabilities before introducing a duplicate custom field.
Both Standard and Lite require verified native PR linking before In review.
Separate-session Review uses the linked PR's exact head, approved requirements
in the issue, and the mode-specific Technical design section: Standard's linked
Git design or Lite's inline details. An empty Lite section does not block review.
Keep product sign-off to four entries: approver, approval timestamp, approved
scope with a pinned snapshot link, and approval evidence. Keep hashes, full
revision identifiers, and migration history in the linked Git evidence rather
than repeating them in the issue. Verify the live requirements against the
approved snapshot before sign-off, Build claim, or Review acceptance; a concise
presentation does not waive revision binding or authorize approval by an agent.
The configured Git artifact backend still stores planning documents, decisions,
release records, and history; no GitHub storage adapter is implied. This policy
is for framework development, not a change to the legacy installed consumer
workflow.

For an explicitly invoked workflow role, every Project transition must pass the
live preflight and executable transition gate in
[the workflow playbook](workflow-kit/PLAYBOOK.md#mandatory-transition-gate).
`--offline` validation alone never authorizes a Project write.

## Read-only PO status guidance

A request for status is not permission to invoke a delivery role or mutate
GitHub. Follow the shared playbook's read-only PO status guidance: observation
time and coverage first, then product decisions, blockers, and moving work.
Batch complete reads without dropping evidence; use current, scope-bound
approval rather than archived pending labels. Keep the delivery small and
read-only, and distinguish design guidance from implementation acceptance.

## Development Commands

The CLI commands below maintain the legacy framework and its supported storage
backends. They are not the entry points for the current Requirements, Architect,
Build, or Review loops. Use GitHub directly for this repository's backlog.

| Task | Command |
|------|---------|
| Run all tests | `python3 -m pytest tests/` |
| Test one file | `python3 -m pytest tests/path/to/test_file.py` |
| Lint all | `ruff check src/ tests/` |
| Lint one file | `ruff check path/to/file.py` |
| Run CLI (framework repo) | `python3 -m src.cli.main <command>` |
| Run CLI (consumer project) | `./briefcase <command>` |
| Format | `ruff format src/ tests/` |

For legacy Notion integration only, load `.env` before CLI commands that hit Notion:
```
export $(grep -v '^#' .env | xargs)
```

## Legacy CLI Project Root Resolution

Always resolve the project root before running any `briefcase` command.
In Git, this is the current checkout or linked worktree, not necessarily the
main checkout that holds the framework installation:

```bash
PROJECT_ROOT="$(git rev-parse --show-toplevel)"
cd "$PROJECT_ROOT"
```

Keep `_project/storage.yaml` and artifacts in this checkout. The installed
launcher can share the main checkout's `.briefcase/` code and Python environment
without inheriting its config or changing the caller's directory. It defaults
`--project-dir` to the current checkout root; explicit options still win.

If `./briefcase` is missing, use `git worktree list` to locate the initialized
main checkout and invoke its launcher by absolute path **from this worktree**.
Read shared framework instructions there if `.briefcase/skills/` is absent
here. Do not `cd` to the main checkout or point `--project-dir` there unless
you intend to operate on its artifacts. If this worktree has no canonical
config, initialize it explicitly; never assume the local backend.

## Key Conventions

- All folders use `kebab-case`
- Issue and task titles: **3–7 words**. Put longer context in the issue discussion
  or linked requirements document, not a second status queue.
- Python: PEP 8 via `ruff`. Config in YAML. Secrets in `.env`, never committed.
- See `_project/tech-stack.md` for full stack. See `_project/testing-strategy.md` for test policy.

## Commit Attribution

AI commits MUST include:
```
Co-Authored-By: Claude <noreply@anthropic.com>
```
