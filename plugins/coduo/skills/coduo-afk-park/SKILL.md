---
name: coduo-afk-park
description: |
  Park AFK work before the quota or the session runs out, and resume it later
  without re-deriving anything. PARK: start nothing new, let merges in flight
  finish, stop every runner, lane and timer, and pin a resume note to each
  epic's PR. RESUME: read the note and restart where it stopped. Use for
  "quota is running low", "start parking", "wrap up to save tokens", "find a
  safe place to stop", "quota is back, continue", or when the user pastes a
  parked session's last message.
disable-model-invocation: false
---

# Coduo AFK park

Parking is cheap because the runner already makes a restart safe. On restart
it reconciles stale workers and worktrees, rolls an interrupted integration
back to its recorded base SHA, re-queues verified task branches, and saves
unverified changes as patches under `.afk/recovery/`. The work survives, and
what gets lost is the *context*: which run was where, what you were about to
do, and what the user still owes. That context is what this skill writes
down. The note is the product; stopping the processes is just the step you
can't skip.

## Park

### 1. Inventory what is live

For every epic this session touched, and every other epic on the machine:

```bash
ls ~/.afk-claude/epics/                      # epic worktrees, one per --worktree run
(cd <epic worktree> && afk status)           # lifecycle, lanes in flight, gated tasks
ps aux | grep -E 'auto\.mjs|wave\.mjs|agent-fix-' | grep -v grep
```

Add your own live handles to the list: the 30-minute check-in timer,
`heartbeat --watch`, any `Monitor`, background shells and sub-agents.

**Done when** each run has one line: epic, lifecycle, lanes in flight, what
is gated, and its PR.

### 2. Choose the landing point for each run

- **An integration or a fixer is mid-merge:** wait for it, since it takes
  minutes. A restart would roll it back safely, but it would also pay for the
  merge a second time.
- **Anything else:** stop now. A lane that is still building is recoverable
  from its branch and its recovery patch, and one that has just been
  dispatched has barely spent anything.
- **Your own unfinished edit** on any branch: commit it with a message
  starting `wip:` and push it. Work that exists only in a worktree is work
  the next session can't see.

Say the plan in one line per run, then do it without waiting to be asked.
The user asked you to park, and parking is the authorization.

### 3. Stop everything, and prove it

Kill by pid, never by pattern. Killing the runner does not kill its lanes,
because every lane is its own `claude` process with its own shells, MCP
servers and `caffeinate`.

```bash
kill <auto.mjs pid> <wave.mjs pid>
lsof -a -d cwd | grep <epic worktree or ~/.afk-claude/worktrees/...>   # lane processes, found by cwd
kill <each lane pid>
```

Then check again with the same `lsof` and `ps` commands. `kill -0`
reporting "dead" from a sandboxed shell is not proof; if `lsof` still shows
the process, escalate to an unsandboxed `kill -9`. Stop your own timers and
monitors too, and check each stop took. A stop that answers "no task found"
means the handle was already gone, not that the process is.

**Done when** `ps` and `lsof` show nothing belonging to these runs, and none
of your own timers or monitors is still armed.

### 4. Pin a resume note to each epic's PR

Post it as a PR comment, because `afk` re-renders the PR body and wipes
anything written there. Use this shape:

```markdown
## Parked <YYYY-MM-DD HH:MM> — <reason: quota / end of day>

**State:** <lifecycle> · passed <n> · in flight when parked <ids> · gated <ids>
**Stopped at:** <the step you were on, e.g. "Phase 6 step 4, fix pass not started">
**Owed by the human:** <gates to accept with the filled-in command, rulings, merges> or "nothing"
**Resume:**
    cd <main checkout> && afk epic <n> --base=<base> --worktree
**Then:** <the next one or two actions, named>
```

Read each one back (`gh pr view <pr> --json comments --jq '.comments[-1].url'`).

### 5. Report

Give one line per run with its resume note's URL, then the whole of
**Owed by the human** across all runs as a single list. End with the one
thing to paste when the quota is back: `/coduo-afk-park resume`.

## Resume

1. Find the notes: the latest "Parked" comment on each open epic PR
   (`gh pr list --search "Parked in:comments" --state open`), or the message
   the user pasted.
2. Before restarting anything, `git fetch` and compare each epic branch with
   its remote, and read `afk status`. A parked run can be touched in between:
   the user may have accepted a gate or merged something by hand.
3. Run each note's **Resume** command from the **main checkout**, never from
   inside the epic worktree. `--worktree` names its worktree after the directory
   it runs from, so running it from inside the worktree creates a second,
   nested run instead of resuming the first. Go one epic at a time, waiting for each
   baseline to finish before starting the next. That is the same stagger as
   `coduo-afk`, for the same reason.
4. From here, `coduo-afk` takes over: arm the 30-minute check-in, and carry
   on with the note's **Then**.

**Done when** each parked run is either running again with a check-in armed,
or named as waiting on the human for the thing its note says.
