---
name: coduo-afk
description: |
  The invocation surface for the AFK runner. START — launch an unattended run
  from a GitHub epic: read the `afk:` block, validate the DAG, create the
  feature branch, run it, check in every 30 minutes, and close it out with
  every review finding fixed, dropped or ticketed on the PR. CHECK — validate
  only, launch nothing. STAGGER — run several epics on one machine, staggered
  so their baseline gates never overlap. Carries epic-wide, additive-only
  custom instructions and persists them to `.afk/state.json`. Use for "start
  an afk run on #232", "just validate #232", "coduo-afk stagger #A #B #C", to
  watch or close out a run already going, or "ping me when the epic closes".
  Starting a run comes after
  `coduo-epic` and `coduo-tickets`. SETTING A REPO UP is not this skill:
  `setup-coduo-agents` then `setup-coduo-toolchain` do that.
disable-model-invocation: false
---

# Coduo afk

The invocation surface. `coduo-epic` writes the epic, `coduo-tickets` writes the
`tasks:` block, and this skill starts the thing.

**The runner does the work. This skill's job is to start it correctly and to
explain what happened.** It does not schedule, does not merge, does not decide a
failure is fine. The runner's `README.md` (in the coduo-afk checkout) is authoritative for what
the runner is and what each command does, and `docs/runbook.md` in that repo is
authoritative for what to do when a run goes wrong. Read them; do not paraphrase
them here.

**Read `field-notes.md` in this directory before you launch, resume or stagger a
run, when a lane or baseline goes red, and before you close out.** It holds the
lessons from live runs that the runner's docs do not: dependency pre-installs,
state archiving, epic-authoring traps, the ways a green gate lies, wave mode.

## Verbs

**Setting a repo up is not a verb here.** Use `setup-coduo-agents` (plugins,
classification, and the `roles:` block) then `setup-coduo-toolchain` (deps and
lint config on the base branch). This skill used to carry a setup phase that
delegated to `setup-coduo-agents`; that delegation could never fire, because
the skill was slash-only and no agent could reach it. It is model-invocable
now, so the phase would only be a second route to the same place.

**`coduo-afk start #232`** — the repo is set up and an epic is ready. Start at
Phase 0.

**`coduo-afk check #232`** — "just validate", "don't launch". Run Phases 0–2,
report the Phase 2 numbers and any refusal, then stop. Create no branch and no
worktree, and launch nothing, until the user says go.

**`coduo-afk stagger #A, #B and #C`** — run several epics on one machine,
staggered so their baseline gates never overlap. Start from
`stagger-template.md` in this directory: it is the invocation that ran
github-center wave 1 end to end, with every line traced to the incident that
put it there. Fill in the epic numbers and the repo's env line; do not trim the
rest.

If you cannot tell which the user means, the presence of
`.afk-setup/config.yaml` decides it: absent means setup, present means start.
A request naming multiple epics is always stagger.

**`afk` in every command below** is the runner on the user's `PATH`, run from
the project root. If it is not there, it is
`node <coduo-afk checkout>/afk.mjs` and nothing else changes — say so once
and carry on; do not create the symlink for them.

Two rules that outrank everything below, because both failure modes are silent:

- **Stop and report. Never repair.** On a validation failure or a human gate,
  you stop and say so. You do not edit the epic to make the validator happy and
  you do not decide a gate is probably fine. When a chief of staff runs the night,
  ask it with `afk cos ask --id=<slug> --title="<question>" --from=orch-<n>`, say the
  same in the session, and wait for the relayed answer.
- **A correct run can exit in seconds and look like a crash.** See Phase 5. If
  you get one thing right in this skill, get that one right.

## Driving from Claude Desktop

The user always runs this skill from a Claude Desktop session, never from a
terminal. That session is the **Orchestrator**: you. `auto.mjs` is the Runner,
which is code and owns the queue and every pass or fail; the supervisor is a
read-only model call the Runner makes, and it has nobody to ask. You are the
only role that talks to the user, and the only one with hands. The user's standing instruction
for this role:

> When a step doesn't need my input, keep going. Put status notes in the same
> message as your next action. Stop and ask only when you can't continue without
> me, or before anything destructive: deleting data, force-pushing, or changing
> anything outside this repository.

What that means here:

- **Keep going between phases.** Validate, launch, read back
  `customInstructions`, arm the check-in, all in one run, with no "shall I
  launch?" in between. Each status line goes in the same message as the tool
  call that follows it, not in a message of its own that ends your turn.
- **"Can't continue without me" covers the stops this skill already has**: a
  validation failure or plan-review refusal (Phase 2), a refused instruction
  clause (Phase 1), a human gate or an unaccepted `gate: after` (Phase 5), a sum
  of lane widths over the machine budget, a missing dependency that has to be
  installed on the base branch, and an open ruling a lane needs. "Stop and
  report, never repair" still holds. Keep going means don't wait for permission.
  It does not mean fix the spec so you can keep moving.
- **Orchestrate; sub-agents do the work.** Cheap status reads stay inline:
  `afk status`, `tail` the log, `gh`. Anything that runs a suite, reads code to
  find a cause, or edits a file is a sub-agent brief: diagnosis in one agent,
  the fix in a second, both on Opus, each in its own worktree. Run the cheap
  check on an agent's claim before you relay it. The user has had to stop a
  session mid-run to say this (2026-09-24, epic #251).
- **Decide small stakes yourself; do not wait for the user on them.** A blocker
  in the code or the test harness that changes no product behaviour gets fixed
  through a sub-agent and the run relaunched, with the decision recorded in a PR
  or issue comment: test-setup timing, a merge conflict where one side
  deliberately deleted what the other edited, a union of locale keys, a
  screenshot that differs by 1% or less. Stop for real judgement only: product
  behaviour changes, security or billing logic, possible data loss, a one-way
  door, or a conflict whose intent is unclear on both sides. This does not
  loosen "Stop and report": the spec, a validation failure and a human gate are
  still the user's.
- **Destructive in this skill, so ask first**: removing or archiving
  `.afk/state.json`, `afk reset`, deleting a branch or removing a worktree,
  killing a runner or lane process, `git push --force`, merging the epic's PR.
  Changes outside the repo count too: editing an issue body, closing or
  re-parenting issues, installing a global tool, editing `~/.claude` or the
  afk-claude runner repo. The user saying "merged" or "merge it" authorizes
  `coduo-land-pr` for that PR, and "park" authorizes `coduo-afk-park`.
  **Quota auto-park** is standing: when you hit a usage limit ("limit reached",
  "resets <time>"), or a lane halts `infra_failed` because it never reached the
  API, run `coduo-afk-park` for this epic at once, without asking. Do not park
  early on a forecast. Then tell the chief of staff, if there is one, with
  `afk cos ask --from=orch-<n> --id=parked-<n>`. A step
  the user already asked for in the invocation,
  such as the stagger template's "when I say merged … close the epic", is
  authorized once they say the trigger. It does not carry over to the next
  epic.
- **Keep going also covers the waiting.** `afk epic` is launched detached
  (Phase 3), never in the foreground and never as a `run_in_background` task:
  both have a time limit, and a Runner killed at it orphans its lane agents.
  The check-in `sleep` runs with `run_in_background: true`, because foreground
  `sleep` is blocked here. So while a run works, you
  are silent, and the 30-minute check-in (mechanism in Phase 3) is the status
  note for that silence. It is on whenever this session is watching a run: a
  start, a stagger, a resume, a closeout you are waiting on, any "ping me
  when…". If you pick up a run with no timer armed, arm one in the same turn.
  The first check-in carries the dashboard URL.

## Phase 0 — Read the epic, and the instructions the human gave you

```bash
gh issue view 232 --json number,title,body,state
```

You are looking for the `afk:` fence, and specifically for `tasks:`.

**An epic with no `tasks:` block is inert.** It has a PRD, children, and a
diagram, and it will run nothing — `coduo-tickets` Phase 4 never happened.
Nothing errors at you; the run finds no tasks and exits. If `tasks:` is missing,
stop here and tell the user to run `coduo-tickets` on this epic. Do not author
the block from this skill; deriving `depends_on` is the ticket skill's job and it
needs the child issue bodies you do not have in front of you.

Also confirm, while it is free:

- `.afk-setup/config.yaml` exists, with `defaultChecks` and `worktreeSetup`.
  Without `worktreeSetup`, every lane fails its gate on a missing `node_modules`
  with an error that never names the missing file. It is YAML, and it is
  committed — `.afk-setup/` is the human-owned half of the project interface and
  `.afk/` is gitignored machine state. A repo still carrying a root
  `afk.config.json` is the pre-split layout: the file was removed with no
  compatibility shim, so the runner will not find its config at all.
- `roles:` in that file is optional but worth a glance. It is which skills each
  agent gets — `always` a rule, `offer` a choice the agent makes per task. If it
  is missing and the repo has stack plugins enabled, say so once: `afk stack
  detect` proposes the block, deterministically and for free, and
  `setup-coduo-agents` writes it.
- `roles.verifier.gates` and `roles.verifier.network` are NOT auto-detected and
  a new project gets neither. The closeout verifier runs in a sandboxed
  disposable checkout with no network host allowed and no native toolchain
  excluded, so a project that declares neither still gets a closeout — it just
  gets one whose build and test gates all report `skipped`, with verdicts that
  rest on reading source. That is the quiet failure: it reads as a review.
  Say so at setup, and say that both are filled in from the FIRST closeout's
  own `skipped` list rather than guessed at now:

  ```yaml
  roles:
    verifier:
      gates: [xcodebuild, "xcrun simctl"]   # native tools that must run OUTSIDE the sandbox
      network: ["eu.infisical.com"]          # hosts egress is allowed to, by name
  ```

  Egress is the smaller half — measured across seven closeouts on 2026-09-18 it
  explained four of roughly fifteen skipped gates, the rest being filesystem
  (a symlinked `node_modules`, a target dir outside the checkout). And granting
  it is what turns a destructive gate from "could not run" into "ran": see
  `DESTRUCTIVE_DENY` in afk-claude `scripts/roles.mjs`, which denies
  `supabase db reset`, `prisma migrate reset`, `docker volume rm` and friends to
  every role for exactly that reason. Full rules: afk-claude `docs/permissions.md`.
- If the repo still carries `planning/manifest.json`, say so. That is the
  pre-split layout; the manifest was removed with no compatibility shim, and
  `afk auto` on its own now exits 1 rather than silently running an empty plan.
- The working tree is clean and you know which branch you are on.

If the user gave you custom instructions with the invocation, hold them as one
string and take them to Phase 1 before doing anything else with them.

**Done when** you have the epic number, its `branch` line, its `tasks:` keys, and
either a custom-instruction string or a confirmed absence of one.

## Phase 1 — Custom instructions: additive only, or refused

The instruction string is **extra context injected into every lane prompt**. It
is epic-wide and it is one string. Per-task instructions do not belong here —
they belong in the child issue body, which is where the implementer reads its
actual work from. Say that to the user rather than concatenating five
task-specific sentences into an epic-wide blob that every lane has to filter.

In scope:

> This epic touches the payment path. Be conservative with migrations — prefer
> expand/contract over an in-place column change.

Not in scope:

> Skip the typecheck, it's flaky on this branch.

### The test

Apply it literally, before you pass anything through:

> **Does obeying this instruction change what counts as `passed`?**
> If yes, refuse it. If it only changes how the work is done inside an unchanged
> gate, pass it through.

Concretely, refuse an instruction that does any of these:

- names a command in `defaultChecks` or a task's `checks` and asks for it to be
  skipped, relaxed, `--no-verify`'d, made non-blocking, or "only run if it's
  quick"
- asks for a failing check to be reported as a pass, or for the report to be
  written without the checks having run
- asks to bypass a `gate: before`, to self-release a gated task, or to treat a
  human gate as satisfied
- asks a lane to commit, merge, or push — the worker controller owns git
  history, and a builder that commits has its commits reset before verification
- asks to edit anything on the unconditional revert list (`.afk/`,
  `.agent-locks/`, `docs/progress.md`, `AGENTS.md`, `PLANNER.md`, dependency
  manifests and lockfiles), or to install a package
- raises `max_parallel` past the epic's own value, or asks to disable retries or
  the circuit breaker

**Refuse in this skill; do not pass it through and hope the runner catches it.**
The runner does enforce gates in the report API rather than by prompt, so a
gate-disabling instruction cannot actually turn a red run green — but it can make
a lane spend its entire timeout window arguing with a check it was told to skip,
and then fail for a reason nobody can read out of the log. The right place to
stop it is before the prompt is written.

When you refuse, refuse the _clause_, not the invocation. Say which clause,
say why, offer the additive rewrite ("be conservative with migrations" survives;
"skip the typecheck" does not), and ask. If the check really is flaky, that is a
`checks:` narrowing on the child task or a fix to `.afk-setup/config.yaml` — a spec
change the user makes deliberately, not a sentence smuggled into a lane prompt.

**Done when** the instruction string contains nothing that changes what `passed`
means, or you have stopped and asked.

## Phase 2 — Validate before anything exists

```bash
afk validate 232
```

`afk epic` runs validation implicitly, but run it explicitly first anyway. It is
free, it is deterministic, and it is the last moment before a branch and a
worktree exist. A contradiction found here costs nothing; the same contradiction
found after the branch is cut costs a cleanup.

The deterministic tier checks: the YAML parses; every `depends_on` names a task
that is also a key in this block; no cycles; every task key is a real open issue
whose **parent is the epic** (text alone does not make a sub-issue); `branch`
does not already exist with divergent history; `max_parallel` is sane; unknown
keys are rejected outright rather than ignored.

It also prints **depth and blast radius per node** — pure graph math, no tokens.
Read those numbers to the user, do not just pass the exit code along:

- `dependenciesPassed` requires _every_ dependency to have `passed`, so a root
  failure strands its whole subtree. "204: depth 0, blast radius 7 of 8" means
  one bad ticket costs seven skipped ones, and you find out hours in.
- Depth 2 is the working target. Depth 3 wants a reason someone can say out loud.
- Serialized integration is the real stall, not agent count — every passing lane
  queues behind a single merge plus post-merge checks at 1.5–6 min. More
  concurrency does not help a deep graph; wider and shallower does.

**On failure: stop.** Print the validator's message verbatim, say which epic
field or child issue is wrong, and hand it back. Do not edit the epic body, do
not drop the offending edge, do not close a child issue to make a dangling
reference go away. The DAG is the user's spec; a skill that silently repairs it
produces a run against a graph nobody approved.

### The refusals, and what each one actually means

`validate` and `epic` refuse the same way and name the offending task by id.
Translate; do not just forward the string. Each of these has exactly one fix and
none of them is "edit the epic until the validator shuts up":

| Refusal                                                  | What it means                                                                                                                                                            | What fixes it                                                                                                     |
| -------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------- |
| `#204 is not a sub-issue of epic #232`                   | The `tasks:` key names an issue the epic does not own. Text mentioning the epic is not a link.                                                                           | Re-parent the child (`gh` sub-issue link), or drop the key. `coduo-tickets` Phase 1 owns this.                    |
| `#204 is closed, not open`                               | A closed issue is not runnable work.                                                                                                                                     | Reopen it, or remove it from the block along with every `depends_on` that names it.                               |
| `#204's acceptance criteria name \`bun.lockb\``           | The ticket requires an edit the runner reverts under every lane, so no builder can satisfy it — this is the shape that once shipped a `passed` task over a test file that never ran. The same path in the ticket's prose is a warning, not a refusal. | Rewrite the criterion, or grant the edit in `protectedEdits` in `.afk-setup/config.yaml`. `coduo-tickets` Phase 1 owns the ticket. |
| `no checks: on the task and defaultChecks supplies none` | Nothing would verify that lane; it would merge having run nothing.                                                                                                       | Add `defaultChecks` to `.afk-setup/config.yaml` (the normal fix), or a narrower `checks:` on that one task.              |
| `branch ... already exists with divergent history`       | The epic's `branch:` points at something that is not a descendant of the base.                                                                                           | Rename the epic's branch line, or delete the stale branch. Never force it.                                        |
| `the epic's graph has changed since this run started`    | Restart-only. The spec is re-fetched, never cached, so a child closed, unlinked or re-pointed mid-run changes the shape hash. It lists what moved.                       | Finish or abandon the existing run — reset the tasks, or remove `.afk/state.json` — before running the new shape. |

Only the last one comes from the run itself; the other five are validation and
cost nothing. A shape change is refused on **ids, edges and gates only** — a
retitled issue will not halt a six-hour run.

The semantic tier (`plan-reviewer`) is opt-in on `validate` and unconditional on
`epic`. Bare `afk validate` gives you the deterministic tier plus the graph math
and nothing else — do not describe that output as a design review. Add
`--plan-review` for the real thing: one read-only agent reads the epic and every
child issue and reports contradictions. It costs tokens and needs a live login,
which is why it is not the default. `afk epic` always runs it, before it creates
anything, and a plan review that refuses leaves the repository untouched.

One finding class blocks whatever severity it carries, for as long as the repair
is free: `unsatisfied_criterion`, a criterion in the epic that no task would
satisfy, while the tasks it names are still pending. Past them — on a restart —
the reviewer's own severity applies again, because nothing cheap is left to do. It is the cheapest correct
prediction the system makes — it called, before a token was spent, that an epic
would finish green with the duplication it existed to remove still intact, and
it did. Take the repair back to `coduo-tickets`: the missing work is a ticket,
and patching the epic's prose to match the plan leaves the lanes reading the old
one.

**Done when** `afk validate` has exited clean and you have reported depth and
blast radius, or you have stopped with the failure quoted.

## Phase 3 — Start the run

```bash
nohup node $AFK epic 232 --base=<base> --worktree > /tmp/afk-232-run.log 2>&1 &
```

Detached with `nohup … &`, never as a `run_in_background` task: that limit
killed epic #489's Runner at 30 minutes (2026-10-04), and the restart reset the
lane worktree and lost 25 minutes of builder work. Watch it with the log and a
`pgrep -f "afk epic 232"` exit check. Run every `gh` command from inside the
repo; from `/tmp` it fails silently, and a `--body-file` built from that empty
output wiped the same epic's body.

Both flags go on every launch and every restart, and both run from the main
checkout. `--worktree` names the epic's worktree after the directory it runs
in, so running it from inside the worktree starts a second, nested run. `--base`
because its default is a hardcoded `main` with no config key: a lane worktree with
no local `main` fails loudly, and a stale local `main` runs happily on the wrong
base. `--worktree` because the user keeps the main checkout
for their own work, and a run in it has repeatedly taken it away from them.

`afk epic` fetches the epic and its children, validates, creates the feature
branch named in the `branch:` line, and starts the run. There is no local copy of
the spec — it holds the DAG in memory and re-fetches on restart.

Three things to get right before you type it:

**Custom instructions must land in `.afk/state.json`, not in this conversation.**
This is the whole point of the persistence rule: a retry, or a restart three
hours in, still carries them. Instructions that live only in the invoking session
are lost on the first crash, silently, and the run continues without them looking
exactly like a run that never had them.

The flag is `--instructions=`, on both `afk epic` and `afk auto`. Quote it; it is
one free-form string and the shell will otherwise eat it:

```bash
node $AFK epic 232 --instructions="This epic touches the payment path. Prefer expand/contract over in-place column changes."
```

Then **read the string back out of state** before you walk away. The runner
writes it to the `customInstructions` key of `.afk/state.json`:

```bash
node -e 'console.log(JSON.parse(require("fs").readFileSync(".afk/state.json","utf8")).customInstructions ?? "(none)")'
```

If it comes back `(none)`, **stop and report**. Do not let the run continue on
instructions that exist only in your context window — an eight-task epic running
without the constraint the user asked for looks exactly like one that has it.

Two consequences of persistence, both worth saying out loud:

- **A restart does not need the flag.** State wins: the run reloads the string it
  started with, so `node $AFK epic 232` on its own resumes with the same context
  every earlier lane got. Re-passing the identical string is harmless.
- **A restart with a _different_ string is refused**, with `AUTO: this run was
started with different custom instructions; refusing to swap them mid-run.` A
  mid-run instruction change is a spec change and is refused for the same reason
  a changed graph is. If the user genuinely wants new instructions, that is a new
  run: reset the tasks or remove `.afk/state.json` first, deliberately.

**The runner starts from a clean checkout of its base.** `afk epic` creates and
uses the epic's feature branch, so this is handled for you — but if you are
driving the underlying `afk auto` seam directly, it exits immediately on the
wrong branch (`AUTO: must run from the main checkout`), and five runs once died
silently on exactly that guard because the message went only to a background log.
Check the exit code, do not assume a run is underway.

**Start it and leave it.** Do not pause between tasks, do not print diffs for
approval. Under `--runtime=herdr` you get panes; otherwise the `claude`
subprocesses are invisible to the Claude Desktop UI and visibility is
`.afk/agent-auto.log`, the dashboard, and `heartbeat --watch`.

```bash
node $AFK heartbeat --watch    # notifies on death, stall, and human gate
node $AFK dashboard            # port derived from the checkout path; the launch log prints it, and http://localhost:4099 lists every run
```

### Arm the 30-minute check-in. Always, without being asked.

`heartbeat --watch` is **event-driven** — it fires on death, stall and human
gate, and says nothing at all while a run is healthy. That is correct for a
watcher and wrong for a human who was asleep: an eight-hour run that goes well
produces silence, and the first thing they get is a cold-cache conversation where
they have to ask. The check-in is not an option the user turns on per launch. Arm
it on every run, immediately after the launch call, and do not mention that you
are doing it.

Nothing in `afk` can do this — only the agent driving the conversation can write
into the thread. The mechanism is a background command that exits on a timer and
re-invokes you:

```bash
sleep 1800
```

Run it with `run_in_background: true`. When it exits you are re-invoked; then, in
one turn:

1. `node $AFK status` and `tail -40 .afk/agent-auto.log`.
2. Post a check-in **in the thread**, five lines at most:
   - elapsed, and the tally (`passed 3 · running 2 · pending 1`)
   - which lanes are in flight and for how long
   - anything that changed since the last check-in — a verdict, an integration,
     a retry. On a quiet interval say "no change since HH:MM" and stop there.
   - any human gate, with the filled-in `--accept` command
   - nothing else. No diffs, no log paste, no speculation about lanes still
     working.
3. Re-arm the same `sleep 1800` unless the run is over.

Stop re-arming when the epic closes, when it parks on a gate you have reported,
or when the user says to. Say once, in the launch report, that you will check in
every 30 minutes — then do it silently rather than announcing each timer.

**Done when** the run is started, the check-in timer is armed, the exit is
non-immediate or its immediacy is explained (Phase 5), and the instruction string
has been read back out of `.afk/state.json`.

## Phase 4 — Report what happened

Not a status dump. The user asked you to start a run; tell them the state of it:

- the epic, the branch, and the task ids with their `depends_on`
- depth and blast radius from Phase 2
- the custom instruction string as persisted, quoted, or "none"
- **what is running, what is gated, and what is waiting on a dependency** —
  three different things that all look like "not done"
- anything you refused in Phase 1, with the clause

`afk status` marks a gated task `pending (gated)` and the lane table flags it
with a lock. Read the distinction out loud; a user who sees seven pending tasks
cannot tell which one is waiting on _them_.

A task can fail in two places and they mean different things. `blocked` /
`failed` means the builder never produced a good branch. `integration_failed`
means the branch was good and the merge was not — the base is restored to its
pre-merge SHA and **the branch and worktree are retained**, so the work still
exists and someone should go finish the merge by hand. Never report the second as
if it were the first.

And `passed` is not `correct`. Post-merge checks prove the tree is green, nothing
more. The `verifier` closes that gap at the end of the epic — `/code-review` over
the integrated branch, checked against the acceptance criteria in the child
issues — and the runner runs it whenever the epic **stops**, complete or not. On an epic
parked at a human gate that means BEFORE you accept, which is the only order in
which a review can inform an acceptance. It is **advisory**: it writes a report
and marks nothing complete, so its `must-fix` list is the human's. Mid-run, `afk verify <issue>` runs the same review by hand,
and `.afk/runs/<id>/` is still the per-lane record of what a builder did.

The verifier is the runner's own review and it always runs. A second, independent
`/code-review` over the integrated branch is the one worth spending when the epic
mattered: on the run that produced this advice it found a user-facing bug, a
dead test chain and four duplications that every automated gate had called green.
Say which of the two you are reporting.

Write your account of the run in a **PR comment**. The body is a view of run
state — `afk` re-renders it from `.afk/state.json` on every render and never
reads it back, so anything typed there is gone at the next one, silently. The
comment is the only durable surface, and the runner never touches it.

Acting on the findings is Phase 6.

**Done when** the user knows what is running, what is blocked on them, and what
they still owe the run.

## Phase 5 — "Waiting on you for #204"

The DX detail that matters most.

On a fresh epic whose root task is `gate: before`, **there is nothing runnable**.
The root is gated, everything else depends on the root, the scheduler admits
nobody, and the run exits in seconds. That is completely correct behaviour and it
reads exactly like a crash — same instant exit, same empty log, same silence.

So do not report an exit code. Report this, in these words:

> **Waiting on you for #204** — "Provision Stripe test-mode webhook secrets".
> It is `gate: before`, so nothing else in the epic can start: #205 and #206
> depend on it, and #208 and #211 depend on those. The run exited in seconds
> because there was nothing runnable, not because it failed.
>
> Do the provisioning, then release it:
>
> ```bash
> node $AFK epic 232 --task=204
> ```
>
> When #204 passes, `node $AFK epic 232` picks the epic back up and #205 and
> #206 go out in parallel.

**A release is a restart with one task released**, which is why it is the same
command and not a second path. `--task=<id>` re-fetches and re-validates the
epic, re-runs the plan review, and only then admits that one gated task —
`explicitTaskId` is the single thing that makes the scheduler ignore
`humanGated`, and it narrows the run to that task alone. Consequences
worth saying out loud:

- **A graph that moved while the human was deciding stops the release.** The
  re-fetch feeds the shape hash, so a child closed or re-pointed in the meantime
  is refused rather than resumed into. That is the correct outcome to report, not
  something to route around.
- **A plan review that refuses refuses the release too**, and costs one short
  read-only session every time. Known price, not a surprise.
- **Do not re-pass `--instructions`.** The release lane reads
  `customInstructions` back out of `.afk/state.json` like every other lane, and a
  different string on a restart is refused outright.
- **A commit to the base branch mid-run makes the release refuse.** The epic
  branch must still start from the base, so merging any PR into `main` while an
  epic runs strands its next `--task` release. Merge the base into the epic
  branch and push before releasing; better, hold unrelated merges until the epic
  closes. (Epic #398: merging #411 refused #406's first release.)
- **Releasing the last task leaves the epic open.** A `--task` run is narrowed
  to that task, so it never reaches the closeout review. When the released task
  was the last one, run `afk epic <n> --base=<branch> --worktree` without
  `--task` once it passes; that run finds nothing to build and closes out.

The old two-step — dump the DAG out of `afk validate --json`, then
`afk run --task=<id> --dag=<path> --base=<branch>` — still works and is what you
fall back to if you already have a DAG file. It needs the epic's branch checked
out; off it, the run exits with `AUTO: must run from the <branch> checkout`.

Three things that make that report work, all of them load-bearing:

1. **Name the gated issue and its title.** "A task is gated" is useless; "#204,
   provision the webhook secrets" is an action.
2. **Say what it is blocking**, with the count. It is the difference between "one
   thing is waiting" and "the entire epic is waiting".
3. **Give the exact command that releases it**, filled in — real epic number,
   real task id, real branch name. Use `afk epic <n> --task=<id>` (Phase 5's
   form); `afk run --task=<id> --dag=<path>` is the older equivalent. Either way
   the scheduler admits a gated task only when its id is named explicitly, which
   is precisely what makes the gate a gate. A command in
   a report that does not run is worse than no command, so paste the branch, do
   not leave a placeholder.

You are not guessing at the moment either. When the scheduler stops on a gate it
says so itself, by id, in `.afk/agent-auto.log`:

```
AUTO: no automatic work remains; human-gated task(s) ready: 204.
```

and `afk status` marks that row `pending (gated)`. If the log's last line is
`AUTO: no active, queued, or automatically runnable tasks remain.` instead, no
gate is involved — the DAG drained, or nothing was ever runnable, and that is a
different report.

Say the same thing for a gate reached mid-run, and for the heartbeat's gate
notification. Any moment the run stops for a human, the report names the human's
next command.

`gate: after` fires at the other end, and **no builder is ever dispatched for
it**: the task is `awaiting_acceptance` from admission, not even under an
explicit `--task=`, and the human's acceptance is the entire verdict. Four epics
ran one device-acceptance ticket through a lane before this and recorded
`blocked`, `failed` and `passed` for the identical shape, on builder judgment
alone. What waits is the **epic**, which cannot close until a human accepts:

```bash
node $AFK epic 232 --accept=204     # or: node $AFK auto --accept=204
```

`afk status` names the outstanding ones in the second form — quote the form the
screen shows when you are reading it back to a user. The acceptance is recorded
and survives a restart; `afk reset` on the task clears it. Nothing an agent
writes can grant one. Report an unaccepted `gate: after` exactly the way you
report a `gate: before`: the id, the title, and the filled-in command.

Prep a `gate: after` as soon as its blockers merge: build the Release artifact and drive
the flow yourself to the first credential, payment or system prompt, entering nothing,
before you hand it over (field notes, "Prepping a human gate").

## Phase 6 — Close out: every finding gets a fate, and the PR says which

When the epic stops, the runner runs the verifier, then the fixer, then posts
a closeout. Two parts of that can fail without anyone noticing, and this phase
exists to catch them:

- **The fixer gets an empty work list** whenever the verifier's report is not
  `ok` (unparseable, inconclusive, timed out), and `minor` findings are never
  queued at all. The closeout does say how many are left open, but nothing
  acts on them.
- **Fixes made after the runner is done, by you or a sub-agent, show up in no
  comment unless you post one.** The user is left asking whether the fixer ran.

The steps, once `afk status` shows the epic closed or waiting on your
acceptance. Under `--worktree`, every `.afk/` path below is inside the epic
worktree, not the main checkout.

1. **Wait out a live fixer.** `ps aux | grep agent-fix-<epic>`. While it is
   running, the lifecycle stays `open` and the log sits at "running the
   closeout verifier" for ten minutes or more. That is not a stall. Leave the
   branch alone until the process exits.
2. **Read the records.** The verifier report under `.afk/verifier/<epic>/`,
   `.afk/fixer/<epic>/report.json` (`fixed`, `deferred`, `notQueued`), and
   `.afk/fixer/<epic>/gate.json`. If the verifier's status is not `ok`, find
   the last report block in its `stream.jsonl` before you trust the status.
   A gate the verifier reports as `skipped` did not run: its verdicts come
   from reading source, so every finding and every `passed` resting on it is
   unverified. Rerun that gate yourself on the epic branch, outside the
   sandbox, before giving those findings a fate, and say in the resolution
   comment (step 6) which gates you reran, so the reader can tell a verdict
   that ran from one that was read.
3. **Give every finding exactly one fate.** Every finding means must-fix,
   blocker, major, each unmet or partial criterion, and the minors (the
   fixer never sees them; they are the `severity: minor` entries in the
   verifier's `report.json` `findings[]`). The fates:
   - **fixed**, with the commit SHA
   - **dropped**, with one line saying why: over-engineering, or code the
     ticket never asked for
   - **ticketed**, with the issue number. Only a stub, or real product work
     too big for this PR, earns a ticket (`coduo-implement` rule 5). Group
     tickets by subsystem rather than one per finding.
4. **Check each fixed finding's lesson** in the "Closeout fixes" comment. Send
   back a `none` whose reason is thin, and a rule without red and green
   fixtures. Review any diff that edits an existing lesson rule or its
   fixtures, or adds a suppression, as a loosening.
5. **Run the fix pass on whatever has no fate yet.** Use one sub-agent on the
   epic branch, running `/coduo-implement` with the repo's `roles.implementer`
   skills, and pass that role's `notes` verbatim, so the cleanup is held to
   the same standard as the lanes. It is `implementer` and not `fixer`
   because this pass may push and file tickets, which the fixer role is
   denied. If a finding hits code the ticket never
   asked for, delete that code rather than polishing it. Then run
   `/code-review` over the fix commit alone, because it is the newest and
   least-reviewed code on the branch. That is one review and one fix pass per
   branch. After that, the check belongs to the user; do not loop.
6. **Post one resolution comment on the PR.** The runner's own "Closeout
   fixes" comment already covers what its fixer fixed, so link that and
   tabulate only the rest: finding, fate, and SHA / reason / issue. Read it back with
   `gh pr view <pr> --json comments --jq '.comments[-1].url'`. A comment you
   posted but never read back does not count.
7. **Hand over the merge.** Give the user the `gh pr merge` command. When they
   say merged, run `/coduo-land-pr`.

**Done when** every closeout finding has exactly one fate, your report quotes
the resolution comment's URL, and the user has the merge command.

## Talking to a running run

`docs/epic-schema.md` makes this skill the entry point for talking to the
`supervisor` during and after a run — an LLM that holds the run's context, so
"why has 207 been running 40 minutes" gets an answer rather than a log dump.

The `supervisor` exists — `afk supervise <event>`, and it also answers a question
about the run in plain language. It is **read-only and advisory**: it proposes
`afk` commands and changes nothing, and the runner owns the queue and every
passed/failed transition whatever it says. `afk auto` consults it off the
critical path on run events, bounded by a wall clock, and a supervisor that fails
or times out is ignored rather than allowed to stall a run. Set
`supervisor: false` in `.afk-setup/config.yaml` to turn it off. What a human can
inspect directly:

```bash
node $AFK status              # tasks, lifecycle, which are gated, the supervisor's last diagnosis
node $AFK stats [<id>...]     # live agent stream statistics, per lane
node $AFK dashboard           # this checkout's derived port; http://localhost:4099 lists every run
node $AFK heartbeat --watch   # death, stall past agent.timeoutMs, human gate
tail -f .afk/agent-auto.log   # the reason for every failure
```

Plus the herdr panes under `--runtime=herdr`, which are real terminals — **a
blocked lane can be talked to directly.** The runner tolerates that intervention
because verification inspects artifacts rather than trusting claims.

Read `.afk/agent-auto.log`, not just the status. It carries the reason for every
failure, including the exact stray file or failed check behind an
`integration_failed`, and the reconciliation lines at the top explain any
disagreement between state and expectation.

One judgment call worth making yourself rather than waiting for the supervisor's
opinion: **a wave of lanes dying in the first seconds is infra, not bad
tickets.** Expired
`claude` login, an unset env var, a missing worktree cache. Every one exits
non-zero, the runner reads N task failures, and two in a row trip the circuit
breaker — so N good tickets look like N bad ones. Sub-second uniform failures
across unrelated tasks are environmental. Check auth and env before blaming a
single ticket.

Known hole, worth saying to the user: **nothing pages you when a lane is quietly
wrong.** Blocked lanes notify and the progress deadline catches silence, but a
lane making bad decisions for 40 minutes looks identical to a lane working.

## What is not built

Be accurate about this. A skill that promises unbuilt behaviour is worse than one
that admits a gap, and `docs/findings.md` in the runner repo is the live index —
`docs/deferred.md` was deleted along with the build it tracked.

| Thing                      | State today                                                                                                                                                                                    |
| -------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `allowed_paths` derivation | Declined for v1. Scope is repo-wide and advisory; out-of-scope edits are reported, not reverted.                                                                                               |
| Per-lane code review       | Declined. Review happens once, at epic close, over the integrated branch — never per lane.                                                                                                     |
| Per-role auto-compaction   | Not built. A builder that runs out of context is lost work; nothing resumes it.                                                                                                                |
| Supervisor auto-run        | Declined. It proposes `afk` commands and a human runs them. Its last live diagnosis is on `afk status`, which is what was actually missing — the advice used to reach a human only through `.afk/agent-auto.log`. |
| Merging the epic's PR      | Not built, deliberately. `afk finish` prints the closeout, prunes the lane worktrees and branches, and prints the `gh pr merge` command. A human runs it, or says "merge it" and `coduo-land-pr` runs it. Nothing in the runner lands its own work. |

Everything an older version of this table called unbuilt — `plan-reviewer`,
`verifier`, `supervisor`, the `gate: after` lifecycle, the ledger, the draft PR,
epic close — now exists. Check `docs/findings.md` in the runner repo before
repeating a gap from memory: that file is the live index and this one is a copy
that goes stale.

What the end of an epic actually looks like now: whenever the epic **stops** —
complete, parked on an unaccepted `gate: after`, or incomplete — the runner runs
the closeout verifier, renders a closeout, posts it as a comment on the epic
issue, and refreshes the draft PR it opened when the branch was created. On a
parked epic that happens BEFORE the human accepts, which is the only order in
which a review can inform an acceptance. The review is **advisory** — an epic
closes with the verifier's opinion attached, never on it, so `must-fix` findings
are the human's to act on and nothing waits for them. Tell the user the closeout
is coming and where it lands; do not tell them the run ends in silence. What
you do with it is Phase 6.

## Report

- the epic number, its branch, and whether the branch was created or already there
- `afk validate` output — depth and blast radius per node, verbatim
- the custom instruction string **as read back from `.afk/state.json`**, or "none"
- anything refused under Phase 1, with the clause and the additive rewrite offered
- what the run is doing: running, gated, waiting on dependencies — named, not counted
- if nothing is runnable: **"waiting on you for #<id>"**, the title, what it
  blocks, and the exact release command
- the reminder that `passed` means the checks passed, not that anyone read the
  code — the closeout review at epic end is where that happens, and it is
  advisory
- for a finished epic: where the closeout landed (a comment on the epic issue),
  the verifier's recommendation, and `afk finish` as the next command
- for a closed-out epic: the resolution comment's URL, the count of findings per
  fate, and the merge command
