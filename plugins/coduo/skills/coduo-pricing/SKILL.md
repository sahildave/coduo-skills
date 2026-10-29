---
name: coduo-pricing
description: "Pricing for a Coduo product: report the current decided price and flag stale pricing docs, or, where none exist, price the competitor roster into a dated table and a first-feel price range. Quick summary by default; a deep run writes pricing notes into the repo's flow-note research on request. Use when asked what a product costs or should cost, for competitor prices, or for tier and packaging decisions."
---

# Coduo pricing

One skill, two depths. The user says how deep. Run **quick** unless they asked for
the deep run, and end quick by offering deep.

Everything product-specific comes from the repo you are in. Read the product's name,
positioning and **baseline alternative** (what a buyer uses today instead, named in the
header line of `docs/product/features.md`) from `docs/product/product-market.md` and
`docs/product/features.md`. If neither exists, take them from the repo's README and
say so in the summary.

## Evidence labels

Every price point and claim you report carries one label:

- **Fact**: a page or repo file states it. Give the URL or `path:line` and the date read.
- **Inference**: follows from facts you name. Say which.
- **Assumption**: nobody has checked it (a persona budget, a target revenue). Say so.

A competitor field the page does not show is `Not found`. A figure you derived is
prefixed `Estimate:` and labelled Inference. Compare like with like: a yearly plan
shown per month is not a monthly price, so name the billing interval on every price.

## Quick

### 1. Read the pricing the repo already has

Read every file these match, if it exists:

```
docs/product/pricing/**        docs/adr/*pric*        docs/gtm/*pric*
docs/flow/**/*pric*            docs/product/product-market.md  (Pricing wedge entries)
```

Skip `docs/product/pricing/competitor-prices.md`, which the glob also matches: it
states rivals' prices, never the product's, and only step 2 reads it. Also read any
file one of these names as the current record (an ADR cites its working doc, a plan
points at its decision).

Rank them. A doc is **decided** when its frontmatter says `status: decided`,
`accepted` or `validated`, an ADR says `Status: Accepted`, or its text says
"Decided <date>". Its date is the latest decision or amendment date it states, else
frontmatter `updated`, else `git log -1 --format=%cs -- <file>`. **The newest decided
doc wins**, amendments included. Every other doc that states a different price, tier,
allowance, billing unit or on-sale status is **stale**:
an older decided doc, or any `status: proposed` one. Agreement is not staleness;
list only docs that disagree.

Frontmatter `status:` beats body text: a doc whose frontmatter says `proposed` stays
proposed even if its body says "Decided <date>". Inside the winning doc, a dated
amendment beats the text it supersedes, so read the winner's figures from its latest
amendment.

**Done when** each matched file is either the winner, agrees with it, or is on the
stale list with `path:line` of the disagreeing figure.

If no file states a price, or the user asked for a fresh read, run step 2. Otherwise
skip to step 3.

### 2. Fresh read: competitor prices and a first-feel range

1. **Start from the roster.** Follow the competitor roster rule in the
   `coduo-product-market` skill (`references/competitor-roster.md`): run the roster
   diff, then price every active tool with a published price. Where there is no
   roster yet, build it from `docs/research/competitors/`, `docs/research/*.md`,
   competitor entries in `product-market.md` and the baseline alternative. Ask the
   user only when the repo names none, at most three questions in one message.
2. **Reuse what is saved.** If `docs/product/pricing/competitor-prices.md` exists,
   keep each row checked within 30 days and re-check only the older ones.
3. **Read two pages per competitor**, its homepage and its pricing page, with
   `trafilatura -u "<URL>"` (WebFetch is disabled). An empty or script-only result is
   `Not found` for that page, never a remembered price.
4. **Write the table** to `docs/product/pricing/competitor-prices.md`, one row per
   competitor, so the next run can reuse it:

   | Competitor | Tiers | Price (interval) | Billing unit | Free tier | Source URL | Checked | Label |
   | --- | --- | --- | --- | --- | --- | --- | --- |

5. **Give a range, never a single number**: a low and a high for the product's paid
   tier, each tied to the competitor rows or the baseline alternative it sits against.
   Label the range Inference and name the facts it rests on. Price each rival at the
   buyer's real setup (seats, boards, repos), not at one unit. When the range rests on
   a subset of the rows, log the rest under `## Not covered` in the table file.
6. **One break-even line**: customers needed = target monthly revenue / price, at both
   ends of the range. Take the target from the repo; if it has none, pick a round
   number and label it Assumption.

**Done when** every row has a source URL and a checked date or `Not found`, every
active roster tool is a row or a Not covered row, and the range and break-even line
carry their labels.

### 3. Report

A short summary in chat, in this order:

1. **Current price**: the winning doc's tiers and prices, its status, decision date and
   path. Or, from step 2, the range with its label.
2. **Stale docs**: one line each: path:line, what it says, its own status and date.
   Write "none" when none disagree.
3. **What is priced but not built**, only where a doc says so (an add-on with no
   Stripe Price, a tier with no checkout).
4. **The offer**: "Want the deep run? It writes one note per pricing topic into
   `<the layout this repo uses>` and renders the map."

Change no doc in quick mode except the competitor table. Fixing a stale doc is the
owner's call: name the edit, do not make it.

## Deep (only when asked)

The output slots into the research the repo already keeps, as **flow notes**: one
markdown file per topic, wired into a dependency map.

1. **Match the repo's layout.** Look for existing flow notes: `docs/gtm/` with a
   `README.md` index, `docs/flow/<map>/` with `flow.json`, or `docs/product/pricing/`.
   Use the folder that already holds pricing notes, its file numbering and its
   frontmatter field set (keep extra fields it uses, such as `facts` or `questions`).
   If none exists, start `docs/flow/pricing/`. Update the pricing note that exists
   rather than writing a sibling.
2. **Write one note per topic.** Typical topics: competitor prices (from quick step 2),
   value metric, tiers and packaging, price points, free tier and trial, yearly
   discount, break-even. Each note's frontmatter carries at least:

   ```yaml
   id: <kebab-id>
   title: <the note's claim, as a sentence>
   node: <short label for the map card>
   caption: <one line under the label>
   kind: research | synthesis | decision
   status: proposed
   confidence: low | medium | high
   depends_on: [<ids>]
   unlocks: [<ids>]
   updated: <YYYY-MM-DD>
   summary: <one or two sentences>
   ```

   Every figure in a note carries its evidence label. Notes stay `status: proposed`
   until the owner decides; a decision goes to an ADR where the repo keeps `docs/adr/`,
   and the notes it overrides get a "Superseded by" line naming it.
3. **Pricing theory comes from the `pricing` skill**: value metric, tier design, price
   anchoring. Skip its intake questionnaire (current conversion, ARPU, churn). A
   pre-launch product has none of those numbers; use `product-market.md` and
   `features.md` as its context instead and label every modelled number Assumption.
4. **Competitor facts follow the `competitor-profiling` or `competitors` skill**:
   primary sources, a checked date per fact, where the competitor is stronger. Profile
   every active roster tool against one shared brief and JSON schema, and keep the
   rival set the prices rest on in the method note with a `## Not covered` table
   (roster rule above). Atlas's `docs/research/competitor-matrix/BRIEF.md` is the
   schema to copy.
5. **Render with the `coduo-flow` skill** against the folder from step 1.

**Done when** every topic has a note with the full frontmatter, every figure is
labelled, the map renders, and the report lists the notes written and the stale docs
from quick step 1 still unresolved.

## Recurring

Pricing is re-run, not settled once. Run a deep pass on any trigger: launch, a change
to the product's own price or tiers, a rival price change another exercise saw (a
pain-point refresh, a quick re-check), or a new tier. Run one regardless if the method
note shows no full pass in 6 months; record that rule in the method note, not as a due
date. Quick mode's 30-day row re-check runs whenever the skill does, and the roster
diff rides the monthly pain-point refresh.

A deep pass leaves these behind, at these paths unless the repo already uses others:

| Artefact | Path |
| --- | --- |
| Roster | `docs/research/competitors/README.md` |
| Profiles and matrix | `docs/research/competitors/<slug>.md`, `docs/research/competitor-matrix/<slug>.json` (+ `BRIEF.md`) |
| Price table | `docs/product/pricing/competitor-prices.md` |
| Method, rival set, Not covered | `docs/product/pricing/plan.md` |
| Decision | `docs/product/pricing/decision.md` and an ADR |
| Prototype (optional) | `docs/prototypes/pricing/`, its rival list generated from the matrix |

Atlas and Harbour ran this shape; what each produced and missed is in
[references/examples.md](references/examples.md). Read it before a deep pass.

Where the ideas came from: [references/sources.md](references/sources.md).
