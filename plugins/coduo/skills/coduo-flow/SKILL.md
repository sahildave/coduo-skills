---
name: coduo-flow
description: |
  Capture a working session into one markdown note per topic, wire the notes
  into a dependency graph, and render a self-contained HTML flow map whose
  cards open the note behind them. Use when the work spans SEVERAL linked
  topics with dependencies between them — idea validation across many threads,
  strategy or GTM analysis, user-flow mapping, multi-epic or roadmap planning,
  wayfinding an unfamiliar system — or when asked for a flow map, a roadmap, a
  decision map, or a hand-off a teammate can read without you. Reach for it as
  the discussion starts rather than after it ends: notes are written as topics
  close, which is the only way the reasoning survives. A single idea being
  explored is one file, not a map: use coduo-discuss. To map an existing
  repository's architecture from its code, use coduo-code-flow instead.
disable-model-invocation: false
---

# Coduo flow

Three artifacts, one direction:

```
<dir>/flow.json      the config       <- you write this once
<dir>/NN-topic.md    the notes        <- you write these as you talk
<dir>/epics.json     the tracker      <- sync_epics.py generates it (optional)
<dir>/flow.html      the map          <- build_flow.py generates it
<dir>/READINESS.md   what can start   <- readiness.py generates it (optional)
```

The **notes are the single source of truth**. The HTML holds no data of its
own, so an edit made there disappears at the next build. Frontmatter carries
the graph — `kind` is the card's colour, `depends_on` its edges, `status` and
the note's own open items its dots — and the body carries the thinking.

## Open a finished map for someone to review (lavish)

When the ask is only *"let a person read this map and mark it up"* — the notes
already exist, nothing is being captured or rebuilt — do not run the build.
Resolve the map's `flow.html` and hand it to lavish-axi, then wait:

```bash
LAVISH_AXI_TELEMETRY=0 npx -y lavish-axi docs/flow/<name>/flow.html
npx -y lavish-axi poll docs/flow/<name>/flow.html
```

The reviewer annotates cards, question rows and text in the browser; each note
returns with a selector you map back to a note, apply to its markdown, and
rebuild. The whole loop — selectors, mapping, the Layout issues inbox, the
`--agent-reply` step — is **Phase 4**; read it before you start. Only rebuild if
their feedback changes a note; a pure read needs no build.

**Human-present only.** `lavish-axi poll` blocks with no timeout, so it must
never run in an AFK lane, a hook, or any unattended agent. If nobody is at the
browser, there is nothing to open.

## Where the files go

One folder per map, all of them under `docs/flow/`. Same shape in every repo,
so a stranger opening any project knows where to look and the build command is
the same everywhere.

```
docs/flow/
├── README.md                  index: what maps exist here, and what is NOT a map
├── <name>/                    one map
│   ├── flow.json
│   ├── README.md              what this map is; skipped by the build
│   ├── COMPANION.md           optional prose beside the notes — list it in `index`
│   ├── NN-topic.md            the notes
│   └── flow.html              generated
└── <other-companion>.md       anything derived FROM a map, not part of one
```

Name the folder for the question it answers (`product-map`, `pricing`,
`q3-plan`), not for the artefact — every folder here is a flow, so `-flow` in
the name says nothing.

`docs/flow/README.md` earns its place by listing what is deliberately **not** a
flow map. A repo accumulates progress tables, acceptance checklists and design
folders that look adjacent and are owned by other tools; saying so once stops
them being folded in later.

Anything derived from a map — a readiness report, a decision log — either lives
inside the folder and is named in `flow.json`'s `index` so the build skips it,
or sits beside the folder. It never becomes the only home for a conclusion; see
Phase 4.

The map answers what a reader brings to work they were not part of: what are
the pieces, what rests on what, and what did the people who did this actually
conclude. That last one is why every card opens its note. A diagram with no
reasoning behind it is a picture of a conversation, not a record of one.

The page is four tabs — **Roadmap**, **Schedule**, **Open questions**,
**Risks** — and each one only exists when the notes have filled it. Schedule
sits directly after the map because "what blocks what" and "when" are read
together. The first
thing a reader sees, top right, is how many questions are still open and how
many risks are still unheld, because that is the state of the work, and
everything else is the detail behind it.

## Phase 1 — Fix the vocabulary before you write

**First, get the source material.** If the prior thinking lives in a claude.ai
artifact, a Figma file or a Paper canvas, **ask for it as an image or a paste
before writing a single note** — none of those can be fetched, and a map built
without them will miss whole columns of work and need a second pass to find out.

Then pick the scenario's kind vocabulary from
[`references/presets.md`](references/presets.md) — idea validation, user-flow
mapping, multi-epic planning, wayfinding, or your own — and write `flow.json`
with `title`, `kicker`, `lede`, `kinds` and `lanes`.

Set the four things a working map needs while you are there:

- **`categories`** — the departments that answer questions and hold risks, e.g.
  `{"code": "Code", "product": "Design & product"}`. These name **who answers**,
  not what the work touches; on a software project a subject-shaped "code"
  category matches almost everything and filters nothing.
- **`issueUrl`** — so a bare `#123` anywhere links to the tracker.
- **`doneStatuses`** — which statuses count as finished, for the map's
  dim-what-is-built switch.
- **`index`** — any companion prose in the folder that is not a note.

Doing this first is what keeps twenty notes reading as one system. Choosing
kinds note-by-note produces twenty vocabularies and a legend nobody can use.

Leave `spine` empty for now; you cannot know the critical path yet.

**Done when** a reader could infer the shape of the work from `flow.json`
alone: what this is, and what the columns mean.

## Phase 2 — Capture as the topic closes

**Write the note when the topic closes, not when the session does.** A note
written at the end is written from memory, and memory keeps conclusions while
losing the reasoning, the numbers and the discarded options — exactly the
material that cannot be reconstructed later.

So: the discussion moves, a question gets settled, you write that note, and the
discussion moves on. One topic, one file, named `NN-topic-slug.md` — the number
orders the reading and becomes the panel's prev/next order, so number them in
the order a stranger should meet them. When a note starts wanting two
standfirsts, that is two notes.

Write against [`references/note-schema.md`](references/note-schema.md), and
lead every note with its **standfirst** — the `summary` field, which the panel
renders first and largest, before anything else. Put the *answer* there, not
the subject: "Linear's free plan hard-stops issue creation at 251, and the four
exit paths that follow" tells a reader something; "an analysis of the free
tier" makes them go looking. A teammate who reads only standfirsts should come
away with every conclusion you reached.

The panel is three tabs — Details, Open questions, Risks — so a card is a
self-contained brief: what we concluded, what it still owes an answer on, and
what could break it.

Then the body, in this order, because it is the order a reader needs it:

1. The claim, stated plainly.
2. The evidence — quote the number, name the file, cite the source. A claim a
   reader cannot check is a claim they have to take on faith, and six months
   later nobody remembers whether it was checked.
3. What follows from it.
4. **What to go deeper on** — the open threads. This is what lets someone pick
   the note up cold and keep going.

Use `facts` for the two or three numbers a reader wants without opening
anything, and `## ` headings generously: they become the note's navigation rail.

Give every question **and every risk** its categories — which answer **who
answers it**, not what the work touches, and default to `code` and `product`
(override per project with `categories` in `flow.json`). Tag both when both must
agree. They drive the chip filters on both tabs, and they are what turns forty
open questions into "the eleven that are mine". On the risks tab the category filter stacks with severity, so
"high" plus "code" is the list of things about to bite that you can personally
fix. Each question and risk is numbered `Q-n` / `R-n` automatically, so an answer
can arrive from another thread quoting the handle.

**When the map is read off an artefact rather than a conversation** — a
codebase, a repo, a product — Phase 2's "done when" is not a test over the
discussion, it is a test over the artefact: *what have I not opened that could
contain work?* For an application that means, at minimum: the dependency
manifest (installed-and-unused, and conspicuously absent), the platform config
(permissions declared with no code behind them, capabilities nobody designed
for), the build and release config, the issue tracker, and the project's own
progress or status document. Reading only `src/` will miss roughly a third of
the remaining work and every one of those misses looks like a complete map.

**Catch the risk and the open question in the same pass.** When the discussion
says "this only works if legal signs off" or "if she is away that fortnight the
date moves", that is a `questions:` or `risks:` line on the note you are
already writing — one line each, syntax in
[`references/note-schema.md`](references/note-schema.md). They collect into
their own tabs, each row linking back to the note it came from.

A `risks:` line claims a **consequence**, and a consequence is much harder to
evidence than a dependency. Before writing a severity, read the failure path —
the guard, the catch, the fallback, the copy the user actually sees. "This
feature calls that route" is easy to prove and is not the same claim as "this
breaks when the route is down"; severity written from the first is usually a
grade too high, and a `high` that turns out to be a `medium` distorts the plan
around it.

Write the **consequence**, not the hazard: "the quarter ends in week 13, not
week 8" is something a reader can act on; "schedule risk" is a shrug. A risk
with no `mitigated` marker counts as unheld and is what the quick view reports,
so marking one mitigated is a claim you have to be able to defend. Answered
questions keep their line and move to a settled group — deleting them throws
away the one thing that stops the question being re-asked in six months.

**Done when** every topic the discussion settled has a note, every thing it
did *not* settle is an open question or a risk on the note nearest it, and
nothing a reader would have to re-derive lives only in the transcript. Read back through
the session and check — the topics that get skipped are the ones settled early,
when they felt too obvious to write down.

## Phase 3 — Wire the graph

An edge means **this note could not have been written without that one**. Not
"related to" — everything is related to everything, and a graph that says so
renders as a hairball and tells a reader nothing. A preference ("ops would
rather X came first") is not an edge either; it belongs in the note body, since
drawing it makes it look date-moving when it is not.

A path that genuinely returns — a free tier offering an upgrade, a retry after
a failure — is `loops_to: [id]`. It draws as a dashed back edge and stays out
of the layering, so a looping flow keeps its real shape.

Set `depends_on` on each note, then mirror every edge into the other note's
`unlocks`. The redundancy is deliberate: it means each note states its own
place in the graph and reads alone, and the checker keeps the two in step.

Where the work is scheduled rather than merely ordered — a plan, a quarter, a
set of epics — put each note on the timeline with `start` and `length` and give
`flow.json` a `timeline` block. The map says what blocks what; the Gantt says
when, and shading the weeks someone is away is usually what shows you where the
plan really breaks. Everything else needs none of it.

Where the work is run off a tracker, give each note the epics that land on it —
`epics: [68, 91]`, the issues `coduo-epic` wrote. A card accumulates epics over
its life, and several cards may share one. Then
run the sync, which is the only thing here that touches the network:

```bash
python3 <skill-dir>/scripts/sync_epics.py <flow-dir>
```

It writes `epics.json` beside the notes, and the build reads it off disk. What
you get is the question a plan is usually worst at answering: scheduled work
with an empty `epics` list draws **hatched** on the Gantt and **outlined in
dashed red** on the map — it exists only in this folder and nobody can be
assigned it — while a card with a **closed** epic draws green and gets a shipped
tick, because a shipped epic outranks whatever `status:` the note carries and
never un-builds when a newer open epic lands on the same card. Nobody goes back
to edit a status after a merge; the tracker is the thing that stays true.

Both treatments are **derived**, never declared. Do not add a `gap`, `todo` or
`shipped` kind to say the same thing by hand — a kind is a noun, and one that
means "not built" stops being true the day the work lands. See
[`references/presets.md`](references/presets.md) for the argument and
[`references/note-schema.md`](references/note-schema.md) for the rules.

If the work will be run by unattended agents, mark each note's `executor`
(`unattended` | `human` | `mixed`) and then ask the question that changes plans:
**does this human-gated note have an unattended half that could be built
first?** A seam, a mock, an injected interface or a stubbed backend usually is
that half, and building it first is what keeps the agents busy while the human
is unavailable. Executor colours the Gantt bars, so the plan says who as well as
when.

Then set `spine` — the one path through the graph you want a reader to follow
first. In planning it is the critical path; in a user flow it is the happy
path; in an argument it is the load-bearing chain. Naming it is what turns a
graph into a story.

**Done when** every edge names a real dependency you could defend, and the
spine reads as a sentence when you say the node labels out loud in order.

## Phase 4 — Check, build, look at it

Both scripts are stdlib-only Python (3.9+) and take the **flow directory** as
their argument. The script paths are relative to *this skill*, not to the flow
directory, so `<skill-dir>` below is the absolute path of the skill you loaded
this from — resolve it before you run anything, and never hardcode one machine's
copy into a repo:

```bash
python3 <skill-dir>/scripts/sync_epics.py docs/flow/<name> \
  && python3 <skill-dir>/scripts/check_flow.py docs/flow/<name> \
  && python3 <skill-dir>/scripts/build_flow.py docs/flow/<name>
```

Drop the first line on a flow whose notes carry no `epics:` — a decision map or
a user flow needs no tracker and `epics.json` never has to exist.

On a machine that edits the skill it is `~/.agents/skills/coduo-flow`. Installed
as a plugin, the cache is nested **by version** and old versions are kept, so
resolve it rather than guessing — take the highest, not the first:

```bash
SKILL_DIR=$(ls -d ~/.claude/plugins/cache/*/authored/*/skills/coduo-flow \
  | sort -V | tail -1)
```

Write the resolved command into the map's README so the next person does not
have to work it out.

`check_flow.py` errors on dangling ids, one-way edges, dependency cycles, kinds
outside the vocabulary, node labels too long for a card, and a `risks:` or
`questions:` written as a scalar instead of a list; it warns on islands, long
standfirsts, too few lanes, a risk naming no severity, and an open question
that is not phrased as one. Clear the errors. Read the
warnings and fix the real ones — an island usually means you found something
true and never connected it to why it mattered.

The map itself carries the same category filter as the questions tab, derived
from the categories on each note's questions and risks — a filtered-out node
dims to half opacity rather than disappearing, because it is still part of the
graph. A `doneStatuses` switch dims finished work the same way. Both live above
the scroller with the legend, so panning the map never scrolls them away.

**If the session produced a document beside the notes** — a readiness report, a
decision log, a summary for someone else — it is a **view**, and views go stale
silently while the map keeps building. Three rules keep one honest:

- **Regenerate it, never edit it.** Derive it from the notes each time and stamp
  it with the date it was generated.
- **Address everything by handle** (`Q-7`, `R-12`), never by a private numbering
  scheme. Two id schemes for the same questions is how an approved decision ends
  up recorded in one place and reported as open in the other.
- **Anything in it that is not a pointer to a note is a conclusion in the wrong
  place.** Move it onto the note it decides, as an `answered:` line.

`check_flow.py` now warns when two notes ask near-identical questions, which is
the version of this that can be automated — three duplicates survived forty
passes on one map and inflated its open count until the checker found them.

For the common case, **do not hand-write the companion at all.** `readiness.py`
prints the one view the map cannot render — each note joined to its own open
questions, split into what can start and what is waiting — as markdown for a
terminal or a ticket:

```bash
python3 <skill-dir>/scripts/readiness.py <flow-dir> > <flow-dir>/READINESS.md
```

Add it to `index` in `flow.json` so the build skips it. Its 40 generated lines
replaced 169 hand-written ones that had gone wrong in five ways within four
passes.

Then **have a human read the map back to you through lavish-axi** — an
annotation tool that turns the built `flow.html` into a review surface. The
human marks a card, a question row, or any run of text; each note comes back to
you carrying a CSS selector that names the element they clicked, so the feedback
lands on a specific note rather than a general impression.

This is a **human-present** step. `lavish-axi poll` blocks with no timeout: it
must never run in an AFK lane, an unattended script, a hook, or any prompt an
unattended agent reads. If there is no human to annotate, skip to the structural
fallback below.

1. Open it: `LAVISH_AXI_TELEMETRY=0 npx -y lavish-axi docs/flow/<name>/flow.html`.
   The telemetry flag is not optional — the default posts to a third-party
   endpoint. `npx -y` only: never install lavish-axi globally or into a
   `package.json`, and never run `lavish-axi share`, which publishes the
   artifact to a public third-party host with no true delete.
2. The human annotates cards, question rows and text, then sends. You run
   `npx -y lavish-axi poll docs/flow/<name>/flow.html` and leave it running.
   Never pass `--timeout-ms`. If a poll is interrupted, re-run it — feedback
   stays queued until delivered and delivery consumes it, so read each response
   whole.
3. Each returned prompt carries a `selector`. Map it back to a note:
   - `g#node-<id>`, `article#note-<id>` or `div#open-<id>` → the frontmatter
     `id` `<id>` → its file, by reading frontmatter across the flow directory.
     The `id` is the note's kebab-case `id:` field, **not** its filename, so a
     selector `g#node-pricing` need not mean `pricing.md`; `check_flow.py`
     builds exactly this id→file map.
   - `li#q-7` → handle `Q-7` (the id is lowercased; the rendered handle is
     upper) → the note whose `questions:` list owns that number. `li#r-12` →
     `R-12` the same way.
   - A selector inside an open note is anchored on `div#open-<id>`, which names
     the note that was open; a bare `li#q-7` is the canonical tab-level row.
4. **Apply the feedback to the note markdown, then rebuild** with
   `sync_epics.py` / `check_flow.py` / `build_flow.py`. Never edit `flow.html`:
   it is generated and the next build destroys any change made there. lavish-axi
   watches the file and live-reloads on save, so the human sees your rebuild.
5. Report back and keep waiting:
   `npx -y lavish-axi poll <file> --agent-reply "<what changed>"`.
6. Rendering failures the structural checks cannot see — a chip white on white,
   a clipped label — are filed passively in lavish-axi's **Layout issues** inbox
   and reach you only when the human queues them, arriving tagged
   `layout-warnings`. Fix those in the **shell template or the generator**, never
   in `flow.html`.

When the round is done, `npx -y lavish-axi stop` shuts the background server.

Where you cannot open a browser, verify structurally instead and **say plainly
that you have not looked at it**: every note id present in the HTML, the lane
headers, the card labels, the tab bar and its panel ids, and a probe of one
note's body text.

Structural checks are not a substitute and it is worth being honest about the
gap. They catch a missing id; they cannot catch a chip rendering white on white,
a sticky bar 48px narrower than the thing it is pinned over, or one tab bar
styled unlike another. **A style bug does not look like a bug** — it looks like
a slightly different design decision, and it will survive several passes of
work built on top of it.

**Done when** the map opens, every card leads somewhere worth reading, someone
who was not in the session could act on it, and — where a human reviewed it
through lavish-axi — every annotation they sent has been applied to the notes
and rebuilt, not left in the review thread.

## What the page can do, once it has volume

A map of eight notes is read. A map of twenty-eight is *interrogated*, and the
output assumes it will be:

- **Filters.** Both the questions and the risks tabs carry a category chip bar
  (multi-select, ORs). Risks add a severity bar, and the two AND — "High" plus
  "Code" is the high-severity code risks. The roadmap carries the same category
  chips: a filtered-out node **dims to half opacity rather than disappearing**,
  because a dependency you filtered out is still a dependency.
- **A dim-what-is-built switch** on the roadmap, driven by `doneStatuses`. On a
  map with more shipped than unshipped it is the difference between a plan and a
  wall.
- **Handles.** Every question and risk is numbered `Q-n` / `R-n`, rendered in
  front of the line and usable as an anchor. This is what makes the register
  answerable: without a name, question eleven cannot be answered from another
  thread. Expect answers to arrive as "Q-11: use the overall score."
- **Search over questions and risks**, not just notes, each hit labelled and
  carrying its handle.
- **A three-tab note panel** — Details, Open questions, Risks — using the same
  row component and the same tab bar as the page itself.
- **Facts shut by default**, behind "At a glance" with a count. On an
  agent-driven project a note serves two readers who want opposite things: the
  builder reads the whole body and needs the exact route name; the person
  deciding what to do next needs the argument. Write facts a human would say out
  loud — a threshold, a count, a decision — and let the route names live in the
  body.

## Adding to a flow that already exists

Read `flow.json` for the vocabulary and skim the existing standfirsts before
writing anything — a new note in a fresh vocabulary is worse than no note. Then
Phases 2 through 4 unchanged, remembering to mirror the new edges into the
notes on the other end.

**New work does not always mean a new note.** A card is a durable thing and a
card carries the epics that land on it, so ask first whether the work *extends
something already here*:

- **Extends an existing card** (a field on a screen, a state on a flow): it is
  not a new note. Append the epic to that card's `epics` list — even if the card
  already shipped — and answer any open question the work resolves with an
  `answered,` line. No new bar; the work rides the card it belongs to. This is
  the common case for small epics and every bug fix.
- **A genuinely new feature, screen or system**: a new note, with its own place
  on the timeline (`start`, `length`, `executor`) and its own `epics`. This is
  what keeps the map growing as the product does.

The test is the same one that decides any note: could this stand as its own
standfirst, or is it a paragraph in an existing one? A username field in Settings
is a paragraph in Settings. A whole new onboarding flow is its own note.
