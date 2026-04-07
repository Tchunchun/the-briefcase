**Status: implementation-ready**

---

## Problem
install.sh has several UX bugs reported by users: (1) venv/pip failures are swallowed — users cannot debug install errors, (2) post-install guidance says 'agent' instead of './briefcase' in consumer projects, (3) pip is invoked via mixed paths instead of consistently using .venv/bin/python -m pip, (4) no non-interactive mode for CI or scripted setups.

## Goal
Installer works reliably with clear error output on failure, correct command references in all messages, consistent virtualenv pip invocation, and a --non-interactive flag for CI/scripted workflows.

## Acceptance Criteria
- [ ] venv creation failure shows full stderr (remove 2>/dev/null from python3 -m venv call)
- [ ] pip install failure shows full stderr (remove 2>/dev/null from pip calls)
- [ ] All pip invocations use .venv/bin/python -m pip instead of .venv/bin/pip
- [ ] Post-install and setup messages reference './briefcase' not 'agent' in consumer context
- [ ] --non-interactive flag skips prompts, uses defaults, exits non-zero on any failure
- [ ] Existing interactive behavior unchanged when --non-interactive is absent
- [ ] All changes covered by tests

## Non-Functional Requirements
Installer must complete in under 30s on typical CI. No new dependencies. Backward-compatible with existing .briefcase/ layouts.

## Out of Scope
Remote/curl-pipe install flow. Notion setup changes (separate brief). Windows support.

## Open Questions


## Technical Approach
Files: install.sh (primary), src/cli/commands/setup.py (message fix)

1. Error visibility (install.sh:152-163): Remove 2>/dev/null from the venv/pip block. Redirect stderr to a temp log; on failure, cat the log and exit 1. On success, keep quiet output (existing -q flags).

2. Consistent pip invocation (install.sh:156-157): Replace BRIEFCASE/.venv/bin/pip install with BRIEFCASE/.venv/bin/python -m pip install throughout.

3. Command reference fix: Grep for any 'agent ' references in post-install echo messages and setup.py output; replace with './briefcase'.

4. Non-interactive mode: Add BRIEFCASE_NON_INTERACTIVE env var (checked at top). When set: skip any future prompts, use defaults for optional steps, exit 1 on any failure instead of warning. Also accept --non-interactive as argv[1] and export the env var.

Testing: Shell-based integration test that runs install.sh in a temp dir.
