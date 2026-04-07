# Release Notes Notion Backend
**Status: implementation-ready**
---
## Problem
Release notes are always written to local files (`docs/plan/_releases/v{version}/release-notes.md`) even when the project backend is Notion. The `ArtifactStore` protocol has no release notes methods, so the Notion backend is structurally incomplete and release history is invisible in Notion.
## Goal
Release notes are written to Notion as standalone child pages linked from a Release Notes section on the main project overview page. Agents can write, read, and list release notes via CLI regardless of backend.
## Acceptance Criteria
- [ ] `ArtifactStore` protocol defines `write_release_note`, `read_release_note`, and `list_release_notes` methods
- [ ] Notion backend implements all three methods: each release note is a standalone Notion page
- [ ] Release notes pages are linked from a `Release Notes` section on the main project overview page; the section is created automatically on first write
- [ ] Each link in the Release Notes section is a titled bullet pointing to the release note page (for example, `v0.4.0 Release Notes`)
- [ ] CLI exposes `agent release write --version v0.x.0 --notes '...'`, `agent release read --version v0.x.0`, and `agent release list`
- [ ] `agent release write` is called automatically by the implementation agent at ship time (documented in `skills/implementation/SKILL.md`)
- [ ] Local backend preserves existing behavior by writing release notes to `docs/plan/_releases/v{version}/release-notes.md`
- [ ] All three CLI commands work end-to-end against a live Notion backend in manual testing
- [ ] Unit tests cover Notion backend methods with mocked API responses
## Out of Scope
Editing or deleting existing release notes; versioning or diffing release note content; release notes in any format other than plain text/markdown; migrating previously created local release note files to Notion
## Open Questions
All resolved. Store and use the existing README page ID from Notion config, and render release-note links as bulleted list items rather than toggles.
## Technical Approach
### Storage contract
Extend `ArtifactStore` with:
- `write_release_note(version: str, content: str) -> None`
- `read_release_note(version: str) -> dict`
- `list_release_notes() -> list[dict]`
The version string is the primary key. `read_release_note()` returns at least `{version, title, content}` and backend-specific metadata like `notion_id` when available.
### Local backend
`LocalBackend` preserves the current release-note convention:
- Path: `docs/plan/_releases/{version}/release-notes.md`
- `write_release_note()` creates the version folder if needed and overwrites the file for that version
- `read_release_note()` reads the markdown body
- `list_release_notes()` enumerates version folders under `docs/plan/_releases/`
This keeps shipped local behavior stable while bringing the API surface up to parity with Notion.
### Notion backend
Release notes are stored as standalone child pages under the existing project root page, matching the current brief-page pattern.
- Page title convention: `{version} Release Notes`
- Page location: direct child of `parent_page_id`
- Page body: markdown converted to Notion blocks via the same simplified block conversion already used for briefs/templates
- Lookup: `list_release_notes()` scans child pages under the project root and filters titles matching the release-note convention
This avoids introducing a dedicated Releases database for a low-volume artifact and reuses the existing page-oriented Notion structure.
### README index
Use the provisioned README page as the canonical overview page. The ID should be read from `config.notion.databases["readme"]`; if missing from config but the page exists under the project root, backend setup code may discover and cache it.
On first write:
1. Ensure the README page contains a `## Release Notes` heading
2. Insert a bulleted list item under that section linking to the release-note page
3. Avoid duplicate bullets for the same version
Bulleted list items are the chosen block type because they are scan-friendly, match the current README style, and avoid nesting friction that toggles would introduce.
### CLI surface
Add a new `release` command group:
- `agent release write --version v0.x.0 --notes "..."`
- `agent release read --version v0.x.0`
- `agent release list`
These commands follow the same JSON envelope conventions as the existing artifact CLI commands. `write` is idempotent by version: if the page already exists, replace its content and ensure the README index entry still points to it.
### Implementation notes
Required code changes:
- `src/core/storage/protocol.py` — add release-note methods
- `src/core/storage/local_backend.py` — implement local release-note storage
- `src/integrations/notion/backend.py` — implement release-note page CRUD and README index maintenance
- `src/cli/main.py` and `src/cli/commands/release.py` — register the new CLI group
- `skills/implementation/SKILL.md` — document ship-time invocation
The Notion backend will need a helper that can replace existing child blocks on a page, because release-note updates are not append-only.
### Tests
Minimum required coverage:
- Unit tests for local release-note read/write/list behavior
- Unit tests for Notion backend release-note lookup and README index maintenance using mocked client responses
- CLI integration tests for `agent release write/read/list`
- Live manual Notion verification for write, rewrite, list, and README index linking
### Cost and dependency impact
No new dependencies are required. The feature stays within the existing Python + Click + notion-client/httpx stack and should add only a small number of Notion API calls per ship event.
