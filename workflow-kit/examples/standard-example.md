# Standard profile example

This example shows all required artifacts for one Standard Feature with two
child Tasks. A single requirement revision is the only scope authority throughout.

---

## Requirement packet (Feature)

- Work item: `https://github.com/owner/repo/issues/42`
- Profile: `Standard`
- Parent: none
- Canonical requirement: `docs/requirements/feat-42.md @ sha:a1b2c3d`
- Approval: `@user, 2026-11-01T10:00Z, https://github.com/owner/repo/issues/42#issuecomment-100`

### Context and outcome

Admin users cannot filter the audit log by date range. They must scroll through
hundreds of rows to find relevant entries.

### Scope

- Add a date-range filter to the audit log API endpoint.
- Add a UI date picker to the audit log page.

### Exclusions

- Export to CSV is excluded from this Feature.

### Acceptance and verification

| Criterion | Observable result | Check | Owner |
|---|---|---|---|
| AC-01 | API returns only entries within the date range | `pytest tests/api/test_audit.py::test_date_range_filter` | Build |
| AC-02 | UI date picker is visible and applies the filter | Manual smoke test with screenshots | Build |

### Dependencies and questions

- Blockers: none
- Open questions: none
- Privacy/visibility: audit log data is internal only

---

## Standard brief (Architect sign-off)

- Work item: `https://github.com/owner/repo/issues/42`
- Profile: `Standard`
- Canonical requirement: `docs/requirements/feat-42.md @ sha:a1b2c3d`
- Requirement approval: `@user, 2026-11-01T10:00Z`

### Technical approach

Extend the existing `/api/audit-log` endpoint with optional `start_date` and
`end_date` query parameters. Filter rows in the SQL query using an indexed
`created_at` column. The UI uses the existing date-picker component from the
design system; no new dependency is introduced.

### Alternatives considered

| Alternative | Why rejected |
|---|---|
| Client-side filtering | Requires fetching all rows; unacceptable at >10 000 rows |
| New `/api/audit-log/filtered` endpoint | Duplication; the existing endpoint accepts query params |

### Risk assessment

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Index scan on large tables | Low | Med | `created_at` is already indexed; verified in schema |

### NFR verification

| NFR | Requirement | How verified |
|---|---|---|
| Latency | p95 < 500 ms for 10 000 rows | Load test in CI: `pytest tests/perf/test_audit_latency.py` |

### Architect sign-off

- Approved requirement revision: `docs/requirements/feat-42.md @ sha:a1b2c3d`
- Decision record: none
- Signed by: architect-session-12
- Signed at: 2026-11-02T09:30Z

---

## Requirement packet (child Task — API endpoint)

- Work item: `https://github.com/owner/repo/issues/43`
- Profile: `Standard`
- Parent: `https://github.com/owner/repo/issues/42`
- Approved parent revision: `docs/requirements/feat-42.md @ sha:a1b2c3d`
- Canonical requirement: `docs/requirements/task-43.md @ sha:b2c3d4e`
- Approval: `@user, 2026-11-02T11:00Z, https://github.com/owner/repo/issues/43#issuecomment-200`

### Context and outcome

This Task scopes the API change for Feature #42. Scope and parent criteria are
defined in `docs/requirements/feat-42.md @ sha:a1b2c3d`; this document records
only the Task-specific scope boundary and verification.

### Scope

- Add `start_date` and `end_date` query parameters to `/api/audit-log`.
- Filter with a parameterized SQL query on `created_at`.

### Exclusions

- UI changes are covered by Task #44.

### Acceptance and verification

| Criterion | Observable result | Check | Owner |
|---|---|---|---|
| AC-01 | API returns only entries within the date range | `pytest tests/api/test_audit.py::test_date_range_filter` | Build |
| AC-02 | Invalid dates return HTTP 400 | `pytest tests/api/test_audit.py::test_date_validation` | Build |

### Dependencies and questions

- Blockers: none (parent Feature sign-off is complete)
- Open questions: none
- Privacy/visibility: internal only

---

## Standard release record

- Work item: `https://github.com/owner/repo/issues/42`
- Profile: `Standard`
- Approved requirement revision: `docs/requirements/feat-42.md @ sha:a1b2c3d`
- Review verdict: `https://github.com/owner/repo/pull/55#issuecomment-300`
- Accepted head: `def456abc789`
- Landing evidence: PR #55 merged to `main` at commit `ghi012`

### Version

- Version: v1.5.0
- Version approval: `@user, 2026-11-10T14:00Z, https://github.com/owner/repo/issues/42#issuecomment-400`

### Scope coverage

- Feature: `https://github.com/owner/repo/issues/42`
- Child Tasks covered: `#43 (API), #44 (UI)`
- Coverage complete: yes

### Required checks

| Check | Command | Result |
|---|---|---|
| Unit + integration | `pytest tests/` | pass |
| Performance | `pytest tests/perf/test_audit_latency.py` | pass, p95 = 210 ms |

### Release note

Added a date-range filter to the audit log. Admin users can now specify
`start_date` and `end_date` to narrow audit entries without scrolling.
