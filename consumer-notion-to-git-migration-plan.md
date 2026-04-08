# Consumer Notion-to-Git Migration Plan

## Goal
Move an already-installed consumer project from the Notion backend to the git backend with minimal operator risk, preserved planning artifacts, and a clean post-cutover workflow.

## Scope
- In scope: briefs, backlog rows, decisions, inbox artifacts, local artifact hydration from Notion, storage config cutover, first git push, validation in a clean consumer workspace, and team rollout.
- Out of scope: deleting Notion data, rewriting historical Notion content, or changing the project’s source-code git workflow.

## Recommended Rollout Model
- Use a single planned cutover window for each consumer project.
- Freeze planning writes during the cutover. No one should edit Notion artifacts between the final sync pull and the first git push.
- Run the migration on a dedicated branch first, then merge after verification.

## Phase 1: Pre-Migration Checks
- [ ] Confirm the consumer project currently resolves to the Notion backend.
  Verify: `python -m src.cli.main backlog list --project-dir <project-root>` succeeds and the active config shows `backend: notion`.
- [ ] Confirm Notion credentials are still available.
  Verify: `.env` or environment contains `NOTION_API_KEY` or `NOTION_API_TOKEN`.
- [ ] Confirm git remote strategy.
  Decide whether the consumer will use a dedicated private artifact repo or a shared private artifact repo with a unique `project_slug` namespace.
- [ ] Confirm config-path state before migration.
  Verify: if both `_project/storage.yaml` and `.briefcase/storage.yaml` exist, they must match. Canonical precedence is `_project/storage.yaml`.
- [ ] Create a migration branch.
  Verify: `git checkout -b chore/migrate-planning-to-git` from the consumer project root.

## Phase 2: Backup and Dry Run
- [ ] Export a safety snapshot of the current config and planning files.
  Verify: copy `_project/storage.yaml`, `.briefcase/storage.yaml` if present, and any existing `docs/plan/` tree to a dated backup folder.
- [ ] Run the migration in dry-run mode.
  Verify:
  `python -m src.cli.main migrate notion-to-git --dry-run --remote-url <private-remote-url> --project-dir <project-root>`
- [ ] Review the dry-run outcome with the project owner.
  Verify: operator understands that the command will pull Notion data locally, rewrite storage config to `backend: git`, and then commit/push artifact files.

## Phase 3: Cutover Execution
- [ ] Announce a short write freeze for planning artifacts.
  Verify: no one is editing Notion backlog/briefs during the cutover.
- [ ] Run the real migration.
  Verify:
  `python -m src.cli.main migrate notion-to-git --remote-url <private-remote-url> --branch main --remote origin --project-dir <project-root>`
- [ ] Confirm the command completed all four steps successfully.
  Verify:
  - Notion pull completed with `failed = 0`
  - `_project/storage.yaml` now says `backend: git`
  - git remote is configured as expected
  - initial artifact push succeeded

## Phase 4: Post-Cutover Validation
- [ ] Validate local reads after cutover.
  Verify:
  - `python -m src.cli.main brief read <brief-slug> --project-dir <project-root>`
  - `python -m src.cli.main backlog list --project-dir <project-root>`
- [ ] Validate roundtrip in a clean consumer workspace.
  Required acceptance gate. Verify with the shakedown command:
  `python -m src.cli.main sync shakedown-git --brief-name <brief-slug> --feature-title "<feature-title>" --expected-status <status> --project-dir <project-root>`
- [ ] Validate current workflow fields for one actively routed feature if applicable.
  Verify expected `review_verdict`, `route_state`, and `lane` via `sync shakedown-git` options.
- [ ] Inspect the artifact repo namespace.
  Verify: the remote contains `docs/plan/` and `_project/` under the expected project namespace.

## Phase 5: Team Rollout
- [ ] Tell the team the source of truth has changed.
  Verify: operators know Notion is no longer the active backend for this consumer project.
- [ ] Switch team habits to git sync.
  Verify team uses:
  - `python -m src.cli.main sync pull --project-dir <project-root>` before work
  - `python -m src.cli.main sync push --project-dir <project-root>` after artifact updates
- [ ] Remove obsolete Notion secrets after the project is stable on git.
  Verify: remove `NOTION_API_KEY` from `.env` only after cutover is confirmed.
- [ ] Preserve Notion as read-only historical backup for an agreed period.
  Verify: do not delete the old Notion workspace immediately.

## Recommended Success Criteria
- [ ] A clean workspace can pull and read the migrated brief and backlog artifacts.
- [ ] `_project/storage.yaml` is canonical and set to `backend: git`.
- [ ] Team workflow no longer depends on Notion credentials.
- [ ] At least one active feature survives a git roundtrip with expected workflow fields.
- [ ] `sync shakedown-git` passes before the migration branch is merged.

## Rollback Plan
- If the migration fails before storage rewrite: keep Notion as the active backend and fix the pull/precheck issue.
- If the migration fails after storage rewrite but before successful push: restore the saved `_project/storage.yaml` backup, revert the migration commit, and keep Notion as source of truth.
- If the first push succeeds but validation fails: do not resume team writes yet. Fix the artifact issue on the migration branch, rerun `sync shakedown-git`, then merge.
- Do not delete Notion data during the same maintenance window as the cutover.

## Known Operational Notes
- Current config resolution treats `_project/storage.yaml` as canonical and `.briefcase/storage.yaml` as fallback. If both files exist and differ, commands will fail with a config mismatch error.
- The migration command is non-destructive to Notion data. It copies artifacts out of Notion and switches the active backend to git.
- The strongest validation after migration is a clean-consumer pull plus `sync shakedown-git`, not just local file inspection.

## Minimal Operator Runbook
1. Freeze planning writes.
2. Create migration branch.
3. Run `migrate notion-to-git --dry-run`.
4. Run `migrate notion-to-git`.
5. Run `sync shakedown-git` against one known brief/feature. Do not merge until this passes.
6. Merge the branch and announce git as the new planning backend.