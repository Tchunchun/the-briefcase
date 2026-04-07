# Skills Distribution Implementation Plan

## Objective

Enable other repositories to reliably consume and update agent skills maintained in this repository, with clear versioning, low drift risk, and predictable rollback.

## Scope

- Source repo: this repository (upstream skills owner)
- Consumer repos: any project using Claude Code and/or Codex
- Deliverable: repeatable distribution and update workflow for skills

## Recommended Distribution Model

Use this repository as upstream and distribute skills to other projects via a pinned Git reference.

- Preferred: `git submodule` (clear pinning + explicit update)
- Alternative: `git subtree` (no submodule UX, but heavier history)
- Avoid: manual copy/paste

## Target Structure

In this upstream repo:

```text
.skills/
  skills/
    ideation/SKILL.md
    architect/SKILL.md
    implementation/SKILL.md
    review/SKILL.md
scripts/
  validate-skills.sh
  release-skills.sh
CHANGELOG-skills.md
```

In each consumer repo:

```text
vendor/agent-skills/   # submodule checkout of upstream repo
AGENTS.md              # points skill paths to vendor/agent-skills/.skills/skills/...
scripts/sync-skills.sh
```

## Phased Implementation Plan

## Phase 1: Stabilize Upstream (this repo)

1. Confirm each skill has a single canonical `SKILL.md`.
2. Add `CHANGELOG-skills.md` for release notes specific to skills.
3. Add `scripts/validate-skills.sh`:
   - checks required files exist
   - checks no missing `SKILL.md`
   - checks optional metadata frontmatter is present/valid (if required)
4. Define semantic version policy:
   - Patch: wording/clarity only
   - Minor: additive behavior
   - Major: breaking behavior/contract changes

Exit criteria:

- Validation script passes locally and in CI.
- First tagged skills release is published (for example `skills-v0.1.0`).

## Phase 2: Prepare Consumer Template

1. Add upstream as submodule in one pilot consumer repo:

```bash
git submodule add <upstream-repo-url> vendor/agent-skills
git submodule update --init --recursive
```

2. Update consumer `AGENTS.md` to reference skills from:
   - `vendor/agent-skills/.skills/skills/...`
3. Add `scripts/sync-skills.sh` in consumer repo:
   - fetch tags from submodule
   - checkout target tag/commit
   - run validator
4. Document upgrade procedure in consumer `README.md`.

Exit criteria:

- Pilot repo can bootstrap and resolve all skill paths from vendored upstream.
- Team can update to a newer tag in one command/script.

## Phase 3: Roll Out to All Repos

1. Apply same pattern to remaining consumer repos.
2. Add CI check in each consumer repo:
   - submodule initialized
   - validator passes
   - pinned ref recorded in PR
3. Add ownership rule:
   - designated approver for skills changes
   - required changelog entry per release

Exit criteria:

- All target repos consume skills from pinned upstream references.
- No repo depends on manual copied skill files.

## Phase 4: Operationalize Upgrades

1. Release cadence:
   - regular (e.g., biweekly) or event-driven
2. Upgrade routine per consumer:
   - bump submodule ref to released tag
   - run validation
   - run smoke workflow
3. Rollback routine:
   - reset submodule to previous known-good tag

Exit criteria:

- Upgrade and rollback each take less than 15 minutes per repo.

## Governance and Safety

- Single source of truth: upstream repo only
- Explicit pinning: consumer repos never track `main` directly in production workflows
- Release notes required: every skills release documents changes and risk
- Compatibility note required for every breaking change

## Suggested CI Checks

Upstream CI:

- `scripts/validate-skills.sh`
- lint markdown files under `.skills/skills/`

Consumer CI:

- submodule present and initialized
- all skill paths referenced by `AGENTS.md` exist
- vendored skills validator passes

## Risks and Mitigations

- Drift between repos
  - Mitigation: pinned refs + CI path validation
- Breaking behavior in prompt logic
  - Mitigation: semver + changelog + pilot upgrade first
- Submodule friction for contributors
  - Mitigation: `make init` or bootstrap script that initializes submodules automatically

## Execution Checklist

- [ ] Add `CHANGELOG-skills.md` to upstream
- [ ] Implement `scripts/validate-skills.sh`
- [ ] Create first tagged skills release
- [ ] Pilot one consumer repo with submodule-based sync
- [ ] Add consumer CI checks
- [ ] Roll out to all target repos
- [ ] Publish maintainer runbook (upgrade + rollback)

## Decision Log (for approval)

- Distribution mechanism: `submodule` (default)
- Versioning: semantic versioning via release tags
- Upgrade model: opt-in per consumer repo via pinned bump PR
- Rollback model: revert to previous tag
