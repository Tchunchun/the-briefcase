# AGENTS.md

Read `skills/PLAYBOOK.md` fully before taking any action.

Upstream source for the 0-to-1 Agent Skills framework (five roles, workflow playbook, CLI tooling, Notion integration).

Note: In this repo, skills live at `skills/`. The PLAYBOOK references `.skills/` — the consumer path after install.

## Commands

| Task | Command |
|------|---------|
| Run all tests | `python3 -m pytest tests/` |
| Test one file | `python3 -m pytest tests/path/to/test_file.py` |
| Lint all | `ruff check src/ tests/` |
| Lint one file | `ruff check path/to/file.py` |
| Run CLI | `python3 -m src.cli.main <command>` |
| Format | `ruff format src/ tests/` |

Load `.env` before CLI commands that hit Notion:
```
export $(grep -v '^#' .env | xargs)
```

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
