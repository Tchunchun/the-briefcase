# Global Tech Stack

## Product Shape

- Repository type: Python monorepo for personal AI agents
- Primary surfaces: CLI and Discord
- Planning workflow: `docs/plan/` is the active source of truth; `docs/plan/_reference/` holds historical/reference material

## Backend

- Language: Python 3.12+
- CLI framework: Typer
- Validation/models: Pydantic v2
- HTTP client: httpx
- Config: YAML + python-dotenv
- LLM provider: Azure OpenAI via the `openai` Python SDK
- Storage backends: Notion, JSON, Google Calendar backend in progress

## Agents

- Agent layout: `src/<agent>/`
- Agent tests: `tests/<agent>/`
- Shared infrastructure: `src/core/`
- Channel adapters: `src/adapters/`
- Package root: `src/` (mapped via `pyproject.toml` `[tool.setuptools.package-dir]`)

## Infrastructure

- Packaging: `pyproject.toml`
- Dependency manager: `uv`
- Containers: Docker / docker-compose
- Deployment target: Azure Container Apps
- Lint/format: Ruff
- Test runner: pytest

## Conventions

- `brief.md` is the source of truth for feature scope.
- `tasks.md` is the source of truth for feature execution state.
- `docs/plan/_shared/backlog.md` is the cross-feature execution view.
- Release notes live under `docs/plan/_releases/v{version}/release-notes.md`.
- Long-form proposals, PRDs, and exploratory design docs belong under `docs/plan/_reference/`.
