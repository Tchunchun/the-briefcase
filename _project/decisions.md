# Architectural Decisions

Append-only log. Record what was decided, why, and what alternatives were rejected.

| Date | Decision | Why | Alternatives Rejected |
|---|---|---|---|
| 2026-03-12 | Adopt `src/` layout with `package-dir` mapping | Align repo to AGENTS.md prescribed structure; `package-dir` keeps import paths clean without `src.` prefix | Flat layout (status quo); full `src.*` prefix (more import churn) |
| 2026-03-12 | Place `adapters/` under `src/adapters/` alongside `src/core/` | Adapters are cross-cutting channel interfaces, not features; matches shared-infrastructure role of `core/` | Top-level `adapters/` outside `src/` (breaks prescribed structure) |
| 2026-03-12 | Separate `tests/` from `src/` at top level | AGENTS.md requires `tests/` mirroring `src/`; enables cleaner packaging (tests excluded from distribution) | Co-located tests inside feature folders (previous layout) |
