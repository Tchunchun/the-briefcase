**Status: implementation-ready**
---
## Problem
upgrade.py unconditionally imports notion_client, so even ./agent --help fails with ModuleNotFoundError when notion-client is not installed. This blocks all local-only users.
## Goal
CLI commands that do not touch Notion work without notion-client installed. Notion modules are imported only when a Notion backend operation is requested.
## Acceptance Criteria
- [ ] ./agent --help works without notion-client installed
- [ ] ./agent inbox list works with backend=local without notion-client
- [ ] ./agent setup --backend notion fails gracefully with a clear message if notion-client is missing
- [ ] All Notion-specific imports are lazy (inside functions or behind conditionals)
- [ ] Existing Notion backend functionality unchanged when notion-client is available
## Non-Functional Requirements
No performance regression for Notion-backed commands. No new dependencies.
## Out of Scope
Removing notion-client as a dependency entirely. Changing the Notion backend API.
## Open Questions
Resolved: Only src/cli/commands/upgrade.py line 15 has a blocking unconditional import. The fix is moving FindingStatus import inside the upgrade() function. factory.py and setup.py already use lazy patterns.
## Technical Approach
1. In src/cli/commands/upgrade.py: move the line 'from src.integrations.notion.upgrade import FindingStatus' from module level (line 15) into the upgrade() function body, next to the existing lazy imports on lines 65-66.
2. FindingStatus is an enum used for type hints and display -- it can safely be imported at call time.
3. Verify no other CLI entry points have similar unconditional Notion imports (confirmed: setup.py and factory.py already use lazy patterns).
4. Add a test that imports src.cli.main without notion-client on sys.path to prevent regression.
