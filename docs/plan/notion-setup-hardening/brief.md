**Status: implementation-ready**

---

## Problem
Notion backend setup has three gaps: (1) docs/plan/ directory is created even when backend=notion, adding stale/confusing local files, (2) setup does not validate that the configured parent page exists and the token has access before provisioning databases, causing cryptic failures, (3) README seed text written to Notion contains malformed characters.

## Goal
Notion setup is clean and robust: docs/plan/ only created for local backend, preflight check validates parent page access with actionable error on failure, and README seed content is sanitized/normalized.

## Acceptance Criteria
- [ ] docs/plan/ directory NOT created when storage.yaml backend=notion
- [ ] docs/plan/ IS created when backend=local (existing behavior preserved)
- [ ] Preflight check validates parent_page_id is accessible via Notion API before provisioning
- [ ] Preflight failure produces actionable error message
- [ ] README seed text uses correct emoji for Briefs line
- [ ] Existing provisioner idempotency preserved
- [ ] Changes covered by unit tests

## Non-Functional Requirements
Preflight check adds no more than 1 extra API call. No new dependencies.

## Out of Scope
install.sh changes (separate brief). Notion API retry/rate-limit logic. Database schema changes.

## Open Questions


## Technical Approach
Files: install.sh (conditional docs/plan), src/integrations/notion/provisioner.py (preflight + emoji fix), src/cli/commands/setup.py (preflight call)

1. Conditional docs/plan (install.sh:166-175): Wrap mkdir/cp in backend check. Read .briefcase/storage.yaml; skip if backend != local.

2. Preflight parent access (provisioner.py): Add preflight method calling self._client.get_page(parent_page_id). On 404/403, raise clear error before provisioning. Call at start of provision().

3. Malformed emoji fix (provisioner.py:308): Replace malformed character with correct emoji. Audit all emoji literals.

Testing: Unit tests for preflight (mock 404/403), test docs/plan conditional, test emoji correctness.
