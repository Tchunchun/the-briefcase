**Status: implementation-ready**

---

## Problem
Briefs are stored as child pages under a container page in Notion. This means no structured properties (status, date, linked feature, author), no sorting, no filtering, and no grouping. Users cannot see brief status or date at a glance on the Notion page — they must open each brief individually. The CLI works around this by parsing markdown content, but the Notion experience is a flat, unsortable list.

## Goal
Migrate briefs from child pages under a container page to a proper Notion database. Each brief becomes a database row with structured properties (Name, Status, Date, Linked Feature, Author) while keeping the brief body as page content. The Notion page becomes a sortable, filterable, groupable table. The CLI brief commands (list, read, write) continue to work transparently.

## Acceptance Criteria
- [ ] A BRIEFS_SCHEMA is defined in schemas.py with properties: Name (title), Status (select: draft/implementation-ready), Slug (rich_text for exact matching), Date (date), Linked Feature (url), Author (rich_text)
- [ ] BRIEFS_SCHEMA is registered in DATABASE_REGISTRY
- [ ] Provisioner creates a Briefs database instead of a Briefs container page for new projects
- [ ] Provisioner detects existing Briefs page and handles upgrade path
- [ ] backend.py write_brief creates database rows (not child pages) with structured properties
- [ ] backend.py read_brief reads from database rows, returning the same data shape as today
- [ ] backend.py list_briefs queries the database with sort by Date descending, returning name, status, date, notion_id per entry
- [ ] Brief body content (Problem, Goal, AC, etc.) is stored as page content blocks on the database row page
- [ ] Brief history/revision pages remain as children of the brief database row page
- [ ] briefcase brief list CLI output is human-readable: grouped by date with section headers, showing name + status per line
- [ ] Migration command: briefcase brief migrate moves existing child-page briefs into the new database, preserving name, status, date, and page content
- [ ] Migration handles briefs with history pages (history pages move to be children of the new database row)
- [ ] Migration is idempotent — running it twice does not create duplicates
- [ ] All existing brief CLI commands (list, read, write, history, revision, restore) work after migration

## Non-Functional Requirements
No new external dependencies. Must be backward compatible with local backend (no changes to local_backend.py). Migration must be idempotent. Provisioner remains idempotent.

## Out of Scope
Changing the local backend storage format. Adding database views beyond the default table. Notion relations (using URL properties for Feature links instead). Changing the brief write CLI command interface.

## Open Questions
All resolved during architect review (D-051):
1. Migration trigger: Separate briefcase brief migrate command. Keeps provisioning fast, gives user control over when migration happens.
2. Old Briefs page: Rename to "Briefs (archived)" after migration. Keep as fallback — do not delete.
3. Matching: Add a Slug rich_text property to the database for exact brief-name matching. Name (title) is the display title. Slug is the kebab-case identifier used by _find_brief_page and CLI commands.

## Technical Approach
Five implementation phases, each a separate commit:

**Phase 1 — Schema definition (schemas.py)**
Add BRIEFS_SCHEMA to schemas.py following the backlog/decisions pattern:
- Name (title): display title
- Slug (rich_text): kebab-case brief identifier for exact matching
- Status (select): draft, implementation-ready
- Date (date): last-modified date
- Linked Feature (url): URL to the linked Feature backlog row
- Author (rich_text): who created the brief
Register in DATABASE_REGISTRY as "briefs_db" (key distinct from the existing "briefs" page key).

**Phase 2 — Provisioner update (provisioner.py)**
- For new projects: replace _provision_page("briefs",...) with _provision_database("briefs_db",...)
- For existing projects: provisioner detects whether briefs is a page or database via config. If config has old page ID, skip — migration is a separate command.
- Update the provisioned layout docstring.

**Phase 3 — Backend rewrite (backend.py)**
Rewrite brief methods to use database API:
- _briefs_db_id(): read from config (replaces _briefs_page_id for database mode)
- _is_briefs_database(): check if briefs storage is database or page (for backward compat during migration window)
- write_brief: create_database_page with properties (Name, Slug, Status, Date) + page content blocks. If existing, update properties via update_database_page + replace body.
- read_brief: query_database filtered by Slug, read page content blocks, parse sections. Return same dict shape.
- list_briefs: query_database sorted by Date descending. Extract properties directly (no markdown parsing needed for status/date). Return same list shape.
- _find_brief_page: query_database with Slug filter instead of scanning child blocks.
- History/revision methods: unchanged — they operate on child pages of the brief page, which works the same for database row pages.

**Phase 4 — CLI human-readable output (brief.py)**
- brief_list: replace output_json with formatted text output.
- Group by date, print section headers (── YYYY-MM-DD ──), print name + status per line with column alignment.

**Phase 5 — Migration command (brief.py or new migrate.py)**
- briefcase brief migrate command:
  1. Read all child pages from old Briefs container page
  2. For each brief: extract name, status, date, page content blocks
  3. Create database row with properties + content
  4. Move history pages to be children of the new database row page (via update_page parent)
  5. Rename old Briefs page to "Briefs (archived)"
  6. Update storage.yaml to point briefs key to new database ID
- Idempotency: check if Slug already exists in database before creating

No changes to local_backend.py, protocol.py, or CLI command interfaces.
