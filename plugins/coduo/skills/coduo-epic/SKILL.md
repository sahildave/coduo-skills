---
name: coduo-epic
description: "Turn the current conversation into one GitHub epic issue that carries the PRD and a fenced `afk:` spec block. Wraps `/to-spec`. Use when starting a feature the AFK runner will later run unattended, when asked to write the epic issue, or when scoping one of several epics that will run at the same time. The child tickets come later, from `coduo-tickets`."
disable-model-invocation: false
---

# Coduo epic

The epic issue is the spec. `afk epic <n>` fetches the issue at start and
again on restart, so anything not in the issue body does not exist for the
runner. This skill writes one issue: the PRD and an `afk:` block with no
tasks. `coduo-tickets` cuts the children later, with its own approval from
the user.

## Before you start

- The repo has `.afk-setup/config.yaml` with `defaultChecks` and
  `worktreeSetup`. Without it every lane fails its gate for reasons no
  ticket can fix. If it is missing, stop and say so.
- **A UI epic names its prototype** (a path or branch) that the tickets build
  against. With none, build one first with `coduo-product-prototype`; the
  ruling is `coduo-swiftui-factory`
  `docs/starter-kit/decisions/prototypes-run-on-the-real-shell.md`.
- **Ask which other epics are live** or about to start. Two epics running at
  once in separate checkouts cannot see each other, so an overlap shows up
  only as a merge conflict at the end. If any sibling is live, read its
  `## File surface` off its issue and write this epic's (see below). If a
  sibling has none, tell the user now.

## Phase 0: write the PRD

Run `/to-spec` on Opus. The PRD is synthesis and its quality follows the
model. Ask the user before using Fable for it.

Overrides to `/to-spec`, because the runner reads GitHub and nothing else:

- **The tracker is GitHub, through `gh`.** An epic with no issue number has
  no branch name. If the repo is set up for local-file specs, say so and use
  `gh` for this epic.
- **Stop before it publishes.** You create the issue yourself in Phase 1 so
  you hold the number.
- **The MVP rule beats its story count.** Each user story and requirement is
  a main path a normal user walks, a launch blocker or a real bug, written to
  a finished standard. Hardening, refactors, premature optimization and rare
  edge cases (wifi toggled mid-flow, Reduce Motion, force quit) get at most a
  line in Out of Scope, unless the user named them. Ask of each line: will a
  normal user hit this before launch? Every numbered story under
  `## User Stories` must be cited by a child ticket later, or `afk validate`
  refuses the epic (`story_not_cited`), so a story you would not build is a
  story to cut.
- **File paths are allowed where this skill asks for them** (the file
  surface, sweep counts, the prototype), against `/to-spec`'s "no paths".

Confirm the seams with the user as `/to-spec` asks. It is the cheapest place
this epic will ever be corrected. Seams are test boundaries, not tickets;
`coduo-tickets` decides how few tickets the work needs.

Add these to the PRD where they apply:

- **A mechanical sweep carries its count.** When the work moves a literal, a
  path or a name across the repo, count it: `git grep -l '<literal>' -- src
  e2e | wc -l`, plus the recorded baselines that render it. Put both numbers
  in Further Notes; `coduo-tickets` sizes lanes from them.
- **A user-facing epic has an `## Outcome` section**: the one number it
  should move, where that number is read today (a query on a named table and
  column, a GitHub API count, or "nowhere"), the date it is checked, and one
  line on what must not get worse. Give a baseline only from a query you ran,
  pasted beside it. If the number is read nowhere, the first child adds the
  read.
- **One-way doors.** A price, a schema migration, a public URL or API shape,
  a file format the product writes into a user's repo. Name each in
  Implementation Decisions as "one-way door". The runner gates them by path,
  from `oneWayDoors:` in `.afk-setup/config.yaml`: a child whose paths hit a
  door must be `gate: before` or carry a `waivers:` reason, or validation
  fails. A door with no glob there is gated by nothing, so ask the user now
  to add one; `.afk-setup/` is theirs to edit. Either way, `coduo-tickets`
  makes the door's ticket `gate: before`.
- **External services with no faithful local stand-in.** For each, Testing
  Decisions names the service and the probe that runs against the real one
  before the epic closes, so `coduo-tickets` can give it a home.

**Done when** the user has agreed to the seams and every requirement passes
the MVP test.

## Phase 1: create the issue

```bash
gh issue create --title "<epic title>" --body-file "$TMPDIR/epic-body.md" \
  --label ready-for-agent
```

`gh` prints the issue URL; the number is its last segment. Do not guess it
from the issue list, because the branch name in Phase 2 is built from it.

## Phase 2: write the `afk:` block

The branch is `feat/<number>-<slug>`: epic 203 titled "Stripe subscriptions"
gives `feat/203-stripe-subscriptions`. The slug is three or four kebab-case
words from the title, without "epic", "feature" or "implement". Check the
branch is new: `git rev-parse --verify feat/203-stripe-subscriptions` should
fail. An existing branch with divergent history fails validation.

`gh issue edit --body-file` replaces the whole body, so build the new body
from the live one:

~~~bash
gh issue view 203 --json body -q .body > "$TMPDIR/epic-203.md"
cat >> "$TMPDIR/epic-203.md" <<'EOF'

## AFK spec

```yaml
afk:
  version: 1
  branch: feat/203-stripe-subscriptions
```
EOF
gh issue edit 203 --body-file "$TMPDIR/epic-203.md"
gh issue view 203 --json body -q .body | tail -12
~~~

The block takes three keys at this stage:

`version` and `branch` as above, and optionally `max_parallel`, an integer
from 1 to 32, only when this epic needs a lower cap than `maxParallel` in the
config.

Leave out `tasks:`. Each task key is a child issue number, and the children
do not exist yet; a guessed number can match an unrelated open issue and run
a lane against it. Per-task `checks:` are `coduo-tickets`' call. Titles, criteria and notes stay in the body as prose.
Any other key fails validation as `unknown_key`.

**Done when** the block is on the issue, the branch names the epic's own
number, and the body you read back shows the fence intact.

## File surface

Only when a sibling epic is live. Prose in the body, not a key in the block:

```markdown
## File surface

Owns: `src/services/mutations.ts`, `src/services/query-keys.ts`
Off-limits (epic #401): `src/github/client.ts`, `src/features/onboarding/**`
```

`coduo-tickets` copies it into each child's `## Allowed paths` and
`## Prohibited`, the only sections a lane reads. **Done when** the user has
confirmed the epic runs alone, or its `Owns` list is disjoint from every
sibling's.

## Flow map

Only when `docs/flow/` exists. Append the epic number to the `epics:` list
of every card the work touches, and run `coduo-flow`'s `sync_epics.py`,
`check_flow.py` and `build_flow.py` on the map. A new screen with no card is
a `coduo-flow` job first.

## Report

Give the epic number and branch, the one-way doors, and the next step:
`afk validate` refuses this epic ("`tasks` is required") until
`coduo-tickets <number>` writes the `tasks:` block. Say so in those words,
because the epic looks finished on GitHub before it can run.
