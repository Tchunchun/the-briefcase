**Status: draft**

---

## Problem
First-time users choosing the Notion backend face undocumented manual prerequisites — creating a Notion integration, obtaining an API token, creating a parent page, and sharing that page with the integration — that must be completed inside Notion before briefcase setup can succeed. The current CLI prompts for token and page ID with no guidance, causing silent failures or user abandonment at the most critical moment of onboarding.

## Goal
A first-time user with no prior Notion API experience can complete briefcase setup --backend notion in one sitting, guided by inline hints in the CLI, without needing to consult external documentation.

## Acceptance Criteria
- [ ] When user selects notion backend during briefcase setup, the CLI prints a 4-line checklist before the token prompt covering: (1) integration creation URL, (2) parent page creation requirement, (3) share-page-with-integration step
- [ ] The token prompt includes inline guidance text pointing to notion.so/my-integrations
- [ ] The parent page prompt accepts both a full Notion URL and a raw 32-char hex ID; the page ID is extracted automatically from URLs using a regex
- [ ] All changes are confined to src/cli/commands/setup.py (and optionally a small URL-parsing helper function within that file)
- [ ] Existing scripted / piped-stdin briefcase setup --backend notion behavior is unchanged (no regression for non-interactive use)

## Non-Functional Requirements
No new Python dependencies required. Validation relies on string parsing only (no extra API calls). Change adds approximately 30-50 lines to setup.py. Must not increase setup time perceptibly for users who already know their token and page ID.

## Out of Scope
Token validation via Notion API call. Board view creation via API. briefcase setup --check subcommand. Non-interactive installer mode (tracked separately as existing Idea). Notion OAuth or browser-based authentication.

## Open Questions
Should the inline checklist be skippable with a --skip-guide flag? Recommendation: no — it is a one-time setup and does not slow down experienced users who already have their values ready.

## Technical Approach
