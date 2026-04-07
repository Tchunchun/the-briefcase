**Status: implementation-ready**
---
## Problem
New users have no way to verify their install worked. They run install.sh, see a success message, but have no quick validation step to confirm the CLI, venv, and backend are functional before starting real work.
## Goal
Provide a 2-3 command smoke test in the README that users can run immediately after install to confirm everything works end-to-end.
## Acceptance Criteria
- [ ] README contains a Verify Your Install section after Quick Start
- [ ] Section includes 2-3 commands that test: CLI loads (--help), inbox write works (inbox add), inbox read works (inbox list)
- [ ] Expected output is shown so users know what success looks like
- [ ] Commands work on both local and Notion backends
## Non-Functional Requirements
No new dependencies. Documentation-only change.
## Out of Scope
Automated CI smoke tests. Testing Notion-specific flows. Changes to install.sh beyond what was already added.
## Open Questions
Resolved: No cleanup step needed. The test idea is harmless and serves as a first inbox entry the user can promote or delete later.
## Technical Approach
Documentation-only change to README.md. Add a Verify Your Install subsection inside Quick Start, after the post-install structure block. Include three commands: (1) ./briefcase --help — confirms CLI loads, (2) ./briefcase inbox add --type idea --text 'Test idea' — confirms write path, (3) ./briefcase inbox list — confirms read path. Show expected JSON output snippet for each. No code changes required.
