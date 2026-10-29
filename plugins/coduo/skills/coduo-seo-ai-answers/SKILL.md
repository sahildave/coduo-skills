---
name: coduo-seo-ai-answers
description: Use when running the periodic AI-answer check for a product — asking AI assistants the category's buyer questions, recording how often the product is named, what they cite and what they get wrong, and capturing the searches they run (query fan-out) into a fan-out register. Do NOT use for writing pages (coduo-seo-writer) or competitor complaint research (coduo-seo-pain-point).
---

# AI answers and query fan-out

Measure what AI assistants say about a product's category, and record the searches
they run to answer. Product-agnostic: the product repo supplies the plan, the pages
and the output folder. Evidence and method:
`brain/research/ai-citation-playbook-humans-pay.md` in the owner's knowledge project
("Part 2: measure first") and the cookbook file
`brain/cookbooks/web/seo-aeo/14-ai-answers-and-fan-out.md`.

**Query fan-out**: the sub-queries an assistant rewrites a prompt into before it
searches. Pages that answer those sub-queries are the pages it reads and cites.

Cadence comes from the product's routine table in `docs/product/seo-aeo/plan.md` (the
"Buyer-question check" row): monthly by default, every 15 days at early stage (the
site's first ~6 months; cookbook `09-routines.md`, "Early stage cadence"). The file is
`docs/product/seo-aeo/ai-answers/<period>.md`: `<YYYY-MM>` monthly, the run date
`<YYYY-MM-DD>` at early stage. If the latest non-partial file is less than one period
old, return it and stop.

## 1. Build the prompt set

Read the product's SEO plan (`docs/product/seo-aeo/plan.md`, or the product's file in
the knowledge base's `cookbooks/web/seo-aeo/projects/`), `docs/product/features.md` and
`docs/product/product-market.md`. Reuse the last run's set unchanged so runs compare.

On the first run, or when the set needs a change, you choose it; nobody approves it.
If the product keeps a saved set (`docs/product/seo-aeo/ai-answers/prompts-<date>.tsv`),
reuse it unchanged. Otherwise write 30–50 prompts built around buying decisions, not
keywords: what a buyer asks about the **category**, never the brand. Each gets a `type`
(category, comparison, alternative, use-case, pricing, problem) and a `topic`. Starting
templates: "best X for Y", "X alternative", "how do I <task>", "<competitor> vs",
"<competitor> free plan limit". Seed them from the demand register's
phrases where one exists, and fill `<competitor>` from the active rows of the competitor
roster (`coduo-product-market` skill, `references/competitor-roster.md`). Cut to the set by this rule: drop any that names the product;
of two with the same intent keep the one whose phrase shows in Google autocomplete
(the curl recipe in `coduo-seo-writer` step 1); keep at least three per template that
applies to the category. On later runs retire a prompt only when its premise is gone
(the competitor closed or renamed, the task no longer exists) and add one only for a
new competitor (add it to the roster too) or a demand-register row with two or more sources, each with a dated
note.

**Done when** the set is saved at the top of this run's file with an ID per prompt
(`P01`…), no prompt names the product, and a "Prompt candidates" appendix lists every
candidate with kept or dropped and the reason.

## 2. Run the prompts in the web UIs

Load the `ego-browser` skill and drive the EgoLite browser on the owner's Mac
yourself; the owner does not run or watch the prompts. Use each assistant's normal
web UI: ChatGPT, Claude, Gemini, Google AI Mode; Perplexity and Copilot only while
their free limits allow. No APIs: the API answers
differ from what a buyer sees. A fresh chat per run; signed-out or a clean profile
where the assistant allows it, and record which.

Run core prompts 2 times per assistant and the rest once. Brand lists vary run to run,
but the top of each list is stable and the tail is noise, so two runs are enough. Space
the runs. If an assistant rate-limits, asks for a CAPTCHA or shows a sign-in
wall, stop that assistant, record where it stopped, and go on with the others. Never
solve a CAPTCHA, never sign in, and never wait for the owner to.

Per run, store `body` and `sources` as separate fields, plus `retrieved_urls` for
ChatGPT. Classify the product's verdict by hand (a regex counts source chips as
mentions). Per prompt per assistant, record:

- **Mentioned, recommended, cited**: three separate verdicts, as N/runs each. The
  product can be cited without being named.
- **Cited URLs**: every link the answer cites, with counts; mark the product's own.
  For ChatGPT also the retrieved URLs: a page it read and did not cite.
- **Wrong claims**: anything false about the product or its category, quoted, with
  the run it came from.
- **Competitors named**, with counts.

**Collector.** Drive the runs with one resumable script, not ad-hoc calls:

- 3 prompts per `ego-browser nodejs` call, looped; longer calls get killed (exit 144).
- Resume by `prompt_id#run`, skipping rows already stored.
- Mark stub text ("reached the request limit", "daily limit", "free search limit") as
  `blocked`, never as an answer.
- Clear the editor (select all, Backspace) and verify it is empty before typing.
- One driver per run space; stop the old agent before a replacement takes its run space.
- ChatGPT: read the answer and sources from the DOM; SSE capture is optional.

**Done when** every prompt has a row for every assistant, or a recorded reason it has
none (rate limit, CAPTCHA, assistant down, sign-in wall).

## 3. Capture the fan-out

Record ChatGPT's search queries for each run, verbatim. Gemini and AI Mode do not
expose theirs and Claude's echo the prompt, so spend no time there.

Where an assistant hides its searches, fall back to Google for the prompt's core
phrase: the People-also-ask questions and autocomplete (the curl recipe in
`coduo-seo-writer` step 1). Mark every such phrase `fallback: PAA` or
`fallback: autocomplete`. Never present a fallback phrase as an assistant's search.

**Done when** each assistant per prompt has either verbatim fan-out phrases or
fallback phrases marked as such.

## 3b. Analyse the gaps

1. **Topic gap table**: per topic, competitor appearances minus ours.
2. **Sources**: open the top ~12 sources from runs a competitor won. Per source record
   owner, page type, competitors named, the claim, and whether we are listed.
3. **Page map**: map each prompt to the existing page that should win. Propose a new
   page only for a prompt with none.
4. **Technical layer**: check the host's bot and firewall settings (on Vercel,
   `security.managedRules` and custom rules). Test with 1 request per bot UA, 3 s apart.
   A spoofed UA does not prove real-bot access: confirm with a real fetch (ask
   ChatGPT or Claude to open a URL) and the firewall log.

**Done when** each topic has a gap number, each opened source has its row, and each
prompt has a page path or `none`.

## 4. Write the fan-out register

Merge identical phrases. For each phrase, find the product's page that answers it:
grep the site's content folder for the phrase's nouns and read the hits. A page that
only mentions the topic does not answer it.

Write `docs/product/seo-aeo/ai-answers/<period>.md` in the product repo:

1. Header: date run, assistants, runs per prompt (core vs rest), signed-in state, gaps in coverage.
2. Prompt set (step 1).
3. Results table: `prompt | type | topic | assistant | mentioned | recommended | cited | cited URLs | competitors | wrong claims`.
   Then the topic gap table, the source table and the page map (step 3b).
4. Fan-out register: `phrase | source (ChatGPT or fallback) | prompts | our page or "gap"`.
5. Change since the last run: mentioned, recommended and cited counts up or down, new gaps, closed gaps.

**Done when** every fan-out phrase has a page path or `gap`, and every wrong claim
names the page or listing it most likely came from, or "unknown".

## 5. Hand off

- **Every phrase** goes into the demand register
  (`docs/product/seo-aeo/demand-register.md`; columns in the cookbook README, "The
  demand register"): a new row with source `fan-out`, a link to this file's register
  row, first-found date, covering pages and their count; a phrase already there gets
  this link added and `times covered` rechecked. Fill any due +4/+8 week `AI named`
  impact cells from this run.
- **Gaps** go into the product's pain-point register (`coduo-seo-pain-point`,
  `docs/research/pain-points/`) as demand rows: the phrase, the prompts, the date.
- **Phrases** feed `coduo-seo-writer` briefs: a page's headings and FAQ take their
  wording from the fan-out register.
- **Wrong claims** about the product each get a fix: the page that misleads, or a
  ticket for it.
- Append a one-line summary (date, verdict totals, gap count, file path) to the plan
  doc's routine table.

This skill writes files; it publishes nothing and sends no messages. Commit the run's
files from a worktree, never the user's main checkout, onto a branch, and open a PR: a
routine's output is a PR (cookbook `09-routines.md`, "Scheduling them").

**Done when** each phrase is in the demand register, each gap is in the pain-point
register, each wrong claim has a fix or a ticket, and the plan doc points at this run's
file.
