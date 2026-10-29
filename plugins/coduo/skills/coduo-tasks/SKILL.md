---
name: coduo-tasks
description: |
  Author the `tasks/` directory the AFK wave runner executes unattended
  overnight — no tracker, no pull requests. Wraps `/to-tickets` and retargets
  it at a small-to-medium executor. Use for a one-shot overnight build, for a
  project that runs from `tasks/` instead of issues, or when
  `coduo-wayfinder` picks the one-shot branch. GitHub-issue runs use
  `coduo-epic` and `coduo-tickets` instead.
disable-model-invocation: false
---

# Coduo tasks

The one-shot path. `coduo-epic` + `coduo-tickets` publish to GitHub and the
runner works the issue graph; this publishes nothing. `afk wave` runs the
directory overnight and merges each wave onto `main` itself.

```
tasks/GOAL.md        the intent every wave is reviewed against
tasks/tasks-todo/     one file per task
tasks/tasks-done/     the runner moves files here. You never write here.
```

A loader accepts or refuses the whole directory. **Authoring ends when
`afk wave validate` exits 0**, not when the files look right.

## Phase 0 — Refuse early

Each of these, absent, produces a 3am failure whose error names none of them.

- The **scaffold is committed and green** on the base branch. A lane cannot
  create the project or install a dependency: the runner reverts manifest
  edits, so the lane's green describes a chain that no longer exists.
- The **check commands pass right now**. Run them. A red baseline makes every
  lane failure unattributable.
- **`afk wave validate` exists.** Without the loader these files are a
  directory of hope. Stop and say so.
- **`tasks/tasks-todo/` is empty**, or half a previous night joins this graph.
- **`.afk/` is in the base branch's `.gitignore`.** The runner refuses to
  start without it, and a fix committed after launch never reaches a wave
  already recorded: waves replay from their recorded base sha, so the remedy
  is wiping the untouched wave state and relaunching, not resuming.

**Done when** all four hold and you have the check output.

## Phase 1 — GOAL.md

One file: product intent, the architecture decisions already settled, the
standing prohibitions. The plan reviewer reads it as the thing each wave is
checked *against*, so it carries what a task file cannot — the shape of the
whole.

Write constraints as facts about the project ("routing lives in X", "the
manifest is generated"), not as advice. A small model reads this as ground
truth.

**Done when** someone who saw no other file could tell whether a given task
belongs to this project.

## Phase 2 — Slice

Run `/to-tickets` for the slicing, the expand–contract sequence and the
approval loop. Five deviations, all consequences of an executor that is small
and unattended:

1. **Smaller.** One vertical slice with room left in a fresh context. If it
   does not fit on one screen it is two tasks.
2. **Name every file.** `/to-tickets` avoids paths because they go stale; here
   they are the point. "Add the repository layer" makes a small model invent an
   architecture; `Sources/Data/RepoStore.swift` with three named methods does
   not.
3. **Ordered steps**, which `/to-tickets` omits because a strong model infers
   them.
4. **Criteria are commands.** Each one exits 0, or is a test that fails against
   HEAD before the change and passes after. An exported symbol needs a non-test
   caller. **A control criterion is a state change.** A picture cannot catch
   a dead control: quillnote shipped six buttons drawn exactly to the
   board and wired to empty closures, and both the snapshot and the
   accessibility tree passed — an empty closure is still an enabled button. A task that adds an interactive control
   carries, beside its picture, a criterion that drives the built app and
   asserts the state moved — `agent-device click <target> --settle` then
   `wait text`/`is` on the result, or an XCUITest — and the static form a
   lane can always run: the control's handler has a non-test call site,
   `grep -n <handler> App/ Sources/` printing it. One condition per criterion — an `or` is an escape hatch and a
   well-behaved agent takes it. **A criterion asserts a presence**: `grep …
   prints nothing` passes when the task shipped nothing, and three quillnote
   tasks did, green. **A screen criterion is a picture**: a task that changes
   what a user sees names a snapshot test (`swift-snapshot-testing`, installed
   on base by `setup-coduo-toolchain`) — the product `AGENTS.md` "Screen
   criteria are pictures" section has the commands. A snapshot proves the
   screen did not change, not that it is right: it pins a view to its own
   last recording, so a screen that never matched its board stays pinned
   wrong. **A design criterion names its board** — the file under
   `docs/design/` the screen is judged against — and requires an **element
   inventory** in the report, the one criterion that is a table rather than a
   command: every element the board draws, marked present or absent, and
   every element the app draws that the board does not, each extra removed or
   given its own task file. The extras column is the whole value and no grep
   produces it: a grep measures what its author remembered to want, so the
   element nobody asked for is invisible to it by construction. quillnote
   shipped a compose icon that appears in no board's icon set through five
   gates, twelve criteria and a 16/16 closeout; a ten-minute inventory found
   it. An inventory run as a `checks:` line or by a sub-agent runs on Opus —
   `setup-coduo-toolchain` has the measurement.
   **Better than an inventory, where the repo can run it: a written claim.** An
   inventory is something the agent produces and then grades itself against; a
   claim is one falsifiable sentence about the screen, written at ticket time
   by whoever knew what it was for, judged against the board and scoped to a
   region — "the drift guard banner draws exactly two buttons, Re-push and
   Stop Mirroring", "the surface draws exactly three switch rows and a Quit
   control, and no section headers". It holds or it fails, and it belongs in
   `checks:` beside the sweep rather than in the report. Keep the sweep too:
   the claim covers what the author thought to say, the sweep's extras column
   covers what nobody did.
   **Pair every board before you cut a screen ticket.** Coverage is the
   denominator, and a sweep that prints its gap without failing on it
   certifies whatever it looks at. quillnote finished 103/103 with every gate
   pair clean and an app that did not look like the design: 31 boards, 16 with
   no pairing at all, 18 of 22 pairs cropped rather than full-frame, and the
   sweep printing `Frames with no pairing: 16 of 31` on every run while exiting
   0. Write the whole `pairs.d/` manifest before the first screen task, default
   each pair to full-frame, and refuse to schedule a screen task whose board
   has no pair. A criterion asking that `--list` show no `pending` line is not
   a coverage check -- `pending` means a declared pair awaiting work, and a
   board nobody paired cannot appear at all.
   **And gate design from the first screen task, not the last.** quillnote'
   first task carrying any design check was task-75 of 103; the other 74 were
   measured after the fact, which is not the same as being gated. A task that
   builds one control has a falsifiable claim about it the moment it is
   written, so the judge works on day one.
   **Gate on what you can fix.** Scope the sweep line to a pair the task owns
   — `vision-pass-all.sh <PairName>`. A `checks:` line that can fail on a file
   the task's `owns:` excludes fails the lane for something it is forbidden to
   touch, and no retry clears it. quillnote task-89 carried the bare repo-wide
   command while owning two markdown files: it failed three attempts on an
   empty-state card no task in the wave owned, went terminal, and stranded the
   wave's fast-forward — 9 finished tasks were landed by hand. The sharpest
   form of the trap is a report-only task gated on the findings it exists to
   report, which passes only on a day it has nothing to say. Repo-wide
   instruments run outside the task graph until the runner reads a
   `closeoutChecks` key (afk-claude#101).
   A `grep` for a token proves it is referenced, not seen: the moss-switch
   token passed grep on two hidden toggles while the visible one rendered
   blue. A check that cannot fail is not a check: `agent-device diff
   screenshot` exits 0 on a failing pixel diff, so "the diff is pasted" is
   decorative — it is supporting evidence in the report, never the criterion.
   **Screen content comes from the fixture.** The product `AGENTS.md` names
   the one fixture its boards and previews both render from, so a board and
   its snapshot differ only in structure, never in text. Open the board and
   the fixture before writing the task: content the board shows that the
   fixture lacks is a fixture step, ahead of the screen step or in its own
   task the screen task is `blocked_by`. The task's `Read first` names the
   fixture, and one criterion is `grep -n <Fixture> <the preview's file>`
   printing the line. A preview that would build its content from a literal,
   a live store or a clock is a task you rewrite, not one you ship: the
   fixture is where the content changes. A repo whose `AGENTS.md` names no
   fixture gets one task that adds it, and every screen task is `blocked_by`
   that task.
   **A baseline records the environment as well as the screen.** The fixture
   pins the content; nothing yet pins the appearance, locale, timezone, clock
   or display scale the renderer reads, so whatever the recording machine was
   in becomes the expected result. quillnote recorded every screen in the
   host's dark appearance for a light-only design, and three real defects —
   white-on-white toolbar glyphs, an empty state lost in the panel glass, a
   grey-versus-olive panel — became the baselines every later run agreed with.
   A task that records its own baseline can therefore pass by recording the
   bug. The recording environment belongs to a separate task that locks it,
   and every screen task is `blocked_by` that task, exactly as on the fixture.
   Pay the serial waves: a leaf that records first certifies whatever it drew.
5. **The graph is the concurrency control.** Two tasks touching one file get an
   edge, never a hoped-for merge.

**Done when** the user approves the breakdown and you have read the widest
dependency level — past about eight unblocked tasks, the graph's shape is worth
a second look.

## Phase 3 — Owns

Every task declares the exact files it may create or edit: real paths or
directory prefixes. A glob swallows a sibling's files and surfaces at 3am as a
conflict rather than a refusal.

The loader refuses two tasks sharing a path with no edge between them, and the
scheduler refuses to co-run them. The shared files — app entry point, asset
catalog, DI container, route table — are the hard part. Two ways out, in order:
**generate the file** so nothing hand-edits it, or **give one task sole
ownership** and hang the registrations off it as dependencies. Spreading one
file across ten `owns` lists is correct and slow; prefer removing the file from
the problem.

A root-level composition file — the panel/app root view, `AppDelegate`, the
composition root — is not an occasional collision, it is a standing one: every
wiring task for the rest of the product wants a line in it. quillnote put
`App/Panel/PanelRootView.swift` in five tasks' `owns` across three waves, and
the cost landed on the *late* arrival: a closeout-authored follow-up task named
it with no edges to the prior owners, `afk wave validate` refused the whole
directory, and the driver's own cut just silently dropped the task instead.
Two rules fall out: pick the sole-owner-or-generated shape for these files at
authoring time, before wave one; and any task authored mid-run that touches one
must carry `blocked_by` on **every prior owner** of its files, done or not — a
satisfied edge is free, a missing one is a task that vanishes from the cut with
no error.

A task authored mid-run is invisible to the running driver either way: the
graph is frozen at launch, so relaunch the wave to pick it up (quillnote
task-50 sat unrun for two waves waiting to be noticed).

The fixture is a standing collision of the same kind: one task adds or
extends it, and the screen tasks that render it hang off that task.

**Done when** every `owns` path exists or is created by that task, and no pair
shares a path without an edge.

## Phase 4 — Write the files

`tasks/tasks-todo/task-NN-<slug>.md`, numbered in dependency order. The
frontmatter keys are a closed set — an unknown key refuses the directory.

```
id           task-NN-<slug>, matching the filename
blocked_by   [] or ids in this directory
owns         exact paths or directory prefixes
status       ready-for-agent
checks       optional; absent means the project default. Name an expensive
             gate (simulator, browser suite) only on tasks that need it.
gate         optional; before | after
```

`gate: before` marks the run's one legitimate human pause: a task whose
spec rests on a default only the user can ratify (pricing, trial policy,
anything on their decide-list) or on a capability no lane holds (secrets,
hardware). Write the defaults into the task body so releasing the gate is
a one-word ratify — a gated task with an unstated default puts a design
session between the user and their sleep. Everything else runs ungated;
`gate: after` lets the task run and holds only the close. Release is an
act, not a record: drop the gate line (or `afk run --task=`) and re-run.

There is no `model` or `effort` key: the executor is chosen per role in the
runner config.

The body is `/to-tickets`'s issue template with **Blocked by** and **Status**
moved into frontmatter, plus three sections it has no use for:

```markdown
# task-NN: <title>

## What to build
<the end-to-end behaviour this makes work, from the user's side>

## Read first
- `AGENTS.md`, `CONTEXT.md` — glossary terms exactly
- `tasks/GOAL.md`
- <the one reference this task copies rather than reinvents>
- <the platform cookbook, when one exists>. A cookbook written the day
  before and not named here is a cookbook no lane reads: quillnote had
  one warning about live clocks in previews and about a diff that cannot
  fail, and shipped both defects anyway.

## Steps
1. <imperative, naming a file from `owns`>
2. Run the acceptance commands.

## Acceptance criteria
- [ ] `<command>` exits 0. Paste the output.
- [ ] `<test>` fails on HEAD before, passes after. Show both runs.

## Out of scope
- Paths outside `owns`.
- <the neighbouring thing a small model would wrongly pull in>
- Unfinishable scope: write a new `task-NN-<slug>.md` for the remainder first.
```

Two things stay out of the file. **Authoring rules** live in this skill — a
commentary block at the top of every ticket is one document copied a hundred
times. **Lifecycle** belongs to the runner, which moves the file when the work
integrates; a ticket that tells the agent to mark itself done is an agent
marking its own homework.

**Done when** every approved slice has a file and nothing else is in
`tasks-todo/`.

## Phase 5 — Validate

```bash
afk wave validate tasks/
```

Fix what it names, run it again. It refuses unknown keys, `blocked_by` pointing
at nothing, impossible `owns` paths, ownership collisions without an edge, and
cycles — which is what makes every rule above mechanical rather than
aspirational. Read the level widths it prints: a level of thirty is a night of
contention.

**Done when** it exits 0.

## Phase 6 — Hand back

Commit `GOAL.md` and `tasks-todo/` together — the directory and the scaffold it
was written against belong in one history.

Gated tasks are hand-back's first item, before any count: name each
`gate: before` task and **grill its defaults now**, one question per
default, while the user is at the keyboard — a ruling taken here releases
the gate before the run; deferred, it parks the work behind a pause nobody
is awake to lift. Drop the gate line the moment a default is ratified and
re-validate. A gate survives hand-back only when no answer the user could
give tonight releases it (unminted secrets, absent hardware), and then the
report names what the morning needs.

Runtime is config, not a flag. `afk wave run` takes no `--runtime`; each wave
is an `afk auto` run that resolves `agent.runtime` from `.afk-setup/config.yaml`,
defaulting to direct — headless lanes, no Herdr panes. For Herdr visibility,
commit `agent: { runtime: herdr }` to the base branch **before launch**; the
wave worktrees are cut from base, so an uncommitted or later config never
reaches them. The dashboard runs either way — its port is in the launch
output (`AUTO: dashboard started at ...`); name it in the hand-back report.

Report the task count, the level widths, the checks the run will gate on, and
the launch command. Offer `/coduo-flow` when the graph is large enough to earn
a map; a hundred tasks is past that line.
