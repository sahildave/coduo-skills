---
name: coduo-tickets
description: |
  Cut an AFK epic into child GitHub issues, derive the dependency map from their
  real issue numbers, render the Mermaid DAG onto the epic for humans, and write
  the `tasks:` block back onto the epic's `afk:` spec. Wraps `/to-tickets` and
  `/beautiful-dag`. Use after `coduo-epic`, or whenever an epic needs its
  children and its `tasks:` block.
disable-model-invocation: false
---

# Coduo tickets

Four ordered steps, and the fourth is the one that matters:

```
1. create the children          /to-tickets
2. numbers now exist            derive depends_on
3. render for humans            /beautiful-dag  -> epic body
4. write tasks: back            -> epic afk: block      <- the epic runs only after this
```

Step 4 is a **distinct final step, triggered only after every ticket is
pushed**, because the task key in `tasks:` is the child issue number and no
number exists before step 1 returns. It is also the step that is easy to forget:
the epic looks finished after step 3 — PRD, children, a diagram — and it is
**inert**. An epic with no `tasks:` block will not run. Nothing will error at
you; `afk epic <n>` will simply find no tasks and exit in seconds.

## Phase 0 — Read the epic first

```bash
gh issue view <epic> --json number,title,body
```

You need the `afk:` block that `coduo-epic` wrote — specifically `branch`, so
you can confirm you are extending the right epic, and `version: 1`. If there is
no `afk:` block, stop: run `coduo-epic` on this issue before cutting children.
Do not author the block from here.

**Done when** you have the epic number, its branch line, and its acceptance
criteria in front of you.

## Phase 1 — Slice wide and shallow, then create the children

Run `/to-tickets`. It owns the vertical-slice rules, the expand–contract
sequence for wide refactors, and the "quiz the user" approval loop. Use it; do
not restate its rules in your own words and do not skip its approval step.

**Run the authoring phases under a strong model.** Slicing the epic, writing
acceptance criteria (Phase 1) and deriving the dependency edges (Phase 2) is
real synthesis, and ticket quality tracks model strength — run them under Fable
5 or Opus, never Sonnet or Haiku. If you delegate this to a sub-agent, set that
agent's `model` to `fable` (Fable 5, the default) or `opus` — tier aliases, not
version strings; there is no `fable-5` or `opus-5`. The cheap-model default
produced weaker tickets. Only the mechanical `gh` filing and the Mermaid render
(Phases 3–4) are exempt, and even there prefer the strong model over saving
cost.

Four overrides, and two planning constraints that outrank everything.

**The tracker is GitHub.** `/to-tickets`'s local-file mode numbers tickets
`01`, `02` in dependency order. Those are not issue numbers and cannot become
task ids. Publish real issues.

**Every child is a sub-issue of the epic.** The validator checks that every task
key is a real open issue whose **parent is the epic**. Text alone does not
satisfy it:

```bash
gh issue create --title "..." --body-file /tmp/t1.md --label ready-for-agent
gh issue edit <epic> --add-sub-issue <child>
```

**Every ticket and criterion passes the MVP test.** Before publishing, check each
ticket and each acceptance criterion: a main path a normal user walks, a launch
blocker or a real bug, finished to a polished standard. Cut tickets and criteria
for hardening, refactors, premature optimization and rare edge cases (wifi
toggled, Reduce Motion, force quit) unless the epic names them. A small real
follow-up folds into the ticket it belongs to; it never gets its own.

**Publish blockers first**, as `/to-tickets` already says, so each ticket's
"Blocked by" section can name real numbers.

### Prefer wide, shallow slicing

This is a planning constraint the tooling must surface, not a style note.

`dependenciesPassed` requires **every** dependency to have `passed`. A root
failure therefore strands its entire subtree. Shape
`204 → 205/206/207 → 208/209/210 → 211` is depth 3 with a blast radius of seven:
one bad ticket at the root turns into seven skipped ones, and you find out
hours in.

The heuristic, not just the rule:

- **Count the fan-out from the root, not the ticket total.** Eight tickets in
  two waves is a good epic. Eight tickets in four waves is one bad ticket away
  from delivering nothing.
- **Depth 2 is the working target. Depth 3 wants a reason you can say out
  loud.** "205 needs 204's table" is a reason. "205 feels like it comes after
  204" is not — that is sequencing preference, and it costs you the whole
  subtree.
- **An edge you added for tidiness is a liability.** Ask of every edge: does
  this ticket _fail_ without its dependency, or is it merely nicer to do
  second? Delete the second kind. Two lanes touching the same file is a merge
  conflict the integrator resolves; a false edge is a dead subtree.
- **Push shared foundations up, not down.** If three tickets each want a slice
  of the same new module, one root that lands the whole module beats three
  tickets chained behind a partial one. Anything the epic says two tickets
  **share** needs a ticket that owns the sharing, at depth 0. A lane starts with
  no memory of any other lane and cannot see work in flight, so copying is
  locally rational: one epic said in its own words that a new screen "reuses the
  freestyle session wholesale" and the lane copied 150 lines instead. Prose in
  the epic body is not an instruction any lane receives.
- **Serialized integration is the real stall**, not agent count. Every passing
  lane queues for a single merge plus post-merge checks at 1.5–6 min. More
  concurrency does not help; wider and shallower does.

`afk validate` prints depth and blast radius per node — pure graph math, no
tokens. Run it after Phase 4 and read those numbers before anyone starts the
run.

### Fold to the fewest baseline runs

Every builder ticket buys one **baseline run** (the repo's full
`baselineChecks` at integration), plus a lane dispatch, a serialized merge and
a report. That is minutes to tens of minutes per ticket however small the
change, so the ticket count is the epic's wall clock. One day, four tickets
took five hours. This overrides `/to-tickets`' "narrow" slice: here a slice is
as wide as one lane can carry.

Start from **one builder ticket for the whole epic** and split only for one of
three reasons:

1. **Different executor.** Work only a human can do or accept, including every
   decision the epic marks "one-way door", becomes a `gate` ticket. A `gate: after` ticket dispatches no builder, so it costs no
   baseline run.
2. **Different release point.** Part of the work waits on something outside
   this epic (another epic's merge, a human provisioning step) and the rest
   should land without waiting.
3. **Too big for one lane.** The folded ticket would not fit one fresh context
   or the lane clock. Measure the size; a guessed one is how a fold goes
   wrong:
   - **Files.** `git grep -l '<the literal>' -- src e2e | wc -l`, plus every
     recorded baseline (`e2e/__snapshots__/**` and the like) whose page renders
     it, since those re-record with the change.
   - **Clock.** Write time plus three passes of the lane's gate, which is
     `defaultChecks` in `.afk-setup/config.yaml` plus any suite a criterion
     makes the lane run, inside half of `agent.timeoutMs`. Time one pass on
     the base; a flaky test costs a pass, and the half is what pays for it.

   Harbour #429 wrote "about 136 files, splits well by area" and cut one
   ticket: 316 files, a ten-minute browser suite in its criteria, a 60-minute
   clock. Attempt 1 built it in 18 minutes and lost to one flaky test; attempt
   2 was killed at 60 minutes with the work uncommitted.

   Over budget, split so every ticket leaves the suite green on its own: the
   smallest behaviour change with the baselines it moves comes first,
   behaviour-neutral sweeps follow it, and the guard (a lint rule) lands last.
   A ticket that leaves its baselines to a later one fails the integrator's
   browser gate itself.

Everything else folds into its sibling: small tickets, tickets that share
files, per-layer or per-module splits, a ticket that exists only to go second.
Two builder tickets joined by an edge are the first fold to try, since the edge
usually means shared files, which is none of the three reasons.

The proposal the user approves carries the count: a **Why separate** column
naming reason 1, 2 or 3 for every ticket past the first, and a line
`Baseline runs: N (M before folding)`. Fold any ticket whose column would be
empty before you show the table.

- **Only product work becomes a ticket**: user-facing behaviour, a real bug,
  or a launch blocker. Hardening, refactors and enhancements nobody asked for
  are dropped while slicing. Name them in the report with one line each, so
  the user can overrule you.
- **Put the code in the ticket.** When the conversation already worked out a
  snippet, a data shape or an exact edit, paste it into the body so the lane
  applies it instead of rediscovering it. Paste only what you ran: the lane
  applies a snippet as written and cannot tell a guess from a fact, so an
  unrun one sends it down a path that may not exist. If it was not run, write
  the outcome and leave the mechanism to the lane. A mechanism is a mechanism
  whether it is a snippet or a sentence ("the fake refuses an empty list" is
  one). Reading the code it touches gives you facts to state; it does not make
  the mechanism run. The line most often wrong from memory is the one saying
  how one part reaches another at runtime — a lookup, a cast, a global, an env
  var.

### Scope reaches a lane through the body, never the block

A child body carries `## Allowed paths` and `## Prohibited`. Those sections are
the *only* way a scope decision reaches a builder: `allowedPaths` is not a key in
the `afk:` block, and prose in the **epic** body reaches nobody.

Four rules follow, and they are where a night's work is won or lost:

- **A file two children both write makes them one ticket**, unless a split
  reason above keeps them apart; then it is one dependency edge. Advisory scope
  means the runner schedules both lanes happily and the integrator meets a
  conflict-free three-way merge of two edits to one function — which has
  shipped a semantically broken body. Name the shared file, pick the owner, and
  make the other depend on it.
- **When the epic declares a `## File surface`, every child repeats the sibling
  epics' paths in its own `## Prohibited`.** This is the one place duplication is
  correct: a lane reads its issue body and nothing else, so a surface stated once
  on the epic reaches no builder at all.
- **Find a contract's consumers by grepping the API, never from the spec's own
  list of call sites.** The spec's list is what its author remembered; the grep
  is what the code does, and a consumer the ticket never names is one the lane
  leaves broken or fences off. When a consumer sits on another platform, the
  lane must run that platform's check too: the lane gates on its own
  platform, so the break would otherwise surface at integration, where no
  lane learns from it. `afk validate` refuses a criterion that carries a
  `baselineChecks` command verbatim or names `.afk-setup/` or `AGENTS.md`, so
  use one of two shapes. Either the criteria name only the suites the change
  adds or touches (for `xcodebuild`, `-only-testing:<Target>/<Suite>` placed
  before `test`), or the platform's whole-suite command goes in a
  `## Platform gate` section outside the criteria and a criterion reads "the
  gate in `## Platform gate` passes and its summary is pasted".
- **A ticket may not prohibit the file its own mechanism lands in.** For each
  change the body prescribes, name the file it physically lands in and check it
  against `## Prohibited`; a fence that covers it sends the lane into a
  stop-and-report or a workaround in the wrong layer. A fence written for a
  precondition ("until #74 merges") is re-read once that precondition is met.

### A ticket whose only output is a document is planned wrong

The runner discards bookkeeping and protected files from a task's change set, and
if **zero source files** remain it marks the task `blocked` — its dependants with
it. So a spike, an audit, a review or a decision ticket cannot be an ordinary
task, however clearly you word its acceptance criteria. Writing "a code-free run
is a pass here" into the body does not reach the mechanism.

Two shapes that work:

- **Give the finding a home in the tree** — `docs/spikes/<slug>.md`, an ADR — and
  put that path in `## Allowed paths`. The ticket now produces a source file, and
  the finding outlives the run.
- **Or `gate: before`**, and the human releases it after doing the investigation
  themselves.

Reframing "investigate X" as "apply these specific fixes, enumerated in Scope"
also works, when the fixes are actually knowable in advance.

**Done when** the user approved a proposal stating its baseline runs, every
ticket past the first names its split reason, every child issue exists, is a
sub-issue of the epic, carries its
acceptance criteria (a picture for anything a user sees — Phase 4, "What a
criterion may require") and its `## Allowed paths` / `## Prohibited` sections, for
every external service the child touches that has no faithful local stand-in, a
criterion naming the probe that runs against the real service (from the epic's
Testing Decisions, or written here when the child was not cut from an epic), every
ungated child is guaranteed to write at least one source file, and the graph you
have in mind is as shallow as the real data dependencies allow.

## Phase 2 — Derive the dependency map

Now the numbers exist. Turn each child's "Blocked by" into `depends_on`, keyed
by issue number.

Read it back off GitHub rather than off your draft — the user may have edited a
ticket during `/to-tickets`'s approval loop:

```bash
gh issue list --json number,title,body --search "parent-issue:<epic>"
```

Check the three things a validator will check anyway, while it is cheap to fix:

- every `depends_on` entry names a task that is **also a key** in this block —
  a dependency on an issue outside the epic is a dangling reference, not an
  external gate
- no cycles
- every key is a real, open child of this epic

**Done when** you have one map, `{issue: [issue, ...]}`, that satisfies all
three.

## Phase 3 — Render the Mermaid, for humans

Run `/beautiful-dag` over the map from Phase 2 and put the diagram in the epic
body.

**The Mermaid is rendered _from_ the `afk:` block. It is never hand-maintained
alongside it.** Two hand-maintained graphs drift, and the human-readable one is
the one people trust — so the drift is discovered by a human reading a picture
that no longer describes the run. When the DAG changes, change `tasks:` and
re-render. Never edit the diagram to match reality; edit the block and let the
diagram follow.

Two notes where `/beautiful-dag` and the `afk:` schema meet:

- Its step 1 says to prefer native issue dependencies as the source of truth.
  Here the source of truth is `tasks:` — or, on this first pass, the map that is
  about to become `tasks:`. Same graph either way; be explicit about which you
  rendered so a later re-render does not silently pick the other.
- Its `External · gates` subgraph is for things outside the epic. A `gate:
before` task is **not** external — it is a real task with a real issue number
  that a human releases. Style it as a gate if you like; keep it in its phase.

**Done when** the diagram is in the epic body, every child appears exactly once,
and the edges match Phase 2's map node for node.

## Phase 4 — Write `tasks:` back onto the epic

The step everything else was setup for. Do it only after **every** ticket is
pushed.

```bash
gh issue view <epic> --json body -q .body > /tmp/epic.md
# edit the existing afk: fence in place — add tasks:, keep version/branch/max_parallel
gh issue edit <epic> --body-file /tmp/epic.md
gh issue view <epic> --json body -q .body   # read it back
```

The finished block:

```yaml
afk:
  version: 1
  branch: feat/203-stripe-subscriptions
  max_parallel: 3

  tasks:
    204:
      depends_on: []
      gate: before

    205:
      depends_on: [204]

    206:
      depends_on: [204]

    208:
      depends_on: [205, 206]
      checks: [npm run lint:check, npm test]

    211:
      depends_on: [208, 209, 210]
      gate: after
```

### Field rules — a validator rejects anything else

- **Task key is the child issue number.** It is also the AFK task id. Not a
  slug, not a title, not `001`. Issue numbers are unique per repo, which is what
  keeps worktree paths and `.afk/runs/<id>` from colliding across runs.
- **`depends_on`** — a list of issue numbers. Required. `[]` for a root, written
  out; do not omit the key.
- **`checks`** — optional, and only for a **narrower** gate than the repo
  default. **Do not emit it by default.** `.afk-setup/config.yaml` already carries
  `defaultChecks`; duplicating that onto an issue buys nothing and rots
  independently. Absent means `defaultChecks`. Present means the lane runs this
  list *instead of* `defaultChecks` (`baselineChecks` still runs post-merge), so
  repeat every default the lane must keep.
- **`gate`** — optional, `before` or `after`. `before`: a human provisions
  something, then releases the task. `after`: no builder is ever dispatched —
  the task is `awaiting_acceptance` from admission and the human's `--accept` is
  the whole verdict.

  So **a `gate: after` ticket's body must carry the checklist itself**, item by
  item, in the form the human will walk. Nobody else will write one: four epics
  put a device-acceptance ticket through a lane and got three different verdicts
  out of the same shape — `blocked`, `failed`, and `passed` on the strength of
  two commands the builder's own artifact disclaimed. That ambiguity is fixed in
  the runner by never running the ticket, which leaves the checklist to you.
  Check every step against the code: Riverbend #79 step 4 asked the owner for a
  user id the site never shows.
  When the checklist says a failed step gets fixed before acceptance, say how:
  a fix committed to the epic branch outside the runner needs a re-run of
  `afk epic <n>` without `--accept` (it reviews the new head and parks), then
  the accept. "Fix merged to the epic branch … before `--accept`" alone sent
  #1148 into a refused accept on 2026-10-11.
- **Nothing else.** No `title`, no `owner`, no `estimate`, no `allowed_paths` —
  scope is computed at admission, never authored. **Unknown keys are a hard
  validation error, not a silently ignored key.**

### What a criterion may require

An acceptance criterion has to be satisfiable **by a builder in a lane**, and
`afk validate` now refuses the ones that are not:

- **Protected paths.** The runner reverts a builder's edits to lockfiles,
  `AGENTS.md`, `docs/progress.md` and everything under `.afk-setup/`, so a
  criterion requiring one can never be met. One epic marked a task `passed` over
  a test file that never ran for exactly this reason. Name the path in the
  ticket's prose all you like — the refusal reads the criteria.
- **Wiring a new test in is fine, and worth asking for.** `package.json`'s
  `scripts` block is granted to builders by default, so "a new
  `scripts/test-<area>.ts`, appended to the `test` chain" is a criterion a lane
  can satisfy — and a test file the chain never names is a file the gate never
  runs, which the runner now reports as a human action item.

Two more the validator cannot read, so they are yours:

- **A criterion asserts a presence.** `grep … prints nothing` passes when the
  task shipped nothing — three quillnote tasks did, green.
- **A criterion names the spec files the lane runs.** `baselineChecks` runs the
  whole suites at integration whatever the criteria say, so "the e2e suite
  passes" as a criterion buys a second run of a ten-minute suite inside the
  lane, once per self-check. Harbour #432 (epic #429) carried it, and attempt
  2 spent 44 of its 60 minutes re-running the browser suite. Name the specs
  the change adds or re-records; the suite is the integrator's.
- **A screen criterion is a picture.** A child that changes what a user sees
  names its artifact: a snapshot test (`swift-snapshot-testing`, on base via
  `setup-coduo-toolchain` — a lane cannot add it). The product's `AGENTS.md`
  carries the commands and the gotchas (factory products: "Screen criteria
  are pictures"). A snapshot proves the screen did not change, not that it is
  right: it pins a view to its own last recording, so a screen that never
  matched its board stays pinned wrong. A `grep` for a token proves it is
  referenced, not seen: quillnote's switch token passed grep on two hidden
  toggles while the visible one rendered as a blue system checkbox.
- **A design criterion names its board and requires an element inventory.**
  Name the file under `docs/design/` the screen is judged against, and require
  in the report every element the board draws, marked present or absent, and
  every element the app draws that the board does not, each extra removed or
  ticketed. The extras column is the whole value and no grep produces it: a
  grep measures what its author remembered to want, so the element nobody
  asked for is invisible to it by construction. quillnote shipped a compose
  icon that appears in no board's icon set through five gates, twelve
  criteria and a 16/16 closeout; a ten-minute inventory found it. An
  inventory run as a `checks` entry or by a sub-agent runs on Opus —
  `setup-coduo-toolchain` has the measurement.
  **Where the repo can run it, a written claim beats the inventory.** One
  falsifiable sentence about the screen, authored with the ticket and judged
  against the board inside a region — "the drift guard banner draws exactly
  two buttons, Re-push and Stop Mirroring" — holds or fails, and lives in
  `checks` rather than in the report. Keep the sweep beside it: the claim
  covers what the author thought to say; the sweep's extras column covers what
  nobody did.
- **A control criterion is a state change.** A picture cannot catch a dead
  control: quillnote shipped six buttons drawn exactly to the board and
  wired to empty closures, and both the snapshot and the accessibility tree
  passed — an empty closure is still an enabled button. A child that adds an interactive control carries, beside
  its picture, a criterion that drives the built app and asserts the state
  moved — `agent-device click <target> --settle` then `wait text`/`is` on the
  result, or an XCUITest — and the static form a lane can always run: the
  control's handler has a non-test call site, `grep -n <handler>` printing
  it.
- **A check that cannot fail is not a check.** `agent-device diff screenshot`
  exits 0 on a failing pixel diff, so "the diff is pasted" is decorative — it
  is supporting evidence in the report, never the criterion.
- **A baseline records the environment as well as the screen.** Appearance,
  locale, timezone, clock and display scale are all read by the renderer and
  pinned by nothing, so whatever the recording machine was in becomes the
  expected result. quillnote recorded every screen in the host's dark
  appearance for a light-only design, and three real defects — white-on-white
  toolbar glyphs, an empty state lost in the panel glass, a grey-versus-olive
  panel — became the baselines every later run agreed with. A child that
  records its own baseline can therefore pass by recording the bug: the lock
  is a separate ticket at depth 0, and every screen child depends on it.

Title, acceptance criteria and implementation notes **stay in the issue body**
and reach the agent by issue reference. They do not go in the `afk:` block. If
you find yourself wanting to put prose in the block, it belongs on the child
issue.

**Done when** `tasks:` is on the epic, you have read the body back and seen the
fence intact, and every child issue number appears exactly once as a key.

## Phase 5 — Refresh the flow map's view of the tracker

Only when `docs/flow/` exists in this repo, and only when some card carries
this epic in its `epics` list. Skip it otherwise.

The children you just created are the epic's sub-issues, and the map lists them
under every card that carries the epic. It reads them from `epics.json`, which is
a snapshot — it knows nothing about the issues you created ninety seconds ago
until the sync runs:

```bash
python3 <coduo-flow>/scripts/sync_epics.py docs/flow/<name> \
  && python3 <coduo-flow>/scripts/check_flow.py docs/flow/<name> \
  && python3 <coduo-flow>/scripts/build_flow.py docs/flow/<name>
```

Run it again after the epic closes: that is the pass that turns its bar green
and ticks its card. Nothing does this on a schedule, so an unrefreshed map is
the normal failure mode here, and it fails **silently** — a stale map looks
exactly like an accurate one.

**Done when** the card's Details tab lists the epic and every child you created,
each with its state.

## Report

- the epic number, and every child with its `depends_on` and split reason
- baseline runs, before and after folding
- **depth and blast radius per node** from `afk validate <epic>` — the number
  that tells the user whether the slicing is wide enough
- anything you sliced against the user's stated shape, and why
- the confirmation that `tasks:` is written. Say it in those words. Its absence
  is silent, and the user cannot tell a finished epic from an inert one by
  looking at the issue.

## One conflict worth knowing

`/to-tickets` ends with "Do NOT close or modify any parent issue." That rule
exists to stop a ticket-cutting pass from mangling the epic it was reading, and
it holds for the whole of Phase 1.

Phase 4 is the deliberate exception, and it is the entire point of this skill:
an additive edit to the epic's `afk:` fence and its diagram, made by you after
`/to-tickets` has finished. Preserve every other byte of the epic body — read
it, append or replace inside the fence, write it back, read it back.
