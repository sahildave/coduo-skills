---
name: coduo-seo-pain-point
description: Use when researching competitor complaints for pain-point SEO, refreshing the periodic pain-point register, or finding discussion links for owner-written replies. Do NOT use for drafting articles, publishing replies, or general competitor pricing profiles.
---

# Coduo pain-point SEO

Research problems people report before deciding whether the product solves them. Save evidence that article writers can reuse until the next refresh, including problems the product cannot solve.

## 1. Establish scope and freshness

Read project instructions, product context, existing competitor research and the SEO routine. Start from the competitor roster: follow the roster rule in the `coduo-product-market` skill (`references/competitor-roster.md`), run its roster diff, then scope the pass. Every active roster tool left out gets a row in the register README's `## Not covered` table with its reason and date. Keep the scope and product-source pointers in the project's register, so this skill works in other repositories. The register lives in each product repo at `docs/research/pain-points/` (Atlas is the worked example).

Reuse existing register paths and IDs. Otherwise create `docs/research/pain-points/README.md`, one file per competitor and a short refresh log. Record the completed refresh date and next due date, one period later. The period comes from the product's routine table in `docs/product/seo-aeo/plan.md` (the "Pain-point refresh" row): monthly by default, 15 days at early stage (the site's first ~6 months; cookbook `09-routines.md`, "Early stage cadence"). Monthly due dates clamp to month end.

Before the due date, reuse the register unless the user requests fresh research. Targeted pre-publication checks do not reset the clock. A partial pass does not advance it.

**Done when:** the scoped competitors plus the Not covered rows equal the active roster, and the register path, product-source pointers and due date are known, or missing context is recorded. If research is not due, return the existing findings and stop without browsing.

## 2. Investigate reported problems

Search original user discussions and reviews across pricing/limits, workflows, integrations, automation/MCP, permissions, performance, migration/export and self-hosting where relevant. Prefer recent reports; retain older recurring themes.

Open the source and relevant replies. Follow fixes and resolution links, and compare factual claims with current official docs. Keep useful workarounds and vendor corrections even when they weaken the competitive angle.

- Treat reported experience, verified product behavior and product-fit hypotheses as separate claims.
- Mark indexed-only or unavailable evidence; retain direct URLs and access gaps without bypassing restrictions.
- Deduplicate cross-posts by author/problem. Votes and search-result counts do not establish prevalence.
- Mark promotional authors. A competitor's own comparison page is not independent customer evidence.
- Date limits and prices, including plan/edition and billing interval. Missing pricing-page text does not prove missing functionality.

**Done when:** every scoped competitor has a coverage note, supported themes and explicit gaps. Finish after follow-up searches stop adding distinct themes; do not claim exhaustive coverage of all users or force a minimum finding count.

## 3. Maintain the evidence register

Read [the finding contract](references/finding-contract.md) when creating or updating findings. Group the same underlying problem under a stable ID. Preserve resolved history, owner reply URLs/status and article links. If a source disappears, keep its URL and prior checked date, mark it unavailable and seek corroboration.

**Done when:** each finding contains the contract fields, each external claim has a source or an explicit unknown, and repeated reports share an ID. No unresolved complaint is presented as a verified universal defect.

## 4. Close the pass

Record scope, new/changed/resolved findings, inaccessible sources and coverage gaps in the refresh log. Update the README and reply shortlist. Advance the completed-refresh date and next due date only after all scoped competitors received a pass; mark interrupted work partial.

Index the pass in the demand register (`docs/product/seo-aeo/demand-register.md`; columns in the cookbook README, "The demand register"): each new finding's search-intent phrases become rows with source `pain-point` and a link to the finding ID (`<file>.md#RIV-004`), first-found date, covering pages and their count. An existing phrase gets the link added, not a second row. The register is an index: copy no evidence into it.

Add the register to the project's SEO routine table when one exists. Article selection reuses it between refreshes. This skill defines cadence; the routine table schedules it (cookbook `09-routines.md`, "Scheduling them"), with no owner step.

Reply candidates are optional off-site work. The agent drafts them; posting one publishes in the owner's name, so the agent never posts, and nothing in the cycle waits on a reply.

**Done when:** the log and register agree on coverage and dates, any new rival met in the pass has a roster row, every new finding's phrases have a demand-register row, and each reply candidate has a direct discussion link, useful contribution and posting status. Candidate means worth inspecting, not confirmed open for replies. Research sends no replies or messages.

## 5. Hand off grounded article opportunities

Read the project's feature inventory, product-market memory and current pricing before suggesting a product solution. Follow the existing product-memory discovery workflow if canonical files are missing; record the gap without regenerating memory merely to finish research.

Match candidate solutions to released capabilities, code/document evidence, plan/platform requirements and limitations. Keep fit `unassessed` when proof is missing. A feature's existence does not prove superior speed, unlimited underlying-platform capacity or a working migration path.

Return supported themes, direct reply links, resolved traps, coverage gaps, next refresh date and product-verification work. Drafting articles is a subsequent task; no article or reply is published by this skill.

**Done when:** each suggested product solution has evidence or a named verification gap, and the handoff links to the saved register. A complaint alone never qualifies a product recommendation.
