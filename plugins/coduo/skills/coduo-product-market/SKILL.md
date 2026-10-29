---
name: coduo-product-market
description: |
  Own a product repo's product memory: `docs/product/product-market.md`
  (PM-NNN positioning signals), `docs/product/business-rules.md` (BR-NNN
  rules) and `docs/product/features.md` (the feature inventory, tiered
  Must-have / Good-to-have / Extra against the buyer's baseline alternative).
  Use to capture a product signal or business rule — a USP, promise,
  differentiator, objection, audience, pricing wedge — in the house format,
  and to audit which features the landing page should lead with: "what are
  our USPs", "which features go on the landing page", "must-have vs
  good-to-have", "is the website claiming things the app doesn't do". Other
  skills that read or write these files take the format from here.
---

# Coduo product market

Three files in `docs/product/` hold what a product is for and why a buyer picks it.
This skill owns their formats and is the only writer of `features.md`.

| File | Holds | Written by |
|---|---|---|
| `product-market.md` | PM-NNN signals: promise, audience, differentiator, objection… | capture mode, any time a signal appears |
| `business-rules.md` | BR-NNN constraints on product or business behaviour | capture mode |
| `features.md` | the tiered feature inventory, with evidence | audit mode, regenerated wholesale |

Pick the mode from the request: a statement worth keeping is **capture**; "what do we
lead with", "list our features", "check the site against the app" is **audit**. Both
work in any Coduo product repo; read every product name, platform and competitor from
the repo, never from this skill.

## Capture mode

A **product signal** is a concise statement worth keeping because forgetting it could
change positioning, landing-page copy, product boundaries, trust, audience or pricing.
A **business rule** is a constraint that should govern product or business behaviour.

1. Read [references/memory-format.md](references/memory-format.md) before the first
   write of a session. It is the format contract for both files.
2. Search the file for the same meaning. Reuse its ID and update Status, wording and
   Evidence when it exists; take the next stable ID when it does not.
3. Show the entry in the reply, one line:

   ```markdown
   > 💎 PM-007 · Differentiator · hypothesis: <statement>
   > 📐 BR-004 · Data custody · proposed: <rule>
   ```

4. Write the same ID, text and status to the file.

**Done when** the reply and the file carry the same ID, text and status.

If `product-market.md` exists in another layout (the `product-marketing` skill's
section layout, a `# Product Marketing Context` heading), convert it before adding
anything: every filled field becomes one PM entry, Status `observation`, Source
`converted from <old layout>, <date>`. One file holds one format. Set each entry's
Kind from its old section, so the audit can read it:

| Old section | Kind |
|---|---|
| Product Overview | Product promise |
| Differentiation | Differentiator |
| Competitive Landscape | Substitute for a rival; Differentiator for a gap the product fills |
| Objections | Objection |
| Any other | the nearest Kind in [memory-format.md](references/memory-format.md)'s list (prefer one the file already uses), else `Note` |

## Audit mode

Writes `docs/product/features.md`, regenerated wholesale every run: never hand-merge
with the previous copy. If the caller names another output path, write there instead
and leave the repo untouched. Read
[references/audit-method.md](references/audit-method.md) and
[references/memory-format.md](references/memory-format.md) before step 1: the first
carries the scan scope, the evidence and claim rules, the tiering tests and the step-7
check; the second defines the PM Kinds and Statuses step 1 reads.

1. **Orient.** Record the product name, `git rev-parse --short HEAD` and today's date.
   Read `docs/product/product-market.md` (Product promise, Differentiator, Advantage,
   Substitute entries) and `docs/product/business-rules.md`. Where either is missing,
   fall back in this order: the PRD, `docs/product/**/discussion.md`, `docs/gtm/`,
   `docs/research/competitors/`, `docs/adr/`. Find the PRD by searching
   (`git ls-files | grep -i prd`), and say in Sources where it was. Read pricing
   decisions too (`docs/product/pricing/`, any `*pricing*` doc). Note each doc's status
   (`decided`, `supported`, `proposed`…); step 6 needs it. **Done when** you hold a
   list of the sources read, each with its status, and every missing memory file is
   named.
2. **Name the baseline alternative and the named competitors.** The baseline is what
   the buyer does today by default, most often the platform the product builds on, used
   as is. Paid rivals that memory or pricing docs name (the owner's comparison set) go
   on their own line, and each is a `Named: yes` row of the competitor roster
   ([references/competitor-roster.md](references/competitor-roster.md)). **Done when**
   one sentence names the baseline with a source or "inferred from <evidence>", and the
   competitors line lists each rival with its source, or says `none named`.
3. **Inventory features from code.** Count only what an end user reaches in the
   shipped build: a route, screen, command, MCP tool or CLI. Each feature gets a
   concrete name and evidence per the method file. Group sub-capabilities of one job
   under one row. **Done when** every user-reachable route, screen, command, tool and
   billing gate is a row or grouped under one, and every excluded area (dev, internal,
   test, unreachable code, unused strings) is named in the scope note.
4. **Inventory claims.** Read the public website (`landing/` or the repo's marketing
   pages), its pricing and policy copy, the user docs, and product proposal docs
   (mark those `(proposal)`). Match each claim to a feature from step 3. **Done when**
   every claim is matched, listed under `## Claimed but not found in code`, or listed
   under `## Claims the code contradicts`.
5. **Rate.** For each feature write the benefit and tag it Strong / Medium / Weak.
   Move Weak features to `## Dropped (weak benefit)`. Then answer the baseline test:
   does the baseline already do this? **Done when** every feature is either rated
   Strong or Medium with a yes/no baseline answer, or listed as dropped with a reason.
6. **Tier.** Must-have 1-3 rows, Good-to-have up to 5 more, Extra the rest, by the
   tests in the method file. A feature the baseline also has is never Must-have. **Done
   when** every row has a tier, the counts hold, and every owner headline promise that
   tests as parity sits in `## Positioning flags`.
7. **Write** `features.md` in the format below, then run the check in the method file.
   **Done when** the check prints only `check finished`, and by reading: at most three
   Must-have rows, at most five Good-to-have rows, and every Must-have's "Beats the
   baseline because" names something the baseline lacks.

### `features.md` format

Other skills parse this file. Keep the header lines, the column order and the tier
words exactly.

```markdown
# Features — <product>
Generated <YYYY-MM-DD> from <git short sha>. Baseline alternative: <what the buyer does today by default>.
Named competitors: <rival (source)>, <rival (source)>… or none named.

| Feature | Tier | Evidence | Benefit | Beats the baseline because | Landing use |
|---|---|---|---|---|---|
| <name> | Must-have | `src/x.ts:42` `fnName()` | <outcome for the buyer> | <what the baseline lacks; PM-NNN if one backs it> | Hero |

## Must-have

**<Feature>.** One short paragraph: the job, the mechanism, the proof.

## Good-to-have

**<Feature>.** …

## Extras

**<Feature>.** …

## Positioning flags

- <promise, quoted> — <source and status>. Tests as <parity / what it beats>; <which row carries it>.

## Claimed but not found in code

- "<claim, quoted>" — `<page or doc path>`. <what was searched, and what exists instead>

## Claims the code contradicts

- "<claim, quoted>" — `<page or doc path>`. <what the code does instead, with evidence>

## Dropped (weak benefit)

- <feature> — `<evidence>`. <one-line reason>

## Scope notes

Excluded: <each dev, internal, test or unreachable area, with its path>.

## Sources

- <each product doc, research file and website page read, with its status>
- Not present: <missing memory files, as plain text>
```

- Rows go in tier order, Must-have first. Tier is exactly `Must-have`, `Good-to-have`
  or `Extra`. A cell never contains `|`, escaped or not.
- "Beats the baseline because" is `parity` only when the baseline has the feature;
  otherwise it states the reason, in every tier.
- Landing use is one of `Hero`, `Features section`, `Pricing page`, `FAQ`,
  `Optional`, `Docs only`, `Omit`. An Extra defaults to `Optional` (`Docs only` and
  `Omit` also fit); it gets `Hero` or `Features section` only on the user's request.
- A feature behind an allowlist or flag is an `Extra` with `(gated)` in Benefit.
- Every section is present; an empty one says `None.`

Name every Positioning flag and every claim finding in the hand-off reply: they are
findings for the owner, not features.
