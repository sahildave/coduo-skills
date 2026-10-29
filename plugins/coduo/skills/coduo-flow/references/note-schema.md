# The note and the flow config

Two files define everything the build reads. Nothing about the graph is written
twice: `check_flow.py` fails on any drift.

## A note

One markdown file. Frontmatter carries the graph; the body carries the thinking.

```yaml
---
id: kebab-case-id        # stable, referenced by depends_on/unlocks. Never renamed casually.
title: The full title    # shown in the panel header and the search results
node: Short label        # <= 24 chars — the card's label. Longer is a hard error.
caption: shorter still   # optional, the card's second line. Aim for <= 32 chars.
kind: finding            # from flow.json `kinds`; drives the card colour
status: proposed         # open | proposed | validated | decided
confidence: high         # high | medium | low. Optional but cheap and useful.
executor: unattended     # unattended | human | mixed. Optional; colours the Gantt bar.
epics: [68, 91]          # optional: the tracker epics that have landed on this card
summary: One sentence.   # THE STANDFIRST — see below. Required.
facts:                   # optional key-value chips, "Label: value"
  - "Free: 1 project, unlimited issues"
  - "Pro: $7.99/mo"
depends_on: [other-id]   # inbound edges
unlocks: [another-id]    # outbound edges — the exact inverse of depends_on
loops_to: [earlier-id]   # optional return path: drawn dashed, never layered
risks:                   # optional: what could break, one line each
  - "high: The billing owner's February leave lands mid-split."
questions:               # optional: what is still unanswered, one line each
  - "week 1: Can the S3 move run during the Postgres upgrade?"
start: 3                 # optional: first unit on the timeline (see below)
length: 4                # optional: how many units it runs; defaults to 1
updated: 2026-08-22      # required
---
```

### `facts` are reference material, and are shut by default

The chips live behind an "At a glance" disclosure with their count on it. That
is deliberate: on an agent-run project the notes accumulate exact route names,
symbol names and file paths that a *builder* needs and a *reader deciding what
to do next* does not. Collapsing them keeps both audiences without either
drowning.

Write facts a human would quote out loud — a threshold, a count, a decision, a
state list. `Unlocks at: 3 day streak` earns its place; `API routes:
voice-studio, daily-script, judge-content` belongs in the note body, where the
agent reading the whole thing will still find it.

Labels are read cold, with none of the note behind them, so `Guard:`, `Store:`
and `Metrics:` land as three words that could mean anything. `How it decides:`,
`Where it is stored:` and `What it measures:` cost four more characters and
explain themselves. The test: read the label alone, out loud, with no note
around it.

### `summary` is the standfirst, and it does the most work

The panel opens with the note's title, then the standfirst directly under it as
the largest body text on the page — the deck under a headline. It is the first
prose a teammate reads, and for most of them it is the only prose they read.
Write the **answer**, not the topic: "Linear's free plan hard-stops issue creation at 251,
and the four exit paths that follow" beats "an analysis of Linear's free tier".
Someone who reads only the standfirst should be able to repeat your conclusion.

Under ~200 characters, ending in a full stop. The checker warns past that.

### `depends_on` and `unlocks` are exact inverses

If A lists B in `depends_on`, B lists A in `unlocks`. That redundancy is
deliberate — it means every note states its own place in the graph and can be
read alone — and `check_flow.py` enforces it, so it cannot rot.

Edges mean **this note could not have been written without that one**. They are
not "related to". A graph where everything points at everything renders as a
hairball and tells a reader nothing.

`loops_to` is the exception: a return path the reader can actually take. It is
drawn as a dashed back edge and excluded from layering, so it neither creates a
false cycle nor forces a looping flow to leave a real path undrawn. It needs no
inverse.

**Notes can link to each other.** A markdown `[label](#other-id)` whose target
names a note opens that note in the panel. Anything else stays an ordinary
anchor.

### `risks` and `questions` hang off the note they came from

Both are lists of one line, split on the first colon exactly like `facts` —
prefix, then the sentence. They collect into their own tabs, and every row
links back to the note it was written on, because a risk with no note behind it
is a mood rather than a finding.

`risks` — the prefix is severity, optionally `mitigated`, and any number of
**categories**, in any order:

```yaml
risks:
  - "high, devops: The February leave lands mid-split; the quarter ends week 13, not 8."
  - "medium, mitigated, code: Contends with the upgrade for DBA time — sequenced first."
```

Categories are the same four the questions use — `code`, `devops`, `product`,
`design` — and they render as a second chip filter beside the severity one. The
two **AND** together, so "High" plus "Code" is the high-severity code risks
rather than either. That combination is the one worth having: "what is about to
bite me that I can personally fix" is a different list from "what is high".

Severity is `high`, `medium` or `low`; leaving it out reads as medium and the
checker warns. The risks tab carries an All / High / Medium / Low filter over
them, so "what are the high ones" is one click rather than a read-through. Anything without `mitigated` counts as unmitigated, and that
count is the number the quick view puts at the top of the page. **Write the
consequence, not the hazard** — "the quarter ends in week 13" is actionable,
"schedule risk" is not.

`questions` — the prefix is a comma-separated list of **categories**, optionally
including `answered`:

```yaml
questions:
  - "code, devops: Can the S3 move run during the Postgres upgrade?"
  - "product: Who signs off the evidence pack, security or legal?"
  - "answered, product: Does the auditor accept quarterly sampling? Yes, in July."
```

Categories answer **who answers it**, not what the work touches. On a software
project everything touches code, so a subject-matter "code" category matched 46%
of one real register and told nobody anything. Ownership is the split that
works: each person filters to their own department and sees exactly what is
waiting on them.

The default vocabulary is two — `code` and `product` — and a flow overrides it
wholesale with a `categories` object in `flow.json`:

```json
"categories": { "code": "Code", "product": "Design & product" }
```

Tag both when both must agree. The filter ORs, so a shared item shows up for
either person, which is the right behaviour: if it needs both of you, both
should see it. Risks take the same vocabulary, so one set of chips covers both
tabs.
They render as a multi-select chip filter above the list, so a reader can narrow
to the questions they are actually able to answer today. That is the point: a
list of forty questions is a wall, and "the eleven product ones" is an
afternoon.

Prefer categories over a deadline. An earlier version of this schema used the
prefix for timing (`week 1:`, `before kickoff:`), and in practice every line
ended up saying "before the epic", which told a reader nothing they could act
on. The old form still parses and renders as a plain chip, so existing flows keep
working — but a deadline that is the same for every row is not information.

**Every question and every risk gets a stable handle** — `Q-7`, `R-12` — numbered
in note order and rendered in front of the line. It is there so an answer can be
given somewhere else and still land: *"Q-11: use the overall score. Q-19: ship
without it."* Each is also an anchor (`#q-11`), and both are in the search index,
so searching a term finds the open question about it and not only the note that
mentions it. Handles shift if a note is renumbered, which is one more reason not
to renumber.

An answered question does not get deleted; it moves to a settled group at the
bottom of the tab. That is the whole value of writing it down — six months on,
the question someone is about to re-ask is already there with its answer.

The prefix is only read as a prefix when the whole of it is tokens the parser
knows (for a risk) or is short and question-mark-free (for a question), so a
line that merely happens to contain a colon keeps its whole sentence.

### `epics` is the join to the tracker, and a card carries a list of them

A card is a durable thing — a screen, a system, a rule — and the work that lands
against it over its life is a **list** of epics, not one. `epics: [68, 91]` is
the canonical form: #68 built the screen, #91 added a field, and both are part
of the card's history. `epic: 68` (scalar) still parses as a one-element list,
so older maps keep working, but write `epics:` for anything new. Both keys at
once is ambiguous and fails the build.

Several notes may also name the *same* epic — one epic across three screens is
three cards sharing a number. The relationship is many-to-many, which is what
lets a permanent card outlive the transient epics that touch it. (A single
`epic:` was the same category error as a lifecycle `kind`: a transient value
stapled to a permanent noun, decaying every time an epic closed.)

It is the one field whose *truth lives somewhere else*, so nothing about it is
read at build time. `sync_epics.py` fetches each epic and its sub-issues once and
writes `epics.json` beside the notes; `build_flow.py` reads that file and never
touches the network, which is what keeps a rebuild deterministic and its diff
readable.

```bash
python3 <skill-dir>/scripts/sync_epics.py <flow-dir>   # writes epics.json
```

The card's state is aggregated over the list:

| The card's epics | The Gantt bar | The card |
|---|---|---|
| none, and on the timeline | hatched, in its executor's hue | dashed red outline over its kind's fill |
| some, none shipped yet | the ordinary executor fill | unchanged (work in progress) |
| at least one shipped | solid green | green tick, counts as built |

**A shipped epic outranks the note's own `status`, and never un-builds.** Once
any attached epic has closed, the card is built: the note says what we decided,
the tracker says what shipped, and shipped is the stronger claim (nobody edits
`status:` after a merge). A newer *open* epic on the same card — a field added to
a screen already live — is work in flight against a thing that exists, so it
appears in the panel and leaves the bar green. The card is built and evolving,
both true at once, which one collapsed tick could not say.

An epic closed as **not planned** is not shipped. GitHub gives it the same
`state` as one that shipped, so `sync_epics.py` records `stateReason` and the
build treats `not_planned` as not built; the panel says "closed, not planned" so
a closed-but-not-green epic is never a mystery.

The hatch is the useful half. A bar with no epics is a piece of the plan that
exists only in this folder — nobody can be assigned it, no agent can run it, and
it is the honest answer to "what is left to write". On a map where most bars are
hatched, that is the finding.

**The roadmap says the same thing in the same way.** A card gets a dashed red
outline, over whatever fill its kind gives it, when all three hold: it is on the
timeline (`start`), its `epics` list is empty, and it is not done. All three
matter — `start` distinguishes work still to come from a screen that shipped
years before this map existed, and an *open* epic already counts as filed, so a
card with one is in progress, not unbuilt. The treatment only switches on for a
flow where at least one card carries an epic, so a decision map is untouched.

None of that is declared. It is read off the tracker the same way the Gantt is,
which is the point: a kind that means "not built" stops being true the day the
work lands, and then argues with the tick beside it.

Because the map spends red on this, **do not give a flow that uses `epics:` a
`danger`-toned kind.** Two different claims in one colour is worse than either.

`epics.json` carries the **datetime** it was written. The page eyebrow renders
it at full ink — `Last updated: 3 days ago • 11:23 AM 21 Aug` — with the
relative half computed in the browser at read time, because a "just now" baked
in at build time is exactly the lie the line exists to prevent. The footer
carries the same date in prose. The
snapshot going stale is this design's worst failure mode precisely because it is
invisible: a rebuild reproduces yesterday's tracker exactly and looks deliberate
doing it, so the date is the only thing that distinguishes "no epic yet" from
"nobody has asked GitHub since March".

`check_flow.py` fails on an entry that is not an issue number and on a note that
sets both `epic:` and `epics:`, warns when a note names an epic that `epics.json`
has never heard of (run the sync), warns once listing every timeline note with no
epic at all, and warns when
`epics.json` carries an epic no note claims — which means the sync ran ahead of
the notes, or a note lost its `epic:`.

### `executor` is a third axis: who can actually do the work

`kind` is what a note *is*, `status` is how settled it is, and `executor` is
**who has to be present**. On a plan run by unattended agents that is the axis
the schedule really turns on: the dependency graph tells you what is *possible*
next, and the executor tells you what can start tonight with nobody at the desk.

```yaml
executor: unattended   # an agent can run it end to end
executor: human        # credentials, hardware, an account, or a decision
executor: mixed        # it splits — and this is the common case
```

It colours the Gantt bar and nothing else: `unattended` warm, `human` cold,
`mixed` literally half of each so a split epic is legible as one bar. When any
note carries an executor the bar legend switches to the executor key, because
the critical path is already drawn on the map and does not need saying twice.

**`mixed` is the interesting value.** Before marking a note `human`, check
whether it has an unattended half that could be built first — a seam, a mock, an
injected interface, a stubbed backend. It usually does, and finding it is worth
more than the scheduling: it means the human sitting is short and the work
waiting on it is already done.

### The note panel is three tabs

**Details**, **Open questions** and **Risks**, using the same row component
*and the same tab bar styling* as the top-level tabs — two tab bars that look
different on one page read as two different mechanisms — so the two places
cannot drift into naming or ordering the same thing differently. The Details tab
opens with a collapsed facts row, then a vertical **Table of contents** built
from the note's `## ` headings, then the prose. The tab bar only appears when a note actually has
questions or risks; a note with neither is just its prose.

### A danger-toned kind and a done status contradict each other

`kind` and `status` are independent axes — but a `danger`-toned kind (`gap`,
`blocker`) is the one kind that *asserts a state*: it says the thing is not
built. Give that note a status in `doneStatuses`, or an epic that closed, and
the card is simultaneously drawn red for "not built" and dimmed by **Dim what is
built**. A reader gets two contradictory claims on one card and no way to tell
which is current.

It is a data problem every time — the kind was never updated when the work
settled — and it is invisible until someone toggles the switch, so
`check_flow.py` warns on it by name.

The remedy is usually a kind the vocabulary is missing. A map that only has
`gap` for unbuilt work has nowhere to put the same note once it ships, so the
note stays red. Give it a `shipped` kind on its own tone — `muted` reads well,
since built work receding is what the dim switch is for — rather than promoting
it into a kind that means something else.

### `status` and `kind` are different axes

**A kind is a noun; it is never a lifecycle state.** The test: can the same note
keep this value for its whole life? A note about the Settings screen is a
`screen` before it exists, while it is built, and after it ships — that is a
kind. `gap`, `todo`, `done`, `shipped` are true only for a stretch, and they
belong on the axes that already render lifecycle: `status`, `epic:`, the tick,
and the dim switch. `check_flow.py` warns on a kind built from one of those
words, and on two used kinds sharing a tone. The full argument, with the table
of which field answers which question, is at the top of
[`presets.md`](presets.md).


`kind` is what a note *is* (a finding, a decision). `status` is how settled it
is. A decision can be `open`; a finding can be `validated`. The card shows kind
as colour. Its top-right dots are derived, not declared: red for an unheld risk,
amber for an unanswered question, green when the status is settled —
right-aligned, so a card reads "done but still owes answers" or "clean" from
across the room. There is deliberately no dot for "not settled": the card's own
colour already says that.

## `flow.json`

Sits beside the notes. Every field is optional.

```json
{
  "title": "Where Atlas sits between GitHub Issues and Linear",
  "kicker": "Atlas · go-to-market · August 2026",
  "lede": "One paragraph orienting someone who has never seen this before.",
  "out": "flow.html",
  "nodeWord": "topics",
  "lanes": ["EVIDENCE", "SEGMENT & MOAT", "IMPLICATIONS", "EXECUTE"],
  "spine": ["linear-free-tier-wall", "paywall-blocker", "pricing", "execution"],
  "spineLabel": "Critical path",
  "kinds": { "finding": { "tone": "plain", "label": "Finding" } },
  "tally": [{ "value": "2", "label": "open blockers" }],
  "index": "README.md",
  "webfonts": false,
  "questions": { "tab": "Open questions", "title": "Open questions",
                 "lede": "Answer these in week 1." },
  "risks": { "tab": "Risks", "title": "Risk",
             "lede": "Where the plan actually breaks." },
  "timeline": {
    "tab": "Schedule",
    "units": 13,
    "unitLabel": "week",
    "rowLabel": "Workstream",
    "title": "When each piece runs",
    "lede": "One line orienting the chart.",
    "bands": [{ "from": 5, "to": 9, "label": "February - owner away" }]
  },
  "footer": "One line on provenance."
}
```

- **`lanes`** label the columns left to right. The builder lays notes out by
  dependency depth, so lane 1 is everything with no `depends_on`, lane 2 is
  everything that depends only on lane 1, and so on. Name them for what that
  depth *means* in your scenario. Too few lanes is a warning, not an error.
- **`doneStatuses`** names the statuses that count as finished work, defaulting
  to `["validated"]`. The roadmap gains a switch that dims those nodes, which is
  how a map with more shipped than unshipped on it stays readable.

- **`spine`** is a list of ids read as a path. Consecutive pairs must be real
  edges — a typo is an error, not a silently missing red line. This is the one
  arc through the graph you want a reader to follow first.
- **`kinds`** maps a kind to a `tone` and a display `label`. Tones are a closed
  set: `plain` (blue), `warn` (amber, gets a diamond), `danger` (red), `ok`
  (green), `muted` (grey), `sheet` (grey fill), and `none` — embedded and
  searchable but never drawn, for a sources or glossary note.
- **`issueUrl`** turns every bare `#123` in a fact, a question or a risk into a
  link to your tracker: `"issueUrl": "https://github.com/you/repo/issues/"`.
  Left unset, `#123` stays plain text — guessing a tracker would be worse than
  not linking. Note bodies are unaffected; write those as ordinary markdown
  links.

- **`categories`** replaces the question and risk category vocabulary wholesale,
  e.g. `{"code": "Code", "product": "Design & product"}`. See the categories
  section above: these name **departments**, not subjects.

- **`index`** names a file to skip. Its default, `README.md`, lets the folder
  keep a human index without it becoming a card.

- **`webfonts`** loads Archivo, Source Serif 4 and IBM Plex Mono from Google
  Fonts. Off by default, because the whole point of the output is that it works
  with no network; the type stack falls back to Palatino and Georgia, which is
  the same structure in system faces. Turn it on for something you publish and
  leave it off for something you commit.

- **`timeline`** turns on the Gantt. Give it `units` (how many weeks, sprints or
  days the chart spans) and place notes on it with `start` and `length`. Only
  notes carrying a `start` appear; everything else stays on the map alone, so a
  decision map or a user flow needs none of this. `bands` shade a stretch —
  a holiday, a freeze, an absence, or a window in which only one kind of
  executor can work — which is usually where a plan actually breaks. Each band
  gets its own fill rather than a shared wash, so four labelled windows read as
  four windows. Rows and bars are clickable through to their notes, so the chart is
  another way into the same knowledge rather than a second picture to maintain.

  A bar running past the end of the timeline is an error, not a silent clip.

- **`questions`** and **`risks`** rename their tab, heading and standfirst.
  Each block only appears when at least one note carries that field, so a
  decision map with neither stays a single page with no tab bar at all.

## Tabs

The output is one page in four panels — Roadmap, Schedule, Open questions,
Risks, in that order — and a tab only exists when it has something in it.
Schedule follows the map directly: a reader who has just read the graph wants
the dates next, and the questions and risks are the detail behind both. A flow with one
panel shows no tab bar.

Search sits above the tabs and reaches every note from every panel, so a hit
found while reading the risks opens the same note it would have from the map.
`#<note-id>` deep-links a note as before; `#tab-risks` deep-links a panel.

The **quick view**, top right, is the one thing a reader sees before choosing a
tab: how many questions are still open and how many risks are still unheld.
It renders only when the notes carry at least one of either.

## What the build produces

`flow.html`, beside the notes. Self-contained: no server, no network, no
markdown parser on the page. Every note is embedded as pre-rendered HTML, so
clicking a card opens it instantly and search covers all of them.

Regenerate rather than edit — a change made in the HTML disappears at the next
build.
