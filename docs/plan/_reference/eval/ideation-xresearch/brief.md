# Xresearch: X Trends & News Aggregator (v3)

**Status: draft** ← ideation agent sets to `draft`; architect agent sets to `implementation-ready`

---

## Problem

Users lack a centralized way to monitor trending topics and breaking news on X (Twitter) across multiple subjects of interest (e.g., Oil Price, AI Agents, Claude) without manually scrolling the platform. They need an automated tool that pulls recent discussions, trends, and news for curated topics so they can stay informed without constant manual effort.

## Goal

Provide a personal research tool that discovers, aggregates, and surfaces the latest trends and news from X for user-specified topics, enabling informed decision-making and awareness without manual platform monitoring.

## Acceptance Criteria

- [ ] Users can specify topics of interest (minimum: Oil Price, AI Agent, Claude)
- [ ] The tool retrieves recent posts/discussions from X matching those topics
- [ ] Results surface trending conversations and high-engagement content
- [ ] Output is formatted and ready for human review (in chosen surface: CLI, Discord, or stored report)
- [ ] Tool can be triggered on-demand via CLI command
- [ ] Retrieved data is at least as current as the X API allows (typically last 7 days of search history)

## Non-Functional Requirements

- **Expected load / scale:** Single user, ad-hoc queries; ~5–10 topic searches per day
- **Latency / response time:** CLI response < 10 seconds for a typical topic search
- **Availability / reliability:** Best-effort; graceful degradation if X API is rate-limited or unavailable
- **Cost constraints:** Must stay within free tier of X API if available; otherwise < $10/month
- **Compliance / data residency:** No PII stored; X terms of service must be respected; internal use only
- **Other constraints:** Must not break existing CLI commands; integrates with existing agent infrastructure

## Out of Scope

- Storing historical trend data across weeks or months (this brief focuses on current snapshots)
- Automated scheduled scraping or background monitoring (manual trigger only)
- Sentiment analysis, natural language processing, or AI-driven summarization of posts
- Bot detection or filtering out spam/low-quality content
- Creating user accounts or managing X authentication beyond single-user setup
- Cross-referencing X data with other news sources
- Building a persistent cache or data warehouse
- User accounts, multi-user sharing, or permission management

## Open Questions

- Which X API endpoint(s) should be used (search, trends, recent search)? Does the free tier support the required functionality?
- Should results be stored temporarily (e.g., in JSON, Notion, or ephemeral memory) or streamed directly to the user?
- What is the preferred output format: CLI table/text, Discord embed message, Markdown file, or JSON?
- How should the tool be surfaced: as a new CLI command (e.g., `briefcase xresearch --topic "AI Agent"`) or integrated into existing agent workflow?
- Should the tool support batch queries (multiple topics at once) or single-topic-at-a-time?
- What should constitute a "trend" for filtering/ranking results (engagement count, recency, relevance score)?
- How will X API credentials be stored and rotated?

---

## Technical Approach

*Owned by architect agent.*

---

## Notes

- Ideation agent fills everything above Technical Approach, then flags open questions.
- Architect agent fills Technical Approach, resolves open questions, and sets Status to `implementation-ready`.
- Implementation agent treats this entire file as read-only.
- A brief is implementation-ready only when the architect has signed off and the implementation agent can create `tasks.md` without guessing.
