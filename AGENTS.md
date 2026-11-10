# AGENTS.md

Read `skills/PLAYBOOK.md` fully before taking any action.

Upstream source for the 0-to-1 Agent Skills framework (five roles, workflow playbook, CLI tooling, Notion integration).

Note: In this repo, skills live at `skills/` and paths in the PLAYBOOK are correct as-is. The `install.sh` script rewrites them to `.briefcase/skills/` for consumer projects.

## This Repository's Backlog

Read [_project/backlog-policy.md](_project/backlog-policy.md).
[GitHub Project #5](https://github.com/users/Tchunchun/projects/5) is the only
active backlog and owns execution status. This repository-specific policy
overrides generic playbook instructions to use CLI backlog rows, the legacy
inbox, or backlog-scanning automation. Use GitHub directly; do not recreate or
update the retired Markdown backlog. If access fails, report it and pause
affected work rather than silently falling back to local status.

Standard features enter Technical shaping with requirements already shaped
and approved at feature creation. Technical shaping covers architecture and
remaining Build readiness gates. No separate User requirement shaping pass is
required; missing or changed scope is an explicit exception, not routine intake.
Stage and Review Verdict support Status; legacy fields are historical only.

When the user says **"Run the technical shaping loop"** or **"Run the architecture
loop"**, follow the
[repository technical shaping loop](_project/backlog-policy.md#repository-technical-shaping-loop).
**"Run the requirements loop"** remains a compatibility alias for that Standard
loop, not a request to repeat product shaping. Architect owns technical sign-off;
product owns any missing or changed scope approval. Ready also requires satisfied
dependencies and an accepted assignment. Stop at handoff, never automatic Build
dispatch.

When the user says **"Run the review loop"**, follow the
[repository review loop](_project/backlog-policy.md#repository-review-loop).
With no target, inspect the active board's In review column. An independent
review session merges a passing PR, verifies landing and applicable delivery
gates, then marks the task Done and closes its linked issue under that
procedure. Required checks, approvals, and branch protections still apply;
queued or gated work stays open. Explicitly read-only reviews do not mutate.

The configured Git backend still stores briefs, decisions, releases, and
history; no GitHub storage adapter is implied. This override is for framework
development only, not a change to the installed consumer workflow.

## Commands

| Task | Command |
|------|---------|
| Run all tests | `python3 -m pytest tests/` |
| Test one file | `python3 -m pytest tests/path/to/test_file.py` |
| Lint all | `ruff check src/ tests/` |
| Lint one file | `ruff check path/to/file.py` |
| Run CLI (framework repo) | `python3 -m src.cli.main <command>` |
| Run CLI (consumer project) | `./briefcase <command>` |
| Format | `ruff format src/ tests/` |

Load `.env` before CLI commands that hit Notion:
```
export $(grep -v '^#' .env | xargs)
```

## Project Root Resolution

Always resolve the project root before running any `briefcase` command.
If you are in a git worktree (e.g. `.claude/worktrees/<name>/`), a subdirectory, or any path where `./briefcase` does not exist, you are **not** missing the CLI — you are not at the project root.

```bash
PROJECT_ROOT="$(git rev-parse --show-toplevel)"
cd "$PROJECT_ROOT"
```

Then run `briefcase` commands from the project root, or pass `--project-dir "$PROJECT_ROOT"` explicitly.

> **Never treat a missing `./briefcase` as "CLI not available."** It means you need to resolve the project root first.

## Key Conventions

- All folders use `kebab-case`
- Titles (inbox, backlog, brief): **3–7 words**. Longer context goes in `--notes`.
- Python: PEP 8 via `ruff`. Config in YAML. Secrets in `.env`, never committed.
- See `_project/tech-stack.md` for full stack. See `_project/testing-strategy.md` for test policy.

## Commit Attribution

AI commits MUST include:
```
Co-Authored-By: Claude <noreply@anthropic.com>
```
