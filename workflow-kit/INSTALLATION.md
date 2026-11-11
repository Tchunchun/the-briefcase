# Workflow-kit installation path

The current workflow kit is intentionally not installed by the repository-root
`install.sh`; that installer remains the supported legacy five-role product.
Do not extend it with workflow-kit files or mode selection.

## New-project defaults

Use [the manifest template](templates/workflow.yaml) for each new workflow-kit
instance, rather than copying this repository's configured manifest. Once the
kit assets are present in the target checkout, copy the template to
`workflow-kit/workflow.yaml` only if no configured manifest exists. Set the
profile (`standard` or `lite`), repository, Project owner/number, and private
artifact repository/root for that project. The template's `contract.yaml` path
is relative to this destination, not the template's source directory.

The template includes `project.fields.pull_request: Linked pull requests` by
default. Use GitHub's existing native field, not a custom PR URL text field.
Show it on item cards and task/review views. Build links the PR from the issue's
Development sidebar and verifies the native field before handoff; Notes is not
the PR locator. This default applies to both Standard and Lite. The issue
sidebar supports selecting a PR in another repository.

Run `python3 workflow-kit/runtime.py --offline` in the target checkout, then
the read-only live preflight after the board is configured. A missing native PR
field fails preflight for a manifest that configures it; preflight never creates
the field. Existing manifests and boards are not automatically migrated.
These are manual setup assets, not a new installer or CLI initialization command.

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
- the new-project manifest defaults, including native `Linked pull requests` and its
  `project.fields.pull_request` mapping;
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
