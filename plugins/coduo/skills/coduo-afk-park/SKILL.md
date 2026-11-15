---
name: coduo-afk-park
description: |
  Park AFK work before the quota or the session runs out, and resume it later
  without re-deriving anything. PARK: start nothing new, let a merge in flight
  finish, stop this session's runners, lanes, Orchestrators and timers, and pin
  a resume note to each epic's PR. RESUME: read the notes and restart where they
  stopped. Use for "quota is running low", "start parking", "find a safe place
  to stop", "quota is back, continue", when an Orchestrator hits a usage limit,
  or when the user pastes a parked session's last message.
disable-model-invocation: false
---

# Coduo AFK park

The Runner already makes a restart safe: it rolls back an interrupted integration,
re-queues verified branches and saves unverified changes under `.afk/recovery/`. What a stop
loses is the context, so the resume note is what this skill produces.

**Scope.** Park only the runs this session owns: an Orchestrator parks its one epic, a chief
of staff parks the epics it launched or adopted. List any other live run in the report and
leave it alone.

## Park

### 1. Inventory

For each epic this session owns, find its checkout and read its state:

```bash
grep -o 'epic worktree at [^ ]*' <launch log> | tail -1     # the epic checkout
afk status                                                    # run from the epic checkout
```

Epic checkouts live at `~/code/worktrees/<clone>/epic/<n>/<clone>`. If you have no launch
log, `ls -d ~/code/worktrees/*/epic/*/*` lists them.

Then list what is running:

```bash
ps -axo pid,command | grep -E 'afk\.mjs epic|scripts/epic\.mjs|^ *[0-9]+ agent-' | grep -v grep
herdr agent list                                              # herdr Orchestrators, orch-<n>
```

The Runner is the `scripts/epic.mjs` process; the `agent-` processes are its lanes,
merger, verifier, fixer and reviewers. Add your own handles: the 30-minute check-in, any
`Monitor`, background shells and sub-agents.

**Done when** each run has one line: epic, lifecycle, lanes in flight, what is gated, PR, and the Runner's argv (the note needs it after the kill).

### 2. Choose each run's landing point

- **An integration, the closeout review or its fix pass is in flight:** wait for it. A
  restart pays for it again from the start.
- **Anything else:** stop now. A building lane is recoverable from its branch and recovery
  patch.
- **Your own unfinished edit:** commit it as `wip: …` and push; on a closed epic or an open
  `gate: after`, the note's **Then** starts with a fresh review (`afk close --redo <n>`, or
  a relaunch without `--accept`).

Say the plan in one line per run and carry it out. The request to park is the authorization.

### 3. Stop it, and prove it

Kill by pid, never by pattern. `kill` (SIGTERM) on the `scripts/epic.mjs` pid lets the
Runner restore an interrupted integration, signal its lanes and stop its dashboard; `kill -9`
skips all of that. A lane's own shells, MCP servers and headless Chrome can outlive it, so
look for them by cwd in the epic checkout and the lane folder:

```bash
kill <scripts/epic.mjs pid>
lsof -a -d cwd | grep -E '/worktrees/<clone>/(epic|lane)/<n>(/|$)'   # skip your own session and any Orchestrator's
kill <each pid listed>
```

An Orchestrator never stops itself. A chief of staff stops each Orchestrator only after its
note is posted: `node ~/code/projects/coduo-afk/scripts/orchestrator-herdr.mjs stop orch-<n>`,
then `herdr agent list` shows it gone. Stopping the whole night, it runs `afk cos stop` and
checks the summary says `refused 0` and `still alive 0`.

Then run the same `ps` and `lsof` again. A `kill -0` that says "dead" from a sandboxed shell
is not proof; if `lsof` still shows the process, use an unsandboxed `kill -9`. Stop your own
timers and monitors and check each stop took.

**Done when** `ps` and `lsof` show nothing of these runs, and none of your timers is armed.

### 4. Pin a resume note

Post it as a comment on the epic's PR, or on the epic issue when there is no PR. Not in the
PR body: `afk` re-renders the body and wipes what is written there.

```markdown
## Parked <YYYY-MM-DD HH:MM local> (<reason: quota / end of day>)

**State:** <lifecycle> · passed <n> · in flight when parked <ids> · gated <ids>
**Stopped at:** <the step, e.g. "Phase 5 step 5, fix pass not started">
**Owed by the human:** <gates with the filled-in command, rulings, merges> or "nothing"
**Main checkout:** <path>
**Resume:** `afk epic <n>` plus the flags from the Runner's argv (they carry `--runtime`) · or `none: waiting on --accept=<id>` · or `none: closed, continue Phase 5 step <k>`
**Then:** <the next one or two actions>
```

Read each one back with `gh pr view <pr> --json comments --jq '.comments[-1].url'` (or
`gh issue view` for an issue).

### 5. Report

One line per run with its note's URL, then everything **Owed by the human** as one list.
End with what to paste when the quota is back: `/coduo-afk-park resume`. Under a chief of
staff, also tell it: `afk cos ask --from=orch-<n> --id=parked-<n>-<HHMM> --title="Parked #<n> until <reset time>"`


## Resume

1. **Find the notes:** the latest "Parked" comment on each open epic PR
   (`gh pr list --search "Parked in:comments" --state open`), on the epic issue, or the
   message the user pasted. A session that hit the limit may have left no note: read that
   epic's `.afk/state.json` and `afk status` instead.
2. **Check what changed.** `git fetch`, compare each epic branch with its remote, and read
   `afk status`. The user may have accepted a gate or merged something in between.
3. **Relaunch only runs with work left to build**, through `coduo-afk` Phase 3: from the
   note's main checkout, detached, with the note's **Resume** line, one epic at a time so
   their baselines do not compete. Arm the 30-minute check-in, then do the note's **Then**.
   A note that says `none` goes straight to the step it names.

**Done when** each parked run is running again with a check-in armed, or is named as
waiting on the human for what its note says.
