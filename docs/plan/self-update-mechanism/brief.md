**Status: implementation-ready**

---

## Problem
Consumer projects that install the-briefcase via install.sh get a frozen snapshot. When the framework ships new skills, bug fixes, template updates, or CLI improvements, consumers have no way to pull those updates. The only option is manually copying files — error-prone and nobody does it. The existing 'briefcase upgrade' command only repairs Notion schemas; it doesn't update framework code.

## Goal
A single 'briefcase update' command that pulls the latest framework version into a consumer project, updates all framework-owned files, preserves consumer customizations, and reports what changed — so consumers stay current with zero manual file copying.

## Acceptance Criteria
- [ ] New CLI command: briefcase update (separate from existing briefcase upgrade which handles Notion schema)
- [ ] Detects current installed version by reading .briefcase/VERSION file (written at install time)
- [ ] Fetches latest version from the source repo (GitHub release tag or VERSION file in repo)
- [ ] Displays changelog diff: what changed between current and latest (new skills, bug fixes, breaking changes)
- [ ] User confirms before applying (--yes flag to skip confirmation)
- [ ] Updates framework-owned files: .briefcase/src/, .briefcase/skills/, .briefcase/template/, .briefcase/pyproject.toml
- [ ] Re-runs the sed path rewrite (skills/ → .briefcase/skills/) on updated skill files, same as install.sh does
- [ ] Reinstalls Python dependencies in .briefcase/.venv/ if pyproject.toml changed
- [ ] Preserves consumer-owned files: AGENTS.md, CLAUDE.md, _project/, docs/plan/, .briefcase/storage.yaml, .env
- [ ] Detects local customizations to framework-owned skill files and warns (does not silently overwrite)
- [ ] Writes .briefcase/VERSION with the new version after successful update
- [ ] install.sh writes .briefcase/VERSION at install time (currently missing)
- [ ] --check flag: shows what would change without applying
- [ ] Exit codes: 0 = up to date or update applied, 1 = error, 2 = update available but user declined
- [ ] Works for both local-clone installs and future remote installs (GitHub URL)

## Non-Functional Requirements
- **Expected load / scale:** Single user, run occasionally (weekly/monthly)
- **Latency / response time:** < 30s for full update including dependency install
- **Availability / reliability:** Must handle network failures gracefully (GitHub unreachable = clear error, not corruption)
- **Cost constraints:** No new paid services; uses GitHub API (unauthenticated or existing token)
- **Compliance / data residency:** No PII; only fetches public repo data
- **Other constraints:** Must not break mid-update (atomic: either fully applied or rolled back). Must work without git installed in the consumer project (consumer project may not be a git repo). Must not modify consumer's git history.

## Out of Scope
- Auto-update on every CLI invocation (user must explicitly run briefcase update)
- Migration scripts for breaking changes (changelog warns, user handles manually)
- Updating AGENTS.md or CLAUDE.md content (those are consumer-owned after install)
- Plugin/extension marketplace
- Rollback to a previous version (user can re-run install.sh from an older tag)
- Notion schema migrations (that's the existing briefcase upgrade command's job)

## Open Questions
All resolved by architect:

1. Update source: GitHub release tarball. Use the GitHub API to fetch the latest release tarball (no auth required for public repos). This avoids requiring git in the consumer project and gives us versioned, immutable snapshots. The CLI downloads to a temp directory, extracts, copies framework files, then cleans up. Falls back to local clone path if FRAMEWORK_DIR is set (for development).

2. Customization detection: Manifest file (.briefcase/manifest.json). Written at install/update time, contains SHA-256 hashes of every framework-owned file. On next update, compare current file hashes against manifest. If a file has been modified by the consumer, warn and skip (or --force to overwrite). This works without git and is deterministic.

3. Versioning strategy: Single framework version. The VERSION file and pyproject.toml version move in lockstep. Per-skill versioning adds complexity with no clear benefit at current scale. If needed later, the manifest already tracks per-file hashes.

4. Changelog location: CHANGELOG.md in the repo root, included in the GitHub release body. The update command displays the release body (which includes the changelog entries) during the confirmation prompt.

5. Chain upgrade after update: Yes, automatically. After updating framework code, run the Notion schema health check (not full upgrade). If issues are found, suggest running briefcase upgrade. This catches cases where new framework code expects new schema fields.

## Technical Approach
### Architecture

Three components: version tracking, update fetch, and atomic apply.

#### 1. Version Tracking

**`.briefcase/VERSION`** — plain text file containing the semver version string (e.g., `0.8.0`).
- Written by `install.sh` at install time (new step, currently missing)
- Written by `briefcase update` after successful update
- Read by `briefcase update --check` to determine current version

**`.briefcase/manifest.json`** — JSON file mapping relative file paths to SHA-256 hashes:
```json
{
  "version": "0.8.0",
  "files": {
    "src/cli/main.py": "a1b2c3...",
    "skills/ideation/SKILL.md": "d4e5f6...",
    ...
  }
}
```
- Written by `install.sh` and `briefcase update` after copying files
- Used to detect local customizations before overwriting

#### 2. New CLI Command: `src/cli/commands/update.py`

```
briefcase update [--check] [--yes] [--force] [--source URL]
```

Flow:
1. Read `.briefcase/VERSION` for current version
2. Fetch latest release from GitHub API: `GET /repos/{owner}/{repo}/releases/latest`
3. Compare versions. If current >= latest, exit 0 ("up to date")
4. Display: version diff, release body (changelog), list of files that will change
5. If `--check`, exit here (exit 2 if update available)
6. Prompt for confirmation (skip with `--yes`)
7. Download release tarball to temp directory
8. Extract and compare against manifest — flag customized files
9. If customized files found and no `--force`, list them and abort
10. Apply update atomically (see below)
11. Write new VERSION and manifest.json
