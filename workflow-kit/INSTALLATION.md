# Workflow-kit installation path

The current workflow kit is intentionally not installed by the repository-root
`install.sh`; that installer remains the supported legacy five-role product.
Do not extend it with workflow-kit files or mode selection.

## Pilot boundary

Before building a workflow-kit installer:

1. Validate `contract.yaml` and the repository manifest locally.
2. Run the read-only live preflight against one named private pilot.
3. Run that pilot from capture through independently reviewed, verified
   closeout.
4. Record contract, configuration, privacy, and recovery defects.
5. Stabilize the contract before encoding installation or upgrade behavior.

The preflight never repairs a Project. Any field creation, option rename,
backlog conversion, or mode conversion is a separately reviewed migration.

## Planned installer

After the pilot passes, add a separate workflow-kit installer with:

- explicit Lite or Standard selection;
- existing-install and version detection;
- manifest creation from user-supplied repository, Project, and artifact data;
- `gh` authentication plus the same read-only preflight;
- dry-run output and an exact mutation preview for any optional setup step;
- a managed-section merge for `AGENTS.md` that preserves user-owned content;
- profile-specific asset installation;
- installed-version and managed-file hashes;
- idempotent reinstall/update and interruption recovery;
- an explicit migration path for legacy Briefcase consumers;
- post-install verification and a first-loop prompt without automatic dispatch.

It must never silently create or rename Project fields, convert a backlog,
change modes, replace repository instructions, publish private artifacts, or
start a workflow loop.
