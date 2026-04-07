**Status: implementation-ready**

---

## Problem
First-time users running `briefcase setup --backend notion` are presented with bare prompts for an API token and parent page ID, with no guidance on how to obtain either. They must independently discover: how to create a Notion integration, what a token looks like, that they need a dedicated parent page, and that the page must be shared with the integration. There is also no tolerance for pasting a full Notion URL — only raw 32-char hex IDs are accepted.

## Goal
A first-time user with no Notion API experience can complete `briefcase setup --backend notion` in one sitting, guided by the CLI itself, without needing to consult external documentation.

## Acceptance Criteria
- [ ] When user selects notion backend, CLI prints a short inline checklist (pointing to notion.so/my-integrations, parent page requirement, share-with-integration step) before the token prompt
- [ ] Token prompt text includes a hint pointing to notion.so/my-integrations
- [ ] A sharing reminder is printed above the parent page ID prompt
- [ ] Parent page prompt accepts a full Notion URL in addition to a raw 32-char hex ID; the ID is extracted automatically via regex
- [ ] Existing non-interactive / piped-stdin usage (`briefcase setup --backend notion`) continues to work unchanged
- [ ] All new user-facing strings are in setup.py only; no changes to client.py or provisioner.py

## Non-Functional Requirements
- **Expected load / scale:** Single-user interactive CLI; runs once at project setup
- **Latency / response time:** No extra API calls added; latency unchanged from current setup flow
- **Availability / reliability:** Not applicable — local CLI command
- **Cost constraints:** No new dependencies; no additional Python packages
- **Compliance / data residency:** Not applicable
- **Other constraints:** ~30–50 lines of change in setup.py plus a small URL-parsing helper; must not break scripted/piped-stdin usage

## Out of Scope
- Board view creation via Notion API (separate idea)
- Token validation via test API call before provisioning
- Page access validation via pre-flight API call
- Non-interactive installer mode (existing separate Idea)
- Changes to install.sh
- Notion OAuth or browser-based authentication

## Open Questions
- None identified; all decisions resolved during ideation

## Technical Approach
All changes are confined to src/cli/commands/setup.py. No new dependencies or API calls required. 1. Inline checklist: add 3-4 click.echo() calls before the token prompt when backend is notion. Print a short numbered list pointing to notion.so/my-integrations, the parent page requirement, and the share-with-integration step (via Connect to menu). 2. Token prompt text: change from 'Notion API token' to 'Notion API token (from notion.so/my-integrations)'. 3. Sharing reminder: add a click.echo() above the parent page ID prompt. 4. URL-to-ID helper: _parse_page_id(value) using re.search() to extract 32-hex-char ID from raw ID or full Notion URL. No changes to client.py, provisioner.py, or install.sh.
