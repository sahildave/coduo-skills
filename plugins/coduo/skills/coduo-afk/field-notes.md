# AFK runner field notes

Lessons from watching the runner work, not from reading its docs. They apply to any repo the
runner drives. SKILL.md already carries the `--base` / `--worktree` / `run_in_background`
launch rules and the PR-comment-not-body rule; this file holds everything else.

## Launching a run

- **Say at launch when a lane will drive the screen, and make sure it lets go.** A lane
  whose ticket changes a screen proves it with screenshots, and on a desktop app that means
  `agent-device` running an XCUITest runner that takes over the owner's mouse and windows.
  On atlas #1012 (2026-10-03) it started mid-run with no warning and the owner thought their
  screens had been hijacked. Automation is allowed; the surprise is not. In the launch
  report, name every task that touches UI and say "expect the screen to be driven while
  #N verifies". Then watch for the leftovers: the `agent-device` daemon (ppid 1, cwd in the
  lane worktree) and its `AgentDeviceRunner*.app` outlive the command that started them.
  They survive a failed attempt too: on #1012 attempt 1 failed, `agent-device session list`
  showed no session, and the XCUITest runner still held automation mode until killed. After
  EVERY attempt ends (a retry starts its own), `ps` for `agent-device|AgentDeviceRunner|
  xcodebuild test` and stop any whose builder is gone.

- **Never pipe a long-running `afk` command through `tail` in a background job.** The pipe
  buffers until the process exits, so you get nothing until it is over. Let it write plainly
  and read `.afk/agent-auto.log` for live state.
- **Commit a config edit the moment you make it.** `cliEpic`'s preflight requires a clean tree,
  so an uncommitted `.afk-setup/` aborts a resume AFTER the branch is cut and the plan review
  is paid for — and an uncommitted value never reaches the lane worktrees either.
- **`maxParallel` and the rest of `.afk-setup/config.yaml` are read ONCE, at process start.**
  `auto.mjs` captures the config object and the scheduler loop reuses it every tick, so
  editing the YAML mid-run changes nothing. Raising it takes effect on the next `afk epic`.

- **Pre-install every dependency on the base branch, and say so before the run starts.**
  `package.json` and the lockfiles are on the runner's protected list, so a lane's edit
  to `dependencies` is reverted after it runs and `checksInvalidatedBy` treats the
  revert as invalidating that lane's green. **No lane can install a package.** An epic
  that needs a new SDK therefore fails at the first lane that reaches for it, with an
  error that never names the missing dependency. Read every epic's children for packages
  the repo does not have yet, and offer the install list to the user **before** launching
  — this is the check to run at the same moment as `--base=` and the gate list, not after
  a lane dies.
  Two refinements learned the hard way:
  - **Install per wave, not all at once.** A native SDK installed months before the epic
    that wires it is dead weight that still has to build: voice-studio carried
    `react-native-purchases@^10.7.0` imported by nothing but a comment, for an epic that
    had since switched provider to Superwall. Install what the next wave needs, then run.
  - **Check the lockfile name against the protected list.** It names `bun.lockb`; a repo
    on bun's newer text `bun.lock` is unprotected, so `bun install` in a lane commits a
    lockfile change while the matching `package.json` change is reverted — a lockfile
    referencing a dependency the manifest does not declare, discovered at integration.
- **Installing does not unblock the epic.** Dependencies, a `gate: before` root, an
  external epic in another repo, and a cross-repo ticket are four independent blockers
  and clearing one says nothing about the others. Report them as a list, not as "ready".

- **`git fetch && git log HEAD..origin/main` before auditing anything, and read what the
  new commits touched.** An epic's worktree or feature branch is routinely behind `main`
  by exactly the commits that did the preparatory work, so a documentation sweep run
  from it reports every gap as missing when `main` already fixed it. This cost a whole
  pass on voice-studio: two commits named "First/Second pass of backend tickets" sat on
  `main` carrying five ADRs, a 563-line architecture baseline and epic joins on sixteen
  flow-map cards, and the sweep — run from a branch cut before them — reported all of it
  absent, "corrected" two ADR citations that were right, and mirrored another repo's
  ADRs into a colliding namespace. The commits were visible in the session's opening
  `git log`; nobody opened them.
  The tell is that findings cluster in one file type. Code-derived and tracker-derived
  findings survived that pass untouched, because `main`'s commits were docs-only. When a
  sweep says a whole documentation axis is missing, check the branch before believing it.

## State, worktrees and restarts

- **`.afk/state.json` holds one epic.** Archive it, plus `runs/`, `verifier/`, `recovery/`,
  `supervisor/` and `plan-review/`, to `.afk/archive/epic-<id>/` before starting the next epic
  in the same workspace. The same applies when you reshape the epic you are already running:
  adding or removing a task in the `afk:` block makes the runner refuse ("the epic's graph has
  changed since this run started"). Archive the state and relaunch; no lane has to be lost if
  none had started.
- **`--worktree` also gives the epic its own `.afk/`, dashboard and integrator**, so the
  one-epic lock does not apply. Prefer it to hand-rolling a worktree.
  *Supersedes the older note that "herdr forbids a per-epic worktree."* Epic #391 ran to
  completion under `runtime: herdr` from a hand-made worktree, and the flag is in `afk`'s own
  help. Treat the old claim as stale, not as a rule — but if you see herdr misbehave with a
  per-epic worktree, that note was written for a reason.
- **To re-run ONE task after an epic has closed, `afk reset <id>` and a relaunch are enough.**
  Do not hand-edit `epicClose` in `state.json`. The Runner reopens the close record itself
  (`reopenIfWorkResumed` in `scripts/auto.mjs`) once a task is runnable again, and logs
  `the epic has runnable work again; reopening the closed epic record.` The superseded close
  is kept under `epicClose.history`. A relaunch archives `.afk/` only when the epic id differs,
  so siblings already merged are not re-run. *Supersedes the older note that `epicClose` must
  be hand-set to `open`* (corrected 2026-10-07, Riverbend #109).
- **If you fixed a lane branch by hand after its builder finished, `afk reset` throws the fix
  away.** The restart path integrates a lane only when its branch tip carries a verification
  note, and your fix commit has none, so reset starts a new builder. Commit the fix on the
  lane branch, then run `afk salvage <id>` (afk-claude #209): it re-runs the lane's checks at
  the tip, writes a fresh note there and marks the task ready to integrate; then relaunch.
  Never copy the builder's note onto your fix by hand: it records checks your fix never met.
- **After a run, diff the local branch against its remote** before trusting a fix you committed
  mid-run. Lane integration rebuilds the branch and can silently drop a local commit, leaving
  the bad config back in the working tree while the remote still has the fix.
- **Never link a shared build cache** (`src-tauri/target`, `.next`, `.turbo`) into lane
  worktrees via `worktreeSetup.link`. One lane cleaning it destroys the main checkout's cache
  and kills the runner mid-integration, and a `.gitignore` entry like `/target/` matches a
  directory but NOT a symlink of the same name — so the link gets committed onto a task branch
  and breaks every later merge. Let lanes pay their own compile. Linking `node_modules` is
  fine for a webpack or Vite repo and **wrong for any repo that runs Turbopack's
  `next build`**: it rejects the symlink ("Symlink [project]/node_modules is invalid, it
  points out of the filesystem root"), even one into the repo's own parent. Those repos
  put a real install (`pnpm install --offline --frozen-lockfile`) under
  `worktreeSetup.run`, as Harbour does. Confirmed twice on 2026-09-21.

## Writing the epic and its children

- **The semantic plan review is an LLM agent and is not deterministic.** The same epic body
  passed clean and was then refused with two contradictions four minutes later. Treat a ✓ as
  one sample, not as proof that the epic is coherent — and read a refusal against the child
  issues yourself before reshaping anything, because it is often right.
- **Reconcile the epic's Owns list against every child's own Allowed paths before running.**
  They are two lists maintained separately and they drift. The plan reviewer catches some
  mismatches and misses others: it flagged a missing test file, and missed that a task's
  criterion was about what a component *renders* while that component sat in a sibling epic's
  territory. A lane set up that way cannot satisfy its criteria whatever the reviewer says.
- **Children claiming glob paths (`src-tauri/**`) silently swallow their siblings' files.**
  Per-task scope is advisory and unchecked across lanes, so this surfaces as a 3am merge
  conflict, never as a refusal to schedule. Narrow every child to named files at ticket time,
  and sequence the one that shares `locales/*.json` or a command-registration file behind the
  others rather than trusting concurrent edits to merge.
- **`afk ledger add --type=decision --applies-to=<id>` is how a human decision reaches a lane
  prompt.** It survives into the closeout verifier's reasoning too — it cited the entry when
  escalating a design question to a human instead of rubber-stamping it. The ledger is
  git-tracked despite `.afk/` being ignored, so commit it before the run.
- **Size a build ticket in gate passes, not files, and keep the whole suite out of its
  criteria.** Harbour epic #429 (2026-09-29) moved every Board URL from `/github/` to `/b/`.
  The epic guessed "about 136 files"; `git grep` finds 162, and the lane re-recorded 110
  baselines on top: 316 files in one ticket, #432. Writing it took 4–8 minutes both
  attempts. The clock went on gate passes: #432's criteria said "the e2e suite passes", so
  the lane ran the ten-minute browser suite itself, on top of `defaultChecks`, at every
  self-check. Attempt 1 finished in 18 minutes and lost to one load-sensitive test, and the
  retry discarded that worktree and started clean. Attempt 2 spent 44 minutes in self-check,
  re-running the suite and fixing a real 500 its new swap route threw under two concurrent
  cold requests in `next dev`, until the 60-minute `agent.timeoutMs` killed it uncommitted.
  Name the spec files a lane runs, never the whole suite: `baselineChecks` runs that at
  integration anyway. When a sweep won't fit three gate passes in half the clock, split it so
  each ticket leaves the suite green on its own: the smallest behaviour change with the
  baselines it moves first, behaviour-neutral sweeps next, the lint guard last. A final
  "specs and baselines" ticket fails every earlier ticket at integration. `coduo-tickets`
  carries the rule.
- **Prove the base is green under load before launching.** The same epic stopped four times
  in its baseline on three flaky tests already on `main`: two browser specs (fixed in #444),
  then a support round-trip test that boots the emulated stack and a Chromium inside
  `vitest run`. That one passes alone in 11 seconds and fails under full-suite load: it
  passed the 07:09 baseline, failed at 07:34 on the same commit inside the lane, and failed
  again at 09:17. The lane sandbox skips it, so a lane cannot reproduce the runner failing
  it. Run the baseline gates twice on the base alongside a second heavy job before the first
  launch, and fix what flakes before the epic starts, not during it.

## `passed` is not `done` — the three ways green lies

- **Write acceptance criteria a lane cannot satisfy by prose.** #169 said duplication must be
  "accepted with a stated reason **or avoided by design**"; the lane took the second branch,
  shipped a comment-only diff plus a test pinning the bug as correct, and passed every gate
  honestly. Require something mechanical — a non-comment diff in the named file, or a test
  that must **fail against HEAD before the change**. An `or` in a criterion is an escape hatch,
  and a well-behaved agent will use it.
- **A child ticket with no `## Acceptance criteria` section makes the closeout verifier
  diff-only.** It says so itself, then reviews the code against itself with nothing to check it
  against. Epic #371's spec axis only found the unimplemented criterion because a second
  reviewer read the issue prose by hand. Write the section into every child, in
  `coduo-tickets`, not after.
- **Every gate can pass over a control that is wired to nothing.** #365 shipped a settings
  toggle whose resolver had zero non-test callers: it persisted, it was unit-tested, and it
  reached no run. When a lane adds an exported function, grep it for non-test callers before
  believing `passed`.

## Re-running a ticket a lane declined

Three things, in this order:

1. **Revert the lane's artifacts off the branch first.** Its JSDoc and doc paragraphs are the
   house position the next lane reads, and removing them matters more than the ticket edit.
2. **Rewrite the criteria to be checkable** (see above).
3. **Quote the lane's objection in the ticket and overrule it explicitly.** The reasoning is
   usually good, and an agent acts on a good reason unless told it was already weighed.

## Reading a failure

- **A failed baseline gate does not log which test failed.** `.afk/agent-auto.log` captured
  cargo's compile lines and `error: test failed` and nothing between. Re-run the command
  yourself before theorising — four reruns passed, so it was not breakage.
- **A red baseline has THREE explanations, and the usual tiebreaker cannot separate two of
  them.** Regression, flake, or **CPU contention**. "The casualty set shifts between
  attempts" is the standard test for flake-not-regression, but contention shifts it too —
  and the fix is completely different: change nothing in the repo, just stop running two
  heavy things at once. The tell is the failure *shape*: `waitFor` timeouts, components
  rendering empty, `Test timed out in 5000ms`. Starvation, not breakage. The
  discriminator that works is boring — run the suite once on an **idle** machine. Green
  idle plus red under load is contention. One green run is luck; two is a finding.
  atlas 2026-09-08: launching two epics thirty seconds apart put two `rust:clippy` builds
  and two full 613-file jsdom suites on one laptop, load average **47**; the baselines
  reported 4 and 95 failing files against the same base commit, and the base was green
  (613/613, 8192 tests) both times it was measured alone.
- **Stagger epic launches; never run your own test suite while a gate is running.** A
  baseline is a whole-machine load spike, so two of them collide by construction. Lanes
  may overlap once running — disjoint file surfaces are fine — but baselines and any
  full-suite gate must not. And the diagnosing agent is a competing load like any other:
  on that same night, the retry of a single-lane gate release failed because *isolation
  tests run to diagnose the first failure* were still going. The measurement destroyed
  the thing it measured, and the resulting one-file casualty set briefly read as new
  evidence. While a gate runs, restrict yourself to `afk status`, `tail` and `gh`.
- **Nothing reconciles `max_parallel` across concurrent epics.** It is per-epic and read
  once at process start. Two epics allowing 3 and 5 lanes means up to eight lanes each
  running the project's full gate set on one machine. Add them up before launching, and
  remember that lowering the number needs a relaunch.
- **Read the token counters before theorising about a lane failure.**
  `runs/<id>/verification.json` carries `tokens` and `producedFiles`. Zero tokens and no files
  means the agent never reached the API, so nothing it "failed" is about the ticket. Any check
  failure in that report ran against an unmodified tree and is noise. Sibling-lane load is the
  explanation to reach for LAST: it was wrong on Lumina #35, where the cause was herdr killing
  agent processes.
- **Under herdr, the integrator can kill a live builder.** `parent workspace <id> rebuilt for
  the integrator` was immediately followed by `lane 37 agent process died`, losing an agent
  that had already written its files and spent 12k output tokens. Two deaths in a row tripped
  the circuit breaker on a ticket that then passed in three minutes untouched after
  `afk reset`. A lane that dies this way is worth one clean retry before you touch the ticket.
- **A live lane stuck on a never-exiting command can be steered through its Herdr pane.**
  There is no runner channel into a running builder (the ledger reaches prompts only at
  dispatch), but the builder is a claude TUI: text pasted into its pane queues and is read
  when the blocking tool call returns. Proven on atlas #428, hung on the interactive
  `e2e:web` harness: paste the guidance FIRST (name the ruling and the expected exit
  semantics), THEN kill the blocking child processes — found by cwd via lsof, never by
  command-line grep. The builder reads the exit code and the guidance together. Either half
  alone fails: a kill without queued guidance gets misread as a gate failure; guidance
  without the kill never arrives.

## Reviews and closeouts

- **When a verifier reports `unparseable`, `inconclusive`, or "0 of N criteria met", the review
  almost certainly ran.** Read `.afk/verifier/<id>/stream.jsonl` (search back for the last
  fenced report block) and the supervisor's `decision.json` before believing it. The harness
  harvests the agent's *final* message, so a stale timer waking it after it answers replaces
  the report with small talk. An empty report reads as clean and is posted to the epic issue as
  if it were a review.
- **`afk finish` prints the closeout already on disk — history, not state.** On #391 it had run
  hours and eight commits earlier and reported a blocker long since deleted, and its verifier
  could run **zero of six gates** ("no node_modules in this disposable checkout"), so its
  verdicts rested on reading source. Re-verify before quoting it to anyone. `pruned 0 lane(s)`
  is normal — the runner removes lane worktrees at integration.
- **The runner does not post lane closing reports to their issues.** On atlas #409's
  acceptance run, all four passing lanes left their reports in `.afk/runs/<task>/` and the
  tracker showed only pre-run comments — so a lane's deferral lists and rulings have NO
  public record until somebody posts one. "Deferral needs a ticket" silently fails when the
  enumeration was never public. At each wave boundary, check `gh issue view <n> --json
  comments` for the lanes that passed and post the substantive parts (deferrals, rulings,
  sanctioned copied-file edits) as an issue comment yourself.
- **A sub-agent that stops "waiting for X" with no live background children is stalled, not
  waiting.** Completion notifications fire only when the agent has no live children, so that
  final message is self-contradictory — it backgrounded its own long command and lost the
  handle. Nudge it with one instruction: run long commands in the FOREGROUND of its own turn
  (5-7 minutes is fine), never backgrounded, never sleep-polled. Put that line in any brief
  whose verification includes full-suite runs.
- **A fixed finding comes back unless its lesson is a rule.** Harbour's audit
  (`docs/agents/lesson-rules-audit.md`, #414) found repeats were the norm: an ungated Board
  Server Action was fixed three times (4921fb5, #338, #344), each fix testing only its own
  site, and a `"use cache"` with no `cacheTag` found at #191 served a privatised repo's
  content for a week from a second site. A rule written at the first occurrence fired on
  every later one. Two traps in writing it:
  - **ESLint `no-restricted-syntax` entries in different config blocks replace each other
    silently**; options never merge, so the first replay lost two of three lessons on every
    `.ts` file. Give each lesson its own rule under a local plugin (`eslint.lessons.mjs`).
  - **A rule with no red/green fixtures is a loophole.** A lane that hits it can narrow the
    matcher or widen its ignores and pass its gate. The red fixture (pre-fix code, must
    fire) run by the repo's suite is what turns that loosening red.
- **Prepping a human gate: drive the Release artifact to the first credential prompt.**
  Riverbend #74 (Account hardening) passed every gate and its closeout, then its
  `gate: after` #79 caught a crash on the first Sign In click: the
  `ASWebAuthenticationSession` completion ran off-main inside a `@MainActor` type (a Swift 6
  isolation trap) and died in `_startDryRun`, before any credential sheet opened. The tests
  faked web sign-in. The gate-prep agent, briefed "do not sign in", stopped one click short
  and handed the owner a crash. Prep a human gate as soon as its blockers merge: build the
  Release artifact, drive the flow up to the first credential, payment or system-setting
  prompt, enter nothing, and capture what you saw. Fixed in riverbend `c6ef049`.

## Wave mode (`afk wave run`) — quillnote v1 night, 2026-09-03

- **Kill a wave driver by pid, never by pattern.** `pkill -f "afk wave run"` matches the
  thin `afk` wrapper but NOT its `wave.mjs run tasks/` child, which survives orphaned and
  keeps scheduling into the same `.afk` — two drivers restoring `main` under each other's
  mergers presents as "merger produced no commit / exited 1 with empty output". Find
  `wave.mjs` and `auto.mjs --dag` pids, kill those, and re-`ps` each one dead.
- **Teardown order is worktree → prune → branch.** `git branch -D wave-NN` silently fails
  (with stderr suppressed) while any worktree holds the branch; the next launch then reuses
  the stale branch at the old base and every integration fails against it. Verify with
  `git branch | grep wave-` after, not by trusting the delete.
- **Any commit to the base mid-wave strands the wave** — the fast-forward requires base to
  be an ancestor of the wave branch. Corollaries: (a) a fix committed after launch never
  reaches a recorded wave (it replays from its recorded sha) — wipe the zero-work wave
  record and relaunch instead of resuming; (b) a task DEAD after 3 failed attempts IS
  terminal — the wave fast-forwards its passed siblings past a stuck task, so exhausting
  a hopeless lane's attempts is a legitimate way to unstick a wave without touching state.
- **A partial `.afk-setup/config.yaml` is worse than none.** Its presence overrides the
  built-in defaults wholesale: an agent-runtime-only file kills `defaultChecks` (loader
  refuses all tasks as unverifiable) and drops `maxParallel` to 1 silently. Write the full
  file — defaultChecks, agent.runtime, maxParallel — or none.
- **Check `tasks-todo/` for lane-authored files at every wave boundary.** A lane using the
  "unfinishable scope → write a new task file" escape hatch with `status: needs-human`
  refuses the WHOLE directory at the next wave cut, 37 seconds in, with no error naming the
  file (`afk wave validate` names it). Do the human fix on base, `git mv` the file to
  `tasks-done/`, normalize its status to `ready-for-agent` — the loader refuses any other
  status even in the done folder.
- **A test that executes AppleScript can summon a macOS TCC consent dialog, and an
  unattended run then blocks on a GUI prompt nobody is there to click.** This is the
  real shape of the 6-hour baseline stall: a closeout-authored test ran `NSAppleScript`
  inside `swift test`, macOS raised an Allow prompt (the owner found it on waking), and the
  suite sat behind it before failing with errOSAInvalidID (-1751). Two rules fall out:
  tests in an unattended repo must never execute OSA/Apple Events — prove scripting
  through a sending seam, execute nothing (quillnote task-11 had this rule; the closeout
  test broke it) — and any suite that must touch NSAppleScript at all runs `.serialized`
  on the main actor (OpenScripting also races under the parallel runner: full suite red,
  filtered green). Closeout fix commits land AFTER the wave's gates ran — they are the
  least-reviewed code on the branch and the first place to look when the next wave's
  baseline goes red or hangs.
- **Untrack `Package.resolved` in a repo built by both SPM and an xcodegen project.**
  xcodebuild's `originHash` is worktree-path-dependent (three fresh resolutions, three
  hashes, identical pins), so no committed version survives an integration worktree's
  dirty-tree gate. Salvaged task branches that committed lockfile changes then need a
  drop-the-lockfile commit or every merge hits modify/delete.
- **Launch and resume from the base-branch checkout.** The driver refuses any other
  checkout, and the session shell's cwd resets between commands — `cd <worktree> &&` on
  every `afk wave run`, not once.
- **Salvage is real:** builder branches (`afk/task-*`) survive state wipes and the runner
  re-integrates finished builds instead of rebuilding (`recoveredFrom`). Keep those
  branches when wiping wave state.
- **Wave merger panes carry the wave-level workspace label** and restarts multiply
  identical parents (` - 1`, ` - 2`) — filed as afk-claude#51; until fixed, don't close
  suffixed GOAL workspaces mid-run, they are the live merger pane pool.
- **A `blocked` task fails the whole wave, and the ledger outranks `tasks-done/`.** Wave-03
  here: 8 of 8 real tasks merged and verified, one no-op task `blocked` → wave `failed`,
  no fast-forward, driver idle, herdr silent. Landing by hand is safe and reproducible
  (kill drivers by pid → verify merges → `merge --ff-only` → file passed tasks to
  tasks-done → ledger record `merged`+headSha → fix the digest), BUT a non-`passed` task
  outcome in a merged wave's ledger record re-schedules that task into every later wave
  even from `tasks-done/` — set it to `passed` in `.wave-log.json` or the next wave loops
  on it. The stronger form: NO record also reads as pending, so every task a closeout
  fixer authors AND completes is a ghost by construction (task-20-license-gate-wiring,
  re-scheduled two waves later). At any boundary where a closeout filed completed tasks,
  diff `tasks-done/` against the ledger and record the missing ones `passed` before the
  next cut. afk-claude#54.
- **Root-level composition files accrete owners; the late task pays.** A panel/app
  root view or AppDelegate ends up in many tasks' `owns` (PanelRootView: five tasks,
  three waves). The collision cost lands asymmetrically on tasks authored mid-run
  (closeout deferrals especially): with no edges to prior owners, `afk wave validate`
  refuses the directory but the driver's cut silently DROPS the task instead. Fix at
  authoring: sole owner or generated file. Fix mid-run: give the new task `blocked_by`
  on every prior owner of its files — satisfied edges are free. Now in coduo-tasks
  Phase 3.
- **Killing the wave driver does not kill its lanes.** Builders, their shells, `caffeinate`
  and per-lane MCP servers survive every driver pid's death; nothing records lane pids, so
  find them with `lsof -a -d cwd | grep <wave>` — never by command-line grep. And a
  SIGTERM from a sandboxed shell can fail with EPERM while `kill -0` reads as "dead":
  verify with `lsof` again, not with kill, and escalate to an unsandboxed SIGKILL.
  afk-claude#55.
- **`--dangerously-skip-permissions` does not silence the desktop app's safety layer.**
  Lanes running the Claude app's binary can still raise classifier escalations, and with
  Remote Control connected those land on the human's PHONE mid-AFK-run (quillnote: task-06
  attempt 1, task-19's manifest-revert demo). The run then waits on a sleeping human.
  Until afk-claude#53 lands (route lane prompts to the supervisor via
  `--permission-prompt-tool`; time out into a failed attempt), treat an unexplained stalled
  lane as possibly parked on a phone prompt — check the phone before theorising.

## Walkthrough fixes stale the acceptance review

`--accept` on a `gate: after` task checks that the newest closeout review read the branch
head, with only the runner's status commits on top (`reviewIsCurrent`, auto.mjs ~1515,
~1623). Fixes committed to the epic branch by hand during the owner's walkthrough break
that, and the accept refuses. Re-run `afk epic <n> --base=<base> --worktree` without
`--accept`: it reviews the head, runs the fix pass and parks on the gate; then accept.
`afk verify` does not count, since it never writes `close.verifier`. On #1137 (2026-10-11)
18 walkthrough commits plus a staging merge made the accept refuse; the owner chose
`--force` because independent reviews already covered most of the new commits.

## Held proposals — reopen on a second project

Two debates on 2026-10-15 held three proposals until a second project shows the same
defect. If you hit one of these triggers, reopen the proposal; don't re-argue it from scratch.

- **Startup-path test per live component** (coduo-tickets). A ticket that adds a live
  component gets one test that starts the real app with only network and storage swapped.
  Held: only Riverbend showed it; its wrong wiring stayed invisible because every test
  injects the environment (Riverbend 1e16633, 444699a). Reopen when a closeout or human
  gate in another repo finds wiring that every test passed.
- **Freeze notes become tickets** (coduo-product-prototype). Every "wrong / rebuild later"
  line in a frozen prototype's FREEZE or HANDOFF becomes a ticket in the same change.
  Held: one instance (Riverbend SilverFill, states.json:27, now riverbend#139).
  Reopen on a second freeze note with no ticket.
- **Preflight path and symbol probe** (runner). Before launch, check that every path and
  symbol a ticket names exists on the base. Held: it is runner work. Reopen when a lane
  fails on a path or symbol the ticket named that did not exist.

Source: `riverbend` `docs/product/afk-ways-of-working/discussion.md` (PR #137).
