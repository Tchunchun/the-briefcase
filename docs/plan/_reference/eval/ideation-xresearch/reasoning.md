# Ideation Brainstorming Log: Xresearch

## Session Overview

**Ideation Agent Role:** Shape rough ideas into clear, scoped feature briefs before implementation begins.

**User Request:** "I want to build a Xresearch to pull the latest trends/news from X for certain topics, such as Oil Price, AI Agent, Claude, etc."

**Session Goal:** Convert this early-stage idea into a testable brief with clear acceptance criteria, scope boundaries, and open technical questions for the architect agent to resolve.

---

## Brainstorming Workflow (per SKILL.md §Brainstorming Approach)

### Step 1: Restate the Problem

**Initial Understanding:**
- User wants an automated tool to monitor X (formerly Twitter)
- Tool should track trends/news for specific topics of interest
- Examples given: Oil Price, AI Agent, Claude
- Implied need: reduce manual effort in staying informed about these topics

**Restated Problem Statement:**
Users currently must manually browse X to find trending discussions on topics they care about. They need a centralized, automated way to discover and aggregate recent posts/discussions from X for specific topics so they can stay informed without constant platform engagement.

**Decision:** Problem is clear enough to proceed. Not overly vague, has concrete examples, and implies a specific pain point (manual monitoring → automation).

---

### Step 2: Identify User/Persona

**Who is this for?**
- Individual researcher, analyst, or news monitor
- Someone with specific interest domains (finance, AI, technology, etc.)
- Prefers programmatic access over manual browsing
- Likely uses the existing CLI agent infrastructure (based on tech stack)

**Persona Sketch:**
A researcher or analyst who uses AI agents for workflow automation and needs a lightweight way to pull current X discussions on predefined topics for daily or ad-hoc briefings.

**Decision:** Persona is clear — single-user research tool integrated into existing agent CLI. This constrains scope (no multi-user auth, no complex permission systems, no web UI).

---

### Step 3: Define Desired Outcome

**What should the user be able to do?**
1. Specify topics of interest
2. Trigger a search on X for those topics
3. Receive curated, formatted results (recent posts, engagement metrics, URLs)
4. Integrate results into their existing workflow (CLI, Discord, stored files)

**Success Criteria (user-facing):**
- User can ask for trends on "AI Agent" and get back 10–20 recent relevant posts within seconds
- Results include post text, author, engagement counts, and link to original post
- Tool respects X API rate limits and degrades gracefully on rate limit
- Can be called from CLI with a single command

**Decision:** Desired outcome is concrete. User wants to go from "no programmatic X access" to "automated topic search results" accessible via CLI. This is a clear feature boundary.

---

### Step 4: Explore Scope Boundaries

**Critical Boundary Questions Asked & Answered:**

| Question | Initial Answer | Scope Decision |
|---|---|---|
| Real-time vs. snapshot? | X API search is 7-day lookback max; historical is out of scope | Current snapshot only, no long-term storage |
| Scheduled or on-demand? | User didn't specify; keeping lightweight suggests on-demand | On-demand trigger via CLI (no background job) |
| Output format? | "trends/news" — unclear if CLI text, Discord, or stored file | Multiple options → Open Question for architect |
| How many topics? | Examples: 3 (Oil, AI, Claude) — but is this the minimum or scope? | Accept minimum 3; support arbitrary number |
| Filter quality? | User didn't specify spam/bot filtering | Out of scope: bot filtering, sentiment analysis |
| Storage? | User said "pull" — suggests ephemeral, not persistent | Out of scope: historical archive, caching layer |
| Multi-user? | Single researcher implied by "I want to build" and existing agent infra | Out of scope: user accounts, sharing, permissions |

**Out-of-Scope Items Identified:**
- Sentiment analysis or NLP
- Historical trend tracking across weeks
- Spam/bot filtering
- Persistent data warehouse
- Multi-user or account management
- Cross-source aggregation (other news sites)

**Decision:** Scope is now bounded. The feature is "on-demand X topic search with formatted output for single user," NOT "real-time trend monitoring, multi-user research platform, or historical archive."

---

### Step 5: Separate Mixed Ideas / Tangled Concepts

**Check:** Are multiple ideas mixed together here?

- Single coherent idea: "Pull X trends for specific topics"
- No secondary ideas mentioned (e.g., "also want sentiment analysis" or "also need Discord bot")
- Request is focused and unambiguous

**Decision:** One idea, one brief. No splitting needed.

---

### Step 6: Implementation Detail Check

**Did the user jump to implementation details too early?**

User mentioned:
- Tool name: "Xresearch" ✓ (OK, descriptive)
- Platform: X (formerly Twitter) ✓ (OK, defines target)
- Topics: Oil Price, AI Agent, Claude ✓ (OK, examples of inputs)

User did NOT mention:
- Specific API endpoint (good — that's the architect's job)
- Database schema (good — deferred to architect)
- Authentication method (good — deferred to architect)
- UI/UX design details (good — deferred to architect)

**Decision:** User stayed at the problem level. Kept it appropriately high-level. No need to redirect.

---

### Step 7: Acceptance Criteria Formulation

**Observable, testable success conditions:**

From the problem and desired outcome, derived these acceptance criteria:

1. **Input:** User can specify topics (minimum: Oil Price, AI Agent, Claude)
2. **Retrieval:** Tool fetches recent X posts matching those topics
3. **Results:** Output includes trending discussions and high-engagement content
4. **Output:** Results are formatted for human review (via chosen surface)
5. **Trigger:** Can be called on-demand via CLI
6. **Freshness:** Data is current within X API limits (typically ≤7 days)

**Decision:** Criteria are testable. An implementation can verify each one without ambiguity. Criteria are not too specific (e.g., "fetch exactly 47 posts") or too vague ("make it good").

---

### Step 8: Non-Functional Requirements Assessment

**For each NFR category, asked: What do we know? What's unknown?**

| NFR | Known | Unknown | Resolution |
|---|---|---|---|
| **Load/Scale** | Single user, ad-hoc queries | ~5–10 searches/day (assumption) | Marked as assumption; architect may refine |
| **Latency** | User didn't specify; reasonable CLI target is <10s | Is <10s acceptable or too slow? | Open Question for architect |
| **Availability** | X API can rate-limit or fail | Should tool queue, retry, or fail silently? | Open Question for architect |
| **Cost** | Existing tech stack avoids paid services | Is X API free tier sufficient for use case? | Open Question for architect |
| **Compliance** | No user-facing auth; personal tool | Does X ToS allow automated scraping? | Open Question for architect |
| **Other** | Must integrate with existing CLI | Do we need async/background jobs? | Open Question for architect |

**Decision:** Filled in reasonable assumptions (marked as such), left genuine unknowns as Open Questions. This is correct per SKILL.md: "Write 'not yet known' for anything genuinely unclear — the architect will flag it as an Open Question."

---

## Key Decisions Made

1. **Feature Scope:** On-demand, single-user X topic search with current snapshot results (no historical archiving).
2. **Output Surface:** Left open (CLI/Discord/file) — architect to decide with user.
3. **API Approach:** Use X API search endpoint; scope is current posts only.
4. **Persistence:** No storage scope; results are ephemeral per query.
5. **Quality Filtering:** Out of scope; focus on surfacing what X returns (architect can add filtering later if needed).
6. **Multi-topic Support:** Yes, support arbitrary number of topics (no artificial limit).

---

## Open Questions Logged for Architect

Seven open questions were identified and logged in `brief.md`:

1. **X API Endpoint Selection:** Which endpoint(s) support the required functionality within free tier?
2. **Storage Strategy:** Ephemeral vs. temporary storage? JSON files, Notion, or direct output?
3. **Output Format:** CLI table, Discord embed, Markdown, JSON, or other?
4. **Surface/Integration:** New CLI command or integrated into existing workflow?
5. **Batch vs. Single-Topic:** Should one invocation handle multiple topics or one at a time?
6. **Ranking/Filtering:** What defines a "trend" for sorting results?
7. **Credential Management:** How will X API keys be stored and rotated?

**Decision:** All open questions are technical and appropriately belong with the architect agent. Ideation has provided enough context (problem, goal, acceptance criteria) that the architect can resolve these without asking back about scope.

---

## Artifacts Created

1. **brief.md** — Full feature brief with problem, goal, acceptance criteria (6 items), NFRs (5 categories with reasonable assumptions), Out of Scope (8 items), and 7 Open Questions.
   - Status set to "draft" per SKILL.md §Exit Criteria
   - No Technical Approach (architect owns this)
   - No tasks.md (implementation owns this)

2. **inbox-entry.md** — Single-line summary for _inbox.md showing status `[-> planned]` with link to brief.

3. **reasoning.md** (this file) — Log of ideation process, scope decisions, and rationale.

---

## Ideation Complete

**Exit Criteria Met** (per SKILL.md §84–94):

- ✅ Single feature scope defined in `brief.md`
- ✅ Acceptance criteria are clear and testable (6 checkboxes)
- ✅ Non-Functional Requirements filled in to current knowledge ("not yet known" for unknowns)
- ✅ Out-of-scope items are explicit (8 items listed)
- ✅ Open technical questions are clearly listed (7 questions for architect)
- ✅ Inbox item marked `[-> planned]` (ready to transition)
- ✅ Status: draft (awaiting architect review per SKILL.md)

**Readiness:** Brief is ready for architect agent to review. No additional scope clarification needed from user before architect phase begins.

---

## Notes for Architect Agent

- User is motivated by staying informed on trending topics; emphasize real-time or near-real-time results in Technical Approach.
- Cost sensitivity implied (existing tech stack avoids paid services); verify free X API tier or low-cost option.
- Single-user, researcher persona; simplify auth/credential handling accordingly.
- Integration with existing CLI agent infrastructure is required; check `_project/tech-stack.md` for patterns (Typer, Pydantic, httpx).
