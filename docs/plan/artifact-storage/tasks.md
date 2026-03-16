# Tasks — Artifact Storage (v2)

## Task List

### Phase 1 — Storage Abstraction & Local Backend

- [x] **T-001** Define `ArtifactStore` and `SyncableStore` protocols in `src/core/storage/protocol.py` with all method signatures from the Technical Approach. Add unit tests verifying protocol compliance.
- [x] **T-002** Implement config loader in `src/core/storage/config.py` — load/save `_project/storage.yaml`, validate schema, handle missing file (default to local). Add unit tests.
- [x] **T-003** Implement `LocalBackend` in `src/core/storage/local_backend.py` — all `ArtifactStore` methods reading/writing markdown files at canonical paths. Add unit + integration tests.
- [x] **T-004** Implement `get_store()` factory in `src/core/storage/factory.py` and `agent setup` CLI command in `src/cli/commands/setup.py` with backend selection (default: `local`). Creates `_project/storage.yaml`. Add integration tests.

### Phase 2 — Notion Backend

- [x] **T-005** Implement Notion API client wrapper in `src/integrations/notion/client.py` — thin layer over `notion-client` SDK for pages, databases, and blocks. Add integration tests with mocked HTTP.
- [x] **T-006** Implement Notion database schemas in `src/integrations/notion/schemas.py` and workspace provisioner in `src/integrations/notion/provisioner.py` — create page tree + 5 databases with defined schemas. Idempotent. Add integration tests with mocked HTTP.
- [x] **T-007** Implement `NotionBackend` in `src/integrations/notion/backend.py` — all `ArtifactStore` + `SyncableStore` methods backed by Notion API. Add integration tests with mocked HTTP.
- [x] **T-008** Extend `agent setup --backend notion` in `src/cli/commands/setup.py` — prompt for token + page ID, run provisioner, seed templates, write Notion config to `storage.yaml`. Add integration tests.
- [x] **T-009** Implement `agent sync local` in `src/cli/commands/sync.py` + `src/sync/to_local.py` — generate local markdown from Notion (append-only for inbox/decisions, overwrite for briefs/templates). Support `--dry-run`. Add integration tests.

### Phase 3 — Template Management in Notion

- [x] **T-010** Implement `agent sync templates` in `src/cli/commands/sync.py` — pull updated templates from Notion back to `template/`, compare versions before overwriting. Add integration tests.

## Review Findings

*Review agent — 2026-03-16*

### Blocking

1. **[Blocking] T-008: `agent setup --backend notion` does not call the provisioner.** The CLI saves the token and config but never invokes `NotionProvisioner.provision()`. This means acceptance criteria "provisions a full Notion workspace" and "provisioned workspace includes databases for: Intake, Feature Briefs, Decisions, Backlog, Templates" are not met end-to-end via the CLI. The provisioner code exists and is tested in isolation, but the setup command doesn't wire it in. — [src/cli/commands/setup.py](src/cli/commands/setup.py#L50)

2. **[Blocking] T-008: Setup does not seed templates during provisioning.** The acceptance criterion says "Templates from `template/` are seeded into the Notion Templates database during setup." The provisioner has `_seed_templates()`, but since setup doesn't call the provisioner, templates are never seeded. Must be wired into the setup CLI flow.

3. **[Blocking] T-008: Setup does not store database IDs in `storage.yaml`.** The acceptance criterion says "Setup stores Notion database IDs in `_project/storage.yaml`." The provisioner returns `database_ids` but setup never receives them. The saved config has `notion.databases: {}` (empty).

### Major

4. **[Major] T-009: No dedicated integration test for `agent sync local` or `agent sync templates` CLI commands.** The sync logic is tested through the `NotionBackend` tests, but the actual Click CLI commands (`sync_local`, `sync_templates`) have no test file at `tests/cli/integration/test_sync.py`. If the CLI wiring breaks, no test would catch it.

5. **[Major] No `conftest.py` or shared fixtures file.** `_project/testing-strategy.md` specifies "Use `tests/conftest.py` for shared fixtures." This file was never created. Each test file duplicates fixture setup. Not blocking but diverges from the testing strategy.

6. **[Major] `pytest-mock` and `responses`/`respx` listed in tech-stack but not used.** Tests use `unittest.mock` (stdlib) directly. Not wrong, but the tech stack doc implies these packages are part of the stack. Either use them or update the tech-stack.

### Minor

7. **[Minor] Protocol does not include a `delete` method.** OQ-1 resolution says "Operations: read(id), write(id, data), list(filters), delete(id)" but the `ArtifactStore` protocol has no `delete` method for any artifact type. Inbox and decisions are append-only (fine), but briefs/backlog/templates have no deletion path. Not needed for v1, but the protocol diverges from the documented resolution.

8. **[Minor] `setup.py` message says "Run again after provisioning" — confusing.** Since setup should *do* the provisioning, telling the user to "run again after provisioning" is misleading. This should be removed once provisioning is wired in.

9. **[Minor] Backlog notes for T-009 say "Sync logic + CLI implemented" but no CLI test exists.** Notes should reflect which tests validate the task.

### Out-of-Scope Check

- No out-of-scope items were implemented. ✓
- No unapproved dependencies. All imports resolve to `click`, `yaml`, `notion_client`, and stdlib. ✓
- No writes to `brief.md` or other ideation-owned files. ✓

### Regression Check

- 81/81 tests pass. No regressions. ✓

### Summary

**3 Blocking findings** must be resolved before acceptance — all related to T-008 (the setup CLI not calling the provisioner). The provisioner code and NotionBackend code are solid and well-tested individually; the gap is in the CLI wiring.

**Verdict: Not accepted.** Return to implementation agent to fix Blocking findings #1–#3, then add CLI sync tests for Major #4.

---

### Re-Review — 2026-03-16 (post-fix)

**Previous blocking findings — all resolved:**

| # | Finding | Resolution |
|---|---|---|
| 1 (Blocking) | Setup didn't call provisioner | **Fixed.** `setup.py` now calls `NotionProvisioner.provision()`, outputs summary. E2E confirmed: 5 DBs created. |
| 2 (Blocking) | Templates not seeded | **Fixed.** `template_dir` passed to provisioner. E2E confirmed: 9 templates seeded. |
| 3 (Blocking) | DB IDs not saved to `storage.yaml` | **Fixed.** `config.notion.databases = db_ids` + seeded versions saved. E2E confirmed: config round-trips correctly. |
| 4 (Major) | No CLI sync tests | **Fixed.** 5 tests in `tests/cli/integration/test_sync.py` (local rejection, notion sync, dry-run, template sync). |
| 5 (Major) | No `conftest.py` | **Fixed.** Shared `project_root` fixture in `tests/conftest.py`. |

**Previous major/minor findings — remaining status:**

| # | Finding | Status |
|---|---|---|
| 6 (Major) | `pytest-mock`/`responses` in tech-stack but unused | **Open (Minor).** Tests use `unittest.mock` which works fine. Recommend updating tech-stack to remove unused deps. Does not block acceptance. |
| 7 (Minor) | No `delete` method on protocol | **Open (Minor).** Not needed for v1. The documented OQ-1 resolution is aspirational; the implemented protocol covers all v1 use cases. |
| 8 (Minor) | Confusing "run again" message | **Fixed.** Message removed; setup now provisions in one pass. |
| 9 (Minor) | Backlog notes inaccurate | **Open (Minor).** Notes still say "Sync logic + CLI implemented" without referencing the new test file. Cosmetic. |

**E2E verification — both passed:**

- **Local backend E2E:** Setup → inbox CRUD → brief CRUD → decisions → backlog → templates → disk verification. 8/8 steps pass.
- **Notion backend E2E:** Provision (5 DBs + 9 templates) → inbox → brief → decisions → backlog → sync-to-local → template read → idempotency re-provision. 10/10 steps pass.

**Regression check:** 87/87 unit + integration tests pass. No regressions.

**Technology check:** All imports resolve to `click`, `yaml`, `notion_client`, `httpx` (transitive dep of `notion-client`), and stdlib. No unapproved dependencies.

**Out-of-scope check:** No out-of-scope items implemented. No writes to ideation-owned files.

### Verdict: **Accepted.**

All acceptance criteria across Phase 1, Phase 2, and Phase 3 are met. 3 minor findings remain (tech-stack doc cleanup, protocol delete method, backlog notes) — none block acceptance. Feature is ready to ship.

## Notes

- Tasks are ordered by dependency: T-001 → T-002 → T-003 → T-004 (Phase 1 chain), T-005 → T-006 → T-007 → T-008 → T-009 (Phase 2 chain), T-010 (Phase 3).
- Each task includes writing tests per `_project/testing-strategy.md`.
- Mock all Notion HTTP calls in CI; never use live API in automated tests.
- Do not introduce dependencies not listed in `_project/tech-stack.md`.
