# Unified Briefcase: GitHub First

This is the new product path, developed separately from the
[legacy framework](../LEGACY.md). Standard and Lite will share one workflow
core; Standard adds architecture and release records.

## Current Increment

The [GitHub setup script](../scripts/setup-github.sh) implements the first
onboarding gate. It does **not** install agent instructions or claim the
complete new product is ready.

The order is:

1. Select the repository and Project, and verify authenticated access.
2. Verify or explicitly initialize the backlog schema.
3. Link the repository and read back the setup.
4. Only after success may a future installer write workflow assets.

Only Git and an authenticated GitHub CLI (`gh`) are needed for this script.
It does not install Python, the Briefcase CLI, or packages. Agent clients and
application-specific build tools are separate requirements.

## Standard Setup

Preview an existing Project without changing local files or GitHub:

```bash
bash scripts/setup-github.sh --mode standard \
  --repo OWNER/REPOSITORY --owner OWNER --project NUMBER
```

Apply to a compatible Project:

```bash
bash scripts/setup-github.sh --mode standard \
  --repo OWNER/REPOSITORY --owner OWNER --project NUMBER --apply
```

Create a new private Project, or locate an existing one by exact title:

```bash
bash scripts/setup-github.sh --mode standard \
  --repo OWNER/REPOSITORY --owner OWNER \
  --create-project --title 'Briefcase Standard' --apply
```

The default is preview; only `--apply` permits remote mutations. Omit
`--apply` to preview creation and fields. `--dry-run` explicitly selects preview
and cannot be combined with `--apply`.

The shared Status values are **Inbox, Shaping, Ready, In progress, In review,
Blocked, Done**. Standard additionally requires:

| Field | Values / purpose |
|---|---|
| Work Type | Idea, Feature, Task |
| Priority | High, Medium, Low |
| Stage | Requirements, Architecture, Build, Review, Deliver |
| Review Verdict | Pending, Accepted, Changes requested, Blocked |
| Brief Link | Text link to the authoritative requirement |
| Release Note Link | Text link to release evidence |

Stage and Review Verdict are supporting information, not additional execution
backlogs. New fields start unset; setup does not infer approvals or move cards.
The Project's view layout and card-visible fields still need to be configured
in GitHub; this increment verifies schema, not a fully configured visual board.

## Safety and Recovery

- Repository Issues must be enabled and the caller must have write access.
- The caller must be able to update the selected open Project.
- New Projects are private by default. Existing public Projects require
  `--allow-public-project` before applying schema/link changes. No requirement
  content, code, issue, or card is published by this script.
- Existing incompatible fields stop setup. Populated Status fields are never
  reset. Migrate legacy Projects through a separate previewed operation.
- For an empty Project only, `--initialize-empty` explicitly permits replacing
  its initial Status options. New Projects created by this invocation get
  the shared Status options automatically.
- Other existing fields must have compatible types/options; setup does not
  delete fields, cards, options, or repositories.
- After partial failure, use the reported Project number to retry. Missing
  fields are created idempotently; successful earlier mutations are reported,
  not silently rolled back. New-project Status initialization can be retried
  on an empty Project with `--initialize-empty`.
- GitHub failures stop the phase with an error. There is no local-status
  fallback and no workflow files are written.

GitHub becomes the planning authority only through the user's explicit
selection and confirmed setup, not because a similarly named Project exists.
The script requires a repository, owner, mode, and either Project number or
an explicit create request; it never chooses a target from the current folder.
