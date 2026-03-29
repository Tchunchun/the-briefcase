# AGENTS.md

Read `skills/PLAYBOOK.md` fully before taking any action.

Upstream source for the 0-to-1 Agent Skills framework (five roles, workflow playbook, CLI tooling, Notion integration).

Note: In this repo, skills live at `skills/` and paths in the PLAYBOOK are correct as-is. The `install.sh` script rewrites them to `.briefcase/skills/` for consumer projects.

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
