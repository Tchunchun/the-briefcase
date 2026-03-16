# Tech Stack

## Language & Runtime
- **Python 3.11+** — primary language for CLI, storage backends, and sync logic
- **Click** — CLI framework for `agent` commands

## Storage Backends
- **Local filesystem** (markdown files) — default backend; no dependencies
- **Notion API** (`notion-client` Python SDK) — cloud backend for planning artifacts

## Testing
- **pytest** — test runner
- **pytest-mock** — mocking
- **responses** or **respx** — HTTP mocking for Notion API tests

## Infrastructure
- **GitHub** — source control
- **GitHub Actions** — CI/CD (planned)

## Conventions
- All folders use `kebab-case`
- Python code follows PEP 8; enforced by `ruff`
- Config files use YAML (`_project/storage.yaml`)
- API tokens stored in `.env` or environment variables, never committed to git
