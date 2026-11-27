---
name: coduo-tickets
description: "Cut an AFK epic into child GitHub issues, write the `tasks:` block onto the epic's `afk:` spec from their real issue numbers, check it with `afk validate`, and render the dependency diagram onto the epic. Wraps `/to-tickets` and `/beautiful-dag`. Use after `coduo-epic`, or whenever an epic needs its children and its `tasks:` block."
disable-model-invocation: false
---

# Coduo tickets

Five steps, in this order:

1. Read the epic.
2. Slice the work and create the children (`/to-tickets`).
3. Read the dependency map back off GitHub.
4. Write `tasks:` onto the epic and pass `afk validate`.
5. Render the diagram from `tasks:` (`/beautiful-dag`).

The task key in `tasks:` is the child's issue number, so step 4 waits until
every child exists. Until it is written, `afk validate` refuses the epic with
"`tasks` is required".

## 1. Read the epic

```bash
gh issue view <epic> --json number,title,body
```

You need the `afk:` block `coduo-epic` wrote (`version: 1`, `branch`), the
numbered `## User Stories`, any `## File surface`, the one-way doors, and the
probes named in Testing Decisions. If there is no `afk:` block, stop and run
`coduo-epic` on the issue first.

## 2. Slice and create the children

Run `/to-tickets` on Opus; slicing and writing criteria are synthesis. Ask the
user before using Fable for it. Keep its approval loop, with these overrides:

- **The tracker is GitHub.** Local-file mode numbers tickets `01`, `02`, which
  cannot become task ids.
- **Every child is a sub-issue of the epic.** The validator checks that each
  task key is an open sub-issue (`no_child_issue`, `child_closed`):

  ```bash
  gh issue create --title "..." --body-file "$TMPDIR/t1.md" \
    --label ready-for-agent --parent <epic>
  ```

- **Publish blockers first**, so each "Blocked by" names real numbers.
- **Folding beats `/to-tickets`' narrow slices.** See below.
- **File paths belong in the ticket** (`## Allowed paths`, `## Prohibited`),
  against `/to-tickets`' advice.

### Fold to the fewest baseline runs

Every builder ticket costs a baseline run (the repo's full `baselineChecks`
at integration), a lane dispatch, a serialized merge and a report: minutes to
tens of minutes each, however small the change. The ticket count is the
epic's wall clock.

Start from one builder ticket for the whole epic. Split only for one of three
reasons:

1. **Different executor.** Work only a human can do or accept becomes a
   `gate` ticket. Each one-way door is `gate: before`, because by `after` the
   lane has crossed it. A `gate: after` ticket dispatches no builder and
   costs no baseline run.
2. **Different release point.** Part of the work waits on something outside
   this epic (another epic's merge, a human provisioning step) and the rest
   should land without it.
3. **Too big for one lane.** Measure, do not guess:
   - Files: `git grep -l '<literal>' -- src e2e | wc -l`, plus every recorded
     baseline whose page renders it.
   - Clock: write time plus three passes of the lane's gate (`defaultChecks`
     plus any suite a criterion names) must fit in half of `agent.timeoutMs`.
     Time one pass on the base.

   Over budget, split so each ticket leaves the suite green on its own: the
   smallest behaviour change with the baselines it moves first, then the
   behaviour-neutral sweeps, then the guard.

Everything else folds: small tickets, tickets that share files, per-layer
splits, a ticket that exists only to go second.

The proposal the user approves has a **Why separate** column naming reason
1, 2 or 3 for every ticket past the first, and the line
`Baseline runs: N (M before folding)`.

### Keep the graph shallow

A failed task strands everything that depends on it. After folding, ask of
each edge: does this ticket fail without its dependency, or is it only nicer
second? Delete the second kind. Depth 2 is the target; depth 3 needs a
reason you can say ("205 needs 204's table"), and `afk validate` warns at 3.
When the epic says two tickets share something, one depth-0 ticket owns the
shared part; a lane cannot see other lanes and will copy instead.

### What each child carries

Only product work becomes a ticket: user-facing behaviour, a real bug, a
launch blocker. Drop hardening, refactors and unrequested enhancements, and
list each with one line in the report so the user can overrule you.

Body template:

```markdown
<What the user gets, and why. Two or three sentences.>

## User stories

Carries 1–3, 7 from epic #203.

## Acceptance criteria

- <Something a lane can check, see references/criteria.md>

## Journeys

Changes ACT-01. Adds a row for the weekly goal.

## Allowed paths

`src/billing/checkout.ts`, `src/billing/__tests__/checkout.test.ts`

## Prohibited

`src/github/client.ts` (epic #401)

## Blocked by

#204
```

- **`## User stories`** cites the epic's story numbers (numbers, ranges with
  a hyphen or en dash). Every story must be cited by some child
  (`story_not_cited`), and a cited number must exist (`story_not_in_epic`).
- **`## Acceptance criteria`** (or a `**Done when**` line) is required
  (`no_acceptance_criteria`). Read `references/criteria.md` before writing
  them. `afk validate` refuses several shapes outright.
- **`## Journeys`** names the feature-map IDs the child changes, and says
  "adds a row" for a new journey. Only where the repo has
  `docs/feature-map.md`; leave it out for a child with no behaviour change.
  The verifier checks these rows.
- **Scope reaches a lane only through its own body.** The `afk:` block has
  no paths, and prose on the epic reaches no builder.
  - A file two children both write makes them one ticket, unless a split
    reason holds; then it is one edge, with one owner named.
  - When the epic has a `## File surface`, every child repeats the siblings'
    paths in its `## Prohibited`.
  - Find a contract's consumers by grepping the API, not from the spec's
    list. A consumer on another platform means the lane runs that platform's
    check too.
  - A ticket may not prohibit the file its own change lands in.
- **Put worked-out code in the ticket**, so the lane applies it instead of
  rediscovering it, but only code you ran. A lane applies a snippet as
  written. If it was not run, state the outcome and leave the mechanism to
  the lane.
- **A ticket must change a source file.** The runner drops bookkeeping and
  protected files from a change set, and a task with no source change left
  is `blocked`, with its dependants. A spike or audit writes its finding to a
  path in the tree (`docs/spikes/<slug>.md`) named in `## Allowed paths`, or
  becomes `gate: before`.
- **A `gate: after` ticket carries its own checklist**, step by step, in the
  form the human walks, each step checked against the code. No builder runs
  it. If a failed step is fixed on the epic branch outside the runner, the
  checklist says to re-run `afk epic <n>` without `--accept` first, then
  accept.
- **Probes.** For each external service with no faithful local stand-in, a
  criterion names the probe against the real service. If it needs real
  credentials, it goes on a gate ticket.

**Done when** the user approved a proposal with its baseline-run count,
every child exists as an open sub-issue with the sections above, and every
epic story is cited.

## 3. Read the map back

The user may have edited tickets during approval, so read them back with the
same query the runner uses:

```bash
gh api graphql -f query='{repository(owner:"<owner>",name:"<repo>"){issue(number:<epic>){subIssues(first:50){nodes{number state body}}}}}'
```

Turn each "Blocked by" into `depends_on`. Every entry must be a task in the
block (a dependency outside the epic is `dangling_dependency`), with no
cycles.

## 4. Write `tasks:` and validate

`gh issue edit --body-file` replaces the whole body. Read the live body, add
`tasks:` inside the existing fence, keep every other byte, write it back.
This fence and the diagram in step 5 are the only edits to the parent issue,
against `/to-tickets`' "do not modify the parent".

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
      checks: [npm run lint:check, npm test]
    207:
      depends_on: [205, 206]
      gate: after
```

| Key | Rule |
|---|---|
| task key | The child issue number. Not a slug, not `001`. |
| `depends_on` | List of issue numbers in this block. Write `[]` for a root. |
| `gate` | Optional. `before`: a human releases the task. `after`: no builder; the human's `afk epic <n> --accept=<id>` is the verdict. |
| `checks` | Optional. Replaces `defaultChecks` for this lane, so list every default it still needs. Leave it out unless the lane needs a narrower gate. |

Two optional top-level keys:

- `waivers:` maps a task id to why it may cross a one-way door without
  `gate: before`, at least 10 characters. A task whose paths hit a door in
  `oneWayDoors:` needs one or the other (`one_way_door_ungated`).
- `stops:` records the answer for each human stop: `park`, `last`, or
  `"delegate: <condition>"` (quoted, condition at least 10 characters). It
  is usually written when the run is planned (`coduo-afk`,
  `coduo-chief-of-staff`). Write it here only when the user has already
  answered.

Any other key, at either level, is `unknown_key`.

Then run:

```bash
node <runner>/afk.mjs validate <epic>
```

`<runner>` is the coduo-afk checkout. To check a block before writing it,
add `--epic-body=<path>`; it still reads the real sub-issues. Fix every
error and read every warning. **Done when** it exits 0 and you have the
depth and blast radius it prints.

## 5. Render the diagram

Run `/beautiful-dag` over the `tasks:` block (not native issue dependencies)
and put the diagram in the epic body. When the graph changes, edit `tasks:`
and re-render; never edit the picture alone. A `gate: before` task is a real
task in its phase, not an external gate.

If `docs/flow/` exists and a card lists this epic, run `coduo-flow`'s
`sync_epics.py`, `check_flow.py` and `build_flow.py` so the card shows the
new children.

## Report

- each child with its `depends_on` and split reason
- baseline runs, before and after folding
- depth and blast radius from `afk validate`, and its exit status
- work dropped as not product work, one line each
- anything you sliced against the user's stated shape, and why
