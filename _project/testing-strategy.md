# Testing Strategy

---

## Test Types and Scope

| Type | What it covers | Tool / location |
|---|---|---|
| **Unit** | Individual functions, classes, pure logic | pytest · `tests/{module}/unit/` |
| **Integration** | Component interactions, I/O boundaries (file system, HTTP/API) | pytest · `tests/{module}/integration/` |
| **End-to-End** | Full CLI commands in the target environment | pytest · `tests/{module}/e2e/` |

Not every module requires all three. Use the table below to decide.

## Coverage Priorities

| Code category | Minimum required | Notes |
|---|---|---|
| Storage interface + backends (core logic) | Unit + Integration | Must run in CI |
| Notion API client | Integration | Mock HTTP responses in CI; use real API in staging |
| CLI commands | Integration or E2E | At least one happy-path test per command |
| Sync logic (dedup, conflict handling) | Unit + Integration | Critical path — test edge cases |
| Template seeding | Unit | Verify correct rendering |
| Config loading (`storage.yaml`) | Unit | |

## What "Relevant Test Scope" Means

When the implementation guideline says "run the relevant test scope":
1. Run unit tests for any file you touched.
2. Run integration tests for any boundary (file system, Notion API, CLI) you touched.
3. Run E2E tests before shipping a feature.

## Test Data and Fixtures

- Use `tests/conftest.py` for shared fixtures.
- Never use production credentials or live external services in unit or integration tests.
- Mock Notion API responses using `responses` or `respx`.
- Fixture files (sample YAML, JSON, markdown) belong in `tests/fixtures/`.

## CI Gate

All unit and integration tests must pass before a task can be marked Done.
E2E tests are required before a feature ships (Phase 5 in PLAYBOOK.md).

---

*Update this file via the architect agent when the stack or test tooling changes. Log the change in `_project/decisions.md`.*
