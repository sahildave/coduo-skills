---
name: coduo-epic
description: |
  Turn the current conversation into ONE GitHub epic issue carrying the PRD and
  a fenced `afk:` spec block (`version`, `branch`, optional `max_parallel`).
  Wraps `/to-spec`. Use when starting a feature that will later be run
  unattended by the AFK runner, when asked to write the epic issue, or when
  scoping one of several epics that will run at the same time. Children come
  later, from `coduo-tickets`.
disable-model-invocation: false
---

# Coduo epic

The epic issue **is** the spec. There is no local copy — `afk epic <n>` fetches
the issue at start and re-fetches on restart, so anything not in the issue body
does not exist as far as the runner is concerned.

Three sources of truth, none overlapping. This skill writes only the first:

```
GitHub epic + children   WHAT to build, and in what order   (spec)
.afk-setup/config.yaml   HOW this stack is verified         (stack)
.afk/state.json          WHAT is happening right now        (runtime)
```

You produce **one issue**. Not the children — `coduo-tickets` cuts those, and it
is a separate invocation with a separate approval from the user.

## Phase 0 — Synthesize the PRD

Run `/to-spec`. It has the spec template, the seam-selection step, and the
domain-glossary and ADR rules; do not paraphrase them here and do not
reimplement it.

**Run this phase under a strong model.** The PRD is real synthesis and its
quality tracks model strength, so run `/to-spec` under Fable 5 or Opus, never
Sonnet or Haiku. If you delegate it to a sub-agent, set that agent's `model` to
`fable` (Fable 5, the default) or `opus` — tier aliases, not version strings;
there is no `fable-5` or `opus-5`. The cheap-model default produced weaker
epics. Only the mechanical `gh` filing in Phases 1–2 is exempt, and even there
prefer the strong model over saving cost.

Two overrides on it, both because the runner reads GitHub and nothing else:

- **The tracker is GitHub, via `gh`.** `/to-spec` publishes to whatever
  `/setup-matt-pocock-skills` configured, and local-file mode produces a spec
  with no issue number. An epic with no number has no branch name and no task
  ids. If the repo is configured for local files, say so and switch to `gh` for
  this epic rather than emitting a file.
- **Stop before it publishes.** You need the body text, and you need to create
  the issue yourself in Phase 1 so you hold the number.

Confirm the seams with the user as `/to-spec` requires. That conversation is the
cheapest place this epic will ever be corrected.

**Scope to a polished MVP.** Each user story and requirement earns its place as a
main path a normal user walks, a launch blocker or a real bug, and those are
written to a finished standard. Hardening, refactors, premature optimization and
rare edge cases (wifi toggled mid-flow, Reduce Motion, force quit, odd account
states) stay out unless the user named them: at most a line in Out of Scope,
never a requirement, so they never reach `coduo-tickets`. The test for each line
is "will a normal user hit this before launch?" The user corrected
over-engineering about 90 times in Aug–Oct 2026; the PRD is where it is cheapest
to stop.

Seams are test boundaries, not ticket boundaries. Any ticket shape you show
beside them (a proposed-epic table, a slice list in the PRD) is cut by
`coduo-tickets`' "Fold to the fewest baseline runs" rule before the user sees
it: one builder ticket unless a split reason holds, and the baseline-run count
stated.

**A mechanical sweep carries its count.** When the PRD moves a literal, a path
or a name across the repo, count it before writing anything about how it
splits: `git grep -l '<literal>' -- src e2e | wc -l`, and the recorded
baselines that render it. Put both numbers in Further Notes; `coduo-tickets`
sizes lanes from them. Harbour #429 wrote "about 136 files" from memory, and
the lane wrote 316.

**A user-facing epic carries an `## Outcome` section.** The one number the
epic should move; where that number is read today (a query on a named table
and column, a GitHub API count, or "nowhere"); the date it is checked; and one
line on what must not get worse. No baseline figure unless it comes from a
query you ran and paste beside it. A total is not a rate: a table with no
creation timestamp cannot give "per week". If the number is read nowhere, the
first child ticket adds the read, with a criterion a lane can check (a row
written, a test asserting it). The measurement ships in the epic, not after it.

**One-way doors get a human gate.** A price, a schema migration, a public URL
or API shape, a file format the product writes into a user's repo: name each
in Implementation Decisions as "one-way door", so `coduo-tickets` cuts it a
`gate: before` ticket and the user releases it. Everything else is a two-way
door and gets no ceremony.

**Name every external service with no faithful local stand-in.** For each one
the epic depends on, Testing Decisions names the service and the probe that
will run against the real service before the epic closes, so `coduo-tickets`
can give the probe a home (a lane criterion, or a `gate` ticket when it needs
real credentials). A fake passes whatever its author assumed; without a named
probe the first real call happens after close, in the user's hands.

**Done when** you have a PRD body you would be willing to hand an agent, every
requirement passes the MVP test above, and the user has agreed to the seams.

## Phase 1 — Create the issue, get the number

```bash
gh issue create --title "<epic title>" --body-file /tmp/epic-body.md \
  --label ready-for-agent
```

Nothing about the `afk:` block yet. The block cannot be written in this call,
because the value it must carry does not exist until this call returns.

**Done when** `gh` has printed an issue URL and you have read the number out of
it.

## Phase 2 — Write the `afk:` block onto the epic

The branch convention is `feat/<epic-number>-<slug>` — epic **203** titled
"Stripe subscriptions" gives `feat/203-stripe-subscriptions`. The number is in
the branch name on purpose: it makes every worktree path, lane branch and
`.afk/runs/<id>` unique per repo forever, which the old `001`/`002` scheme
could not do across runs.

That is why creation and block-writing are two steps and not one. Do not invent
the number, do not guess the next one from the issue list, and do not write the
branch line before the issue exists.

Slug: kebab-case, from the title, three or four words, no ticket words
("epic", "feature", "implement").

Append exactly this to the epic body — a fenced YAML block, `afk:` at the root:

````markdown
## AFK spec

```yaml
afk:
  version: 1
  branch: feat/203-stripe-subscriptions
  max_parallel: 3
```
````

`gh issue edit <n> --body-file` replaces the whole body, so build the new body
from the old one rather than from memory:

````bash
gh issue view 203 --json body -q .body > /tmp/epic-203.md
cat >> /tmp/epic-203.md <<'EOF'

## AFK spec

```yaml
afk:
  version: 1
  branch: feat/203-stripe-subscriptions
````

EOF
gh issue edit 203 --body-file /tmp/epic-203.md
gh issue view 203 --json body -q .body | tail -20 # read it back

```

**Done when** the block is on the issue, the branch line names the epic's own
number, and you have read the body back and seen the fence intact.

## What goes in the block, and what must not

Exactly three keys at this stage:

| Key | Required | Value |
|---|---|---|
| `version` | yes | `1`. Literal. |
| `branch` | yes | `feat/<epic-number>-<slug>`. Must not already exist with divergent history. |
| `max_parallel` | no | Integer. Only when this epic needs a **lower** cap than `.afk-setup/config.yaml`'s `maxParallel`. Omit otherwise. |

**No `tasks:` block. Not even an empty one.** The child issues do not exist yet,
so they have no numbers, and the task key in the `tasks:` block *is* the child
issue number. An agent that writes placeholder ids here — `001`, `T1`, `TBD`,
a guessed `204` — poisons the entire run: the validator either rejects the epic
outright or, worse, resolves a guessed number to some unrelated open issue and
schedules a lane against a ticket nobody wrote. `coduo-tickets` adds `tasks:`
after the children are pushed and their numbers are real.

**No `checks:`.** Not at epic level, not at all. `.afk-setup/config.yaml` carries
`defaultChecks`; duplicating it onto an issue buys nothing and rots
independently.

**No title, acceptance criteria, or implementation notes in the block.** They
live in the issue body as prose and reach the agent by issue reference. The
block is the graph and nothing else.

**Unknown keys are a hard validation error**, not a key the runner ignores.
Adding `owner:` or `priority:` because it seemed useful fails `afk validate`.

## Concurrent epics — declare the file surface

Several epics can run at once, in separate checkouts against the same base. No
runner can see another runner: per-task scope is advisory and **unchecked across
lanes**, so an overlap between two live epics surfaces as a merge conflict at the
end of the night, never as a refusal to schedule. Nothing catches it but this
step.

Ask the user which other epics are live, or about to be. When any is, write a
**file surface** into the epic body — the paths this epic owns, and the paths its
siblings own:

```markdown
## File surface

Owns: `src/services/mutations.ts`, `src/services/query-keys.ts`, `src/services/milestones.ts`
Off-limits (epic #401): `src/github/client.ts`, `src/features/onboarding/**`
Off-limits (epic #402): `src/services/catalogues.ts`, `src/github/queries/items.ts`
```

Read the siblings' own surfaces off their issues rather than asking the user to
recite them, and say plainly if a sibling has none — an epic with no declared
surface cannot be planned around, and that is a conversation to have now rather
than at 3am.

This is prose in the epic body, not a key in the `afk:` block. It exists so
`coduo-tickets` can turn it into each child's `## Allowed paths` and
`## Prohibited` sections, which is the only form a lane ever reads.

**Done when** either the user has confirmed this epic runs alone, or the body
carries a file surface whose `Owns` list is disjoint from every sibling's.

## Phase 3 — Point the flow map at the epic

Only when `docs/flow/` exists in this repo. Skip the whole phase otherwise; it
is not a prerequisite for anything.

A card on the map is a durable thing — a screen, a system, a rule — and an epic
is a batch of work that lands against it. So the epic **appends** to the cards it
touches; it does not own them.

- **The work extends something already on the map** (a field on Settings, a
  state added to a screen): append this epic to that card's `epics` list. Do
  not overwrite an epic already there, and do not fear a card that already
  shipped — a closed epic plus your new open one is a built card with work in
  flight, which the map draws correctly (green bar, both epics in the panel).
- **The work is a genuinely new feature or screen** with no card yet: it needs
  a new note first. That is a `coduo-flow` job (Phase 2), not this skill's — 
  author the note, place it on the timeline, then set its `epics`. Do not bolt
  the new epic onto an unrelated card because it was the nearest one.

```yaml
epics: [203]        # in the card's frontmatter; append, never overwrite
```

Set it on **every** card the epic touches. Then resolve the `coduo-flow` skill
directory and refresh:

```bash
python3 <coduo-flow>/scripts/sync_epics.py docs/flow/<name> \
  && python3 <coduo-flow>/scripts/check_flow.py docs/flow/<name> \
  && python3 <coduo-flow>/scripts/build_flow.py docs/flow/<name>
```

Until this runs, a card with an empty `epics` list draws hatched — "no epic
filed yet" — which is a lie the moment your epic exists. The two skills share one
repo and no state, so nothing else keeps them in step.

**Done when** every card the epic touches names it in `epics`, the sync reports
it, and the checker no longer lists those cards among the ones with no epic. If
the work needed a brand-new card, that card exists and sits on the timeline.

## Before you hand it over

- `.afk-setup/config.yaml` exists in the repo, with `defaultChecks` and
  `worktreeSetup`. Without it, every lane will fail its gate for reasons no
  ticket can fix. If the repo still has a `planning/manifest.json`, say so —
  that is the pre-split layout and the epic will not run against it.
- The branch does not already exist: `git rev-parse --verify feat/203-...`
  should fail. A branch with divergent history is a deterministic validation
  failure at run time.
- The epic is **inert until `coduo-tickets` writes `tasks:`**. Say this to the
  user in your report, with the next command. An epic that looks finished and
  does nothing is the single most common way this workflow goes wrong.
```
