# AGENTS.md

Read `skills/PLAYBOOK.md` fully before taking any action.

Upstream source for the 0-to-1 Agent Skills framework (five roles, workflow playbook, CLI tooling, Notion integration).

Note: In this repo, skills live at `skills/` and paths in the PLAYBOOK are correct as-is. The `install.sh` script rewrites them to `.briefcase/skills/` for consumer projects.

## This Repository's Backlog

Read [_project/backlog-policy.md](_project/backlog-policy.md).
[GitHub Project #4](https://github.com/users/Tchunchun/projects/4) is the only
active backlog and owns execution status. This repository-specific policy
overrides generic playbook instructions to use CLI backlog rows, the legacy
inbox, or backlog-scanning automation. Use GitHub directly; do not recreate or
update the retired Markdown backlog. If access fails, report it and pause
affected work rather than silently falling back to local status.

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
- Titles (inbox, backlog, brief): **3–7 words**. Longer context goes in `--notes`.
- Python: PEP 8 via `ruff`. Config in YAML. Secrets in `.env`, never committed.
- See `_project/tech-stack.md` for full stack. See `_project/testing-strategy.md` for test policy.

## Commit Attribution

AI commits MUST include:
```
Co-Authored-By: Claude <noreply@anthropic.com>
```
