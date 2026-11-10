# Standard profile example

This example shows all required artifacts for one Standard Feature with two
child Tasks. A single requirement revision is the only scope authority throughout.
This is illustrative source-only material, not actual approval, check, release,
or deployment evidence. Use the [Standard profile](../profiles/standard/PROFILE.md),
[Architect](../profiles/standard/skills/architect/SKILL.md), and
[Feature PRD template](../templates/standard/brief.md).

The Feature's requirement packet is shaped and approved at creation. It enters
Technical shaping directly; Architect reuses that approved revision rather than
running another Requirements pass, then verifies dependencies and the absence
of a competing implementation claim before Ready. Build records assignment
when it claims Ready.

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

Actors: administrators investigating an event. Before: scroll manually through
the full log. After: choose dates and see only matching events.

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

### Constraints, children, and release obligations

- Preserve existing authorization, pagination, and requests without date filters.
- Use existing dependencies; no added licensing or service cost.
- NFR: p95 below 500 ms over 10 000 rows; verify in the supported CI environment.
- Child Tasks: #43 API and #44 UI; both reference this approved Feature revision.
- Require unit/integration, UI smoke, and latency evidence before delivery.
- Version impact: minor; release note required; no deployment claim.

---

## Feature PRD (Architect sign-off)

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

- Work item type: Feature
- Architecture applicability: Feature sign-off
- Approved requirement revision: `docs/requirements/feat-42.md @ sha:a1b2c3d`
- Decision record: none
- Signed by: architect-session-12
- Signed at: 2026-11-02T09:30Z
- Result: approved; no unresolved stopping questions

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

### Architecture applicability

- Parent Feature sign-off: `docs/requirements/feat-42.md @ sha:a1b2c3d`
- Approved Task revision: `docs/requirements/task-43.md @ sha:b2c3d4e`
- Result: parent sign-off applies; this slice adds no technical decision,
  interface, dependency, NFR, approach assumption, or release obligation.

---

## Requirement packet (child Task - date picker)

- Work item: `https://github.com/owner/repo/issues/44`
- Profile: `Standard`
- Parent: `https://github.com/owner/repo/issues/42`
- Approved parent revision: `docs/requirements/feat-42.md @ sha:a1b2c3d`
- Canonical requirement: `docs/requirements/task-44.md @ sha:c3d4e5f`
- Approval: `@user, 2026-11-02T11:00Z, https://github.com/owner/repo/issues/44#issuecomment-201`
- Scope boundary: date-picker UI only; parent scope remains in the Feature.
- Exclusions: API implementation belongs to #43.
- Acceptance: picker supplies start/end dates and updates the displayed results.
- Verification: supported-browser smoke test, recorded by Build for independent Review.
- Dependencies/questions: native blocker #43; no unresolved product question.

---

## Standard release record

- Work item: `https://github.com/owner/repo/issues/42`
- Work item type: Feature
- Profile: `Standard`
- Approved requirement revision: `docs/requirements/feat-42.md @ sha:a1b2c3d`
- Review verdict: `https://github.com/owner/repo/pull/55#issuecomment-300`
- Accepted head: `def456abc789`
- Landing evidence: PR #55 merged to `main` at commit `ghi012`

### Version

- Version impact: minor, additive date-range filtering
- Version: v1.5.0
- Version approval: `@user, 2026-11-10T14:00Z, https://github.com/owner/repo/issues/42#issuecomment-400`

### Scope coverage

- Feature: `https://github.com/owner/repo/issues/42`
- Child Tasks covered: `#43 (API), #44 (UI)`
- Applicable coverage complete: yes

### Required checks

| Check | Command | Result |
|---|---|---|
| Unit + integration | `pytest tests/` | pass |
| Performance | `pytest tests/perf/test_audit_latency.py` | pass, p95 = 210 ms |

### Release note

Added a date-range filter to the audit log. Admin users can now specify
`start_date` and `end_date` to narrow audit entries without scrolling.

### Environment and readiness

- Required environments: supported API CI and browser smoke environment.
- Readiness evidence: passing UI smoke and CI latency evidence linked by Build.
- Remaining obligations: none in this illustrative completed record.
- Deployment: not claimed.

### Completion gate

- Task: not applicable
- Feature: all required child slices covered; Feature acceptance, landing,
  version, release note, environment, and readiness evidence complete.
