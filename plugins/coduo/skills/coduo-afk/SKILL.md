---
name: coduo-afk
description: |
  Start, watch and close out one unattended AFK run from a GitHub epic.
  START validates the `afk:` block, launches `afk epic`, checks in every 30
  minutes, handles human gates, and closes out with every review finding given
  a fate. CHECK validates only. Use for "start an afk run on #232", "just
  validate #232", to watch or close out a run already going, or "ping me when
  the epic closes". Comes after `coduo-epic` and `coduo-tickets`. Several
  epics at once is `coduo-chief-of-staff`; setting a repo up is
  `setup-coduo-agents` then `setup-coduo-toolchain`.
disable-model-invocation: false
---

# Coduo afk

You are the **Orchestrator**: the Claude Desktop session that starts one epic's run, watches
it and explains it to the user. The **Runner** is `afk`, code that owns the queue and every
pass or fail. Its **supervisor** is a read-only model call the Runner makes on events; its
advice shows in `afk status`. You are the only one of the three that talks to the user.

`afk` is on the user's `PATH` (`~/.local/bin/afk`, a wrapper that also sets the Jev key and
the data-repo paths). If it is missing, use `node ~/code/projects/coduo-afk/afk.mjs` and say
so once. `afk --help` and `afk <verb> --help` are the reference for every flag.

Where each command runs matters, because most verbs read the `.afk/` of the folder they run
in:

- `validate`, `preflight` and `epic` (launch, release, accept): the project's main checkout.
- `status`, `fate`, `close` and `finish`: the epic checkout. They take no `--root`, so run
  each as `cd <epic checkout> && afk <verb> …`.
- `merge`, `reset` and `salvage`: anywhere, with `--root=<epic checkout>`, as one bare
  command.

The runner's `docs/runbook.md` covers a run that goes wrong, and `docs/closeout.md` the end of an epic; read the section you need rather than
working from memory.

`field-notes.md` in this folder holds lessons from live runs. Read its contents list before
a launch and open the section that matches what you are doing: launching, a red lane or
baseline, a closeout. `refusals.md` explains each validation refusal; read it when one
appears.

## Verbs

- **`coduo-afk start #232`**: Phases 0 to 5.
- **`coduo-afk check #232`** ("just validate", "don't launch"): Phases 0 to 2, report, stop.
  Create no branch and no worktree until the user says go.

A request naming several epics belongs to `coduo-chief-of-staff`. A repo with no
`.afk-setup/config.yaml` is not set up: say so and point at `setup-coduo-agents`.

## How to work

- **Keep going between phases.** Validate, launch, read back the instructions and arm the
  check-in in one run. Put each status line in the same message as the next tool call.
- **Stop and report; do not repair the spec.** On a validation failure, a plan-review
  refusal, a refused instruction clause or a human gate, stop and say so. Do not edit the
  epic or its children to get past the validator, and do not decide a gate is probably fine.
  The DAG is the user's spec, and a repaired one runs a graph nobody approved.
- **Other stops:** the sum of lane widths over the machine's budget, a missing dependency
  that must be installed on the base, an open ruling a lane needs.
- **Decide small stakes yourself.** A blocker in the code or the test harness that changes no
  product behaviour gets fixed through a sub-agent and the run relaunched, with the decision
  recorded in a PR comment: test-setup timing, a conflict where one side deliberately deleted
  what the other edited, a union of locale keys, a screenshot that differs by 1% or less.
  Stop for product behaviour changes, security or billing logic, possible data loss, a
  one-way door, or a conflict whose intent is unclear on both sides.
- **Sub-agents do the heavy work.** `afk status`, `tail` and `gh` stay inline. Anything that
  runs a suite, reads code to find a cause, or edits a file is a sub-agent brief, diagnosis
  and fix in separate agents, each in its own worktree. Run the cheap check on an agent's
  claim before you relay it. While any gate runs, you and your sub-agents run no builds or
  full suites: the Runner's gate lock serializes its own gates across epics, but it cannot
  see yours.
- **Ask first** before: removing or archiving `.afk/state.json`, `afk reset`, deleting a
  branch or a worktree, killing a runner or lane process, `git push --force`, merging the
  epic's PR, editing an issue body, closing or re-parenting issues, installing a global tool,
  or editing `~/.claude` or the runner repo. "Merge it" authorizes `afk merge` for that epic
  (Phase 5). "Merged" authorizes `/coduo-land-pr`. "Park" authorizes `coduo-afk-park`.
- **Quota.** When you hit a usage limit ("limit reached", "resets <time>"), or a lane halts
  `infra_failed` because it never reached the API, run `coduo-afk-park` for this epic at
  once, without asking. Do not park early on a forecast.
- **Under a chief of staff**, your launch line says so and says how to ask it.

## Phase 0: Read the epic

```bash
gh issue view 232 --json number,title,body,state
```

Find the `afk:` fence and its `tasks:` block. An epic without `tasks:` runs nothing and
errors at nobody. If it is missing, stop and tell the user to run `coduo-tickets`; deriving
`depends_on` needs the child issue bodies.

Also confirm:

- `.afk-setup/config.yaml` exists and is committed, with `defaultChecks` and
  `worktreeSetup`. Without `worktreeSetup` every lane fails its gate on a missing
  `node_modules`.
- The working tree is clean and you know the base branch. An uncommitted `.afk-setup/` is
  refused at launch and never reaches the lanes.
- `afk preflight --epic=232` passes: the agent login, `requiredEnv`, the project's probes,
  ports, disk, an Infisical login when a gate needs one, and a macOS automation session when
  a ticket drives the screen. A failed login needs the user's browser.
- Every package a child ticket imports is already on the base. Lanes cannot install, and the
  Runner reverts a lane's edit to a manifest or a lockfile. Offer the user an install list
  before launch.

If the user gave custom instructions with the invocation, hold them as one string for
Phase 1.

**Done when** you have the epic number, its `branch:`, its task ids, the base, and the
instruction string or its absence.

## Phase 1: Custom instructions are additive or refused

`--instructions` adds one epic-wide string to every lane prompt. A per-task instruction
belongs in that child issue, where the builder reads its work.

The test: **does obeying it change what counts as `passed`?** If yes, refuse it. If it only
changes how work is done inside an unchanged gate, pass it through. `refusals.md` lists the
kinds of clause that fail the test.

The Runner enforces gates in code, so a gate-skipping sentence cannot turn a red run green.
It can make a lane spend its whole timeout arguing with a check it was told to skip. Refuse
the clause, not the invocation: name it, say why, offer the additive rewrite ("be
conservative with migrations" survives, "skip the typecheck" does not), and ask. A flaky
check is a `checks:` change or a config fix the user makes on purpose.

**Done when** the string changes nothing about `passed`, or you have stopped and asked.

## Phase 2: Validate before anything exists

```bash
afk validate 232
```

It is free, deterministic, and runs before any branch exists. It checks the YAML, every
`depends_on`, cycles, that each task is an open sub-issue of the epic, the branch, and
`max_parallel`, and prints **depth and blast radius** per task. Read those to the user:

- A failed root strands its whole subtree. "#204: depth 0, blast radius 7 of 8" means one
  bad ticket costs seven skipped ones.
- Depth 2 is the working target; depth 3 wants a reason. Integration is serialized, so a
  wider, shallower graph finishes sooner than more concurrency on a deep one.
- `maxParallel` in config is a floor: the Runner raises it to the graph's root width. Report
  the root width as the real lane count.

On a refusal, quote it verbatim, name the field or child at fault, translate it with
`refusals.md`, and stop.

Bare `validate` is not a design review. `afk epic` always runs the semantic plan review
before it creates anything; `afk validate 232 --plan-review` runs it now. It is a model and
not deterministic, so a pass is one sample. Read a refusal against the child issues yourself
before relaying it, because it is often right. An `unsatisfied_criterion` (an epic criterion
no task would satisfy) is a missing ticket: take it to `coduo-tickets`, and leave the epic
prose alone.

**Done when** validation exited clean and you reported depth and blast radius, or you
stopped with the failure quoted.

## Phase 3: Launch

From the main checkout, detached:

```bash
nohup afk epic 232 --base=<base> --worktree --instructions="<string>" > ~/.afk-claude/launch-232.log 2>&1 &
```

Use the log path your launch line names, if it names one. Drop `--instructions` when there
are none.

- **Detached with `nohup … &`.** A foreground call or a `run_in_background` task has a time
  limit, and a Runner killed at it orphans its lanes.
- **`--worktree` on every launch and restart.** The epic runs in
  `~/code/worktrees/<clone>/epic/<n>/<clone>` with its own `.afk/`, dashboard and integrator,
  and the main checkout stays the user's. The `launch-232.log` names it on its
  `epic worktree at` line. Every `.afk/` path from here on is inside that checkout.
- **`--base` on every launch and restart.** Its default is `main`, and a stale local `main`
  runs happily on the wrong base.
- **Run from the main checkout, never from inside the epic checkout**, and run every `gh`
  command from inside the repo.

Then, in the same turn:

1. Confirm it is running: `pgrep -f "afk.mjs epic 232"` and the log (the wrapper runs `afk.mjs`, so "afk epic"
   never appears in the command line). An exit in seconds can be
   correct (Phase 4).
2. Read the instructions back from state. If they are missing, stop and report: a run
   without the user's constraint looks the same as one with it.
   ```bash
   node -e 'console.log(JSON.parse(require("fs").readFileSync("<epic checkout>/.afk/state.json","utf8")).customInstructions ?? "(none)")'
   ```
   A restart needs no `--instructions`: state wins, and a different string is refused. New
   instructions mean a new run.
3. Arm the check-in: `sleep 1800` with `run_in_background: true`. When it fires, run
   `afk status` and `tail -40 <epic checkout>/.afk/agent-auto.log`, post five lines at most
   (elapsed and tally, lanes in flight and for how long, what changed since the last one or
   "no change since HH:MM", any gate with its filled-in command), and re-arm. Stop re-arming
   when the epic closes, when it parks on a gate you reported, or when the user says so. If
   you pick up a run with no check-in armed, arm one. `afk status` printing
   `orchestrator exited at …` mid-run means the Runner died: relaunch with the same command
   (`docs/runbook.md` section 9).

Report the launch with the final checklist's first four items and the dashboard port the
launch log prints (`EPIC: dashboard port <n>`). A failed or `integration_failed` lane is read
with field notes section 4; a wave of lanes dying in their first seconds is infrastructure
(login, env, a cache), not N bad tickets.

**Done when** the run is up or its quick exit is explained, the instructions are read back,
and the check-in is armed.

## Phase 4: Human gates

**`gate: before`.** On a fresh epic whose root is gated, nothing is runnable and the run
exits in seconds. That is correct, and it looks like a crash. The log says
`AUTO: no automatic work remains; human-gated task(s) ready: 204.` (A last line of
`AUTO: no active, queued, or automatically runnable tasks remain.` means no gate is
involved.) Report it like this, with real numbers:

> **Waiting on you for #204**, "Provision Stripe test-mode webhook secrets". It is
> `gate: before`, so nothing else can start: #205 and #206 depend on it, and #208 and #211
> on those. The run exited because nothing was runnable, not because it failed. When it is
> done, release it with `afk epic 232 --base=main --worktree --task=204`.

The release re-validates the epic and re-runs the plan review, so a graph that moved in the
meantime is refused; report that, do not route around it. A `--task` run never reaches the
closeout, so after the last gated task passes, relaunch without `--task`.

**`gate: after`.** No builder runs. The task is `awaiting_acceptance` from the start and the
epic cannot close until the user accepts:

```bash
afk epic 232 --base=<base> --worktree --accept=204
```

`--accept` is refused unless the newest closeout review ran at the branch head, so the
Runner reviews before acceptance. Hand commits during a walkthrough move the head: relaunch
without `--accept` to get a fresh review, then accept. `--force` skips that and is the user's
call. A later must-fix puts the gate back to `awaiting_acceptance`.

To prepare a walkthrough for the user, brief a sub-agent "drive to the first credential
prompt, enter nothing", never "do not sign in".

Every report that stops for a human names the task, its title, what it blocks, and the
exact command, filled in.

**Done when** the user knows which gate waits on them and has the command.

## Phase 5: Close out

When the epic stops, the Runner runs the closeout verifier, a fixer over its must-fix,
blocker and major findings, a fix gate, and posts the closeout on the PR and the epic issue
(`docs/closeout.md`). The fixer never sees minor findings, and gets nothing when the
review session died (`agent_failed`, `auth_failed`). Fixes made after that appear in no
comment unless you post one. Run `afk fate` and `afk close` as `cd <epic checkout> && afk …`.

1. **Wait out a live fixer.** While `pgrep -f agent-fix-232` finds it, the log sits at the
   closeout verifier for ten minutes or more. That is not a stall.
2. **Read the records**: `.afk/verifier/232/report.json`, `.afk/fixer/232/report.json`
   (`fixed`, `deferred`, `notQueued`) and `.afk/fixer/232/gate.json`. A gate the verifier
   reports `skipped` did not run, so every verdict resting on it was read, not run: rerun
   that gate yourself on the epic branch while no other gate runs, and say which you reran.
3. **Give every finding one fate**, the minors included. `afk fate 232` lists each finding
   with its id. A finding you will fix in step 5 gets its `--fixed` fate after that commit.
   Record each:
   ```bash
   afk fate 232 <finding-id> --fixed --reason="<sha>"
   afk fate 232 <finding-id> --dropped --reason="<why: over-engineering, or code the ticket never asked for>"
   afk fate 232 <finding-id> --accepted --reason="ticketed #<n>"
   ```
   Ticket only a stub or real product work too big for this PR, grouped by subsystem. Your
   fates default to `--by=cos`. A `--fixed` fate lifts nothing from `afk merge`; only a fresh
   review at the head, or the owner's accept or drop, clears a must-fix. The owner's takes
   `--by=owner` and a link to a comment he wrote himself; do not write that comment for
   him, because `afk fate` refuses one with an agent mark.
4. **Check each fixed finding's lesson** in the runner's "Closeout fixes" comment. Send back
   a thin `none`, and a lint rule without red and green fixtures. Treat a diff that edits an
   existing lesson rule, its fixtures or a suppression as a loosening.
5. **Fix what has no fate yet**, in one sub-agent on the epic branch running
   `/coduo-implement` with the repo's `roles.implementer` skills and that role's `notes`
   verbatim. Code the ticket never asked for gets deleted, not polished. Then run
   `/code-review` over that fix commit alone, since it is the least-reviewed code on the
   branch. One fix pass and one review; after that the check is the user's.
6. **If step 5 committed anything, rerun the review:** `cd <epic checkout> && afk close
   --redo 232`. The `review-at-head` guardrail reads only a review at the branch head. Give
   a fate to anything the new review raises; no second fix pass runs.
7. **Post one resolution comment on the PR.** Link the runner's "Closeout fixes" comment and
   tabulate only the rest: finding, fate, and sha, reason or issue. End it with the review
   marker so `coduo-land-pr` does not review the epic a second time:
   `<!-- coduo-land-pr:reviewed <head-sha> -->`, where `<head-sha>` comes from
   `gh pr view <pr> --json headRefOid -q .headRefOid`. Read it back with
   `gh pr view <pr> --json comments --jq '.comments[-1].url'`.
8. **Hand over the merge.** Run `afk merge 232 --root=<epic checkout> --dry-run` and give
   the user its `PASS|FAIL|WAIT` lines and the command without `--dry-run`. Run `afk merge`
   before `afk finish`, which removes the state it reads. When the user says "merge it",
   run it: it merges, probes health and lands the PR (issues closed, branch deleted, lanes
   pruned). Exit 2 means merged with a red probe (`docs/runbook.md` section 13). If the user
   merged by hand and says "merged", run `/coduo-land-pr`.

**Done when** every finding has a fate in `.afk/fates/232.jsonl`, the resolution comment's
URL is in your report, and the user has the merge command or `afk merge` has run.

## Final report checklist

- [ ] Epic, branch, base, and whether the branch was new
- [ ] Depth and blast radius per task, as `afk validate` printed them
- [ ] Instruction string as read back from state, or "none"; any refused clause with its
  rewrite
- [ ] Running, gated and waiting-on-dependency tasks, named
- [ ] Any human gate: id, title, what it blocks, filled-in command
- [ ] `passed` means the checks passed; the closeout review is where code gets read
- [ ] At closeout: fates per kind, the resolution comment URL, the `afk merge` guardrail lines
