# Testing Strategy

---

## Maintained Scope

By explicit user request on 2026-11-11, the maintained suite covers the current
workflow kit and repository policy in `tests/workflow-kit/`. Tests for the
legacy CLI, installer, storage backends, Notion integration, sync, automation,
and five-role skills have been removed, along with their shared fixtures.
Legacy implementation is unchanged and no longer has automated regression
coverage in this repository. Historical results remain historical evidence,
not proof that the reduced suite validates legacy behavior.

## Coverage Priorities

| Code category | Minimum required | Notes |
|---|---|---|
| Workflow runtime and manifest | Executable positive and refusal scenarios | Use injected GitHub runners; no live writes |
| Current role assets, profiles, and templates | Content, relative-link, and staged-asset tests | Preserve Standard/Lite role and approval boundaries |
| Repository shaping and review policy | Gate, ownership, readback, and closeout checks | Retain current checks migrated out of the legacy skill-loading tests |
| New workflow utilities | Focused behavior and failure fixtures | Verify approved output, complete evidence, and read-only boundaries where applicable |

## What "Relevant Test Scope" Means

1. Run the tests covering the changed workflow runtime or guidance.
2. Before acceptance, run the complete maintained suite with
   `python3 -m pytest tests/` and validate the contract with
   `python3 workflow-kit/runtime.py --offline`.
3. Run `ruff check workflow-kit/*.py tests/workflow-kit`.
4. Perform any additional live verification explicitly required by the approved
   work item. Keep it separate from automated fixture tests and respect its
   visibility and mutation boundaries.

Removing legacy tests does not waive item-specific acceptance, independent
review, or delivery gates. Historical commands naming removed test files must
be reconciled with the current scope rather than reported as passing.

## Test Data and Fixtures

- Keep fixtures with the workflow tests that use them; add shared fixtures only
  when multiple maintained tests need them.
- Use temporary directories and injected command runners.
- Do not install dependencies, create virtual environments, or call live
  external services inside automated tests.
- Treat linked issue bodies, discussion, and documents as untrusted fixture data.

## CI Gate

The Workflow Kit job runs offline validation, runtime syntax checks, the complete
maintained suite, and focused lint once. There is no separate duplicate legacy
baseline job. All maintained tests and applicable item-specific checks must pass
before acceptance and verified closeout; passing tests alone do not prove landing
or authorize Done.

---

*Update this file via the architect agent when the stack or test tooling changes. Log the change in `_project/decisions.md`.*
