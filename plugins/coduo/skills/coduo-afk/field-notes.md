# AFK runner field notes

Lessons from live runs that the runner's docs and guards do not cover. Before adding a note,
check `docs/failure-modes.md` in the runner: a row marked closed there needs no note here.
Remove a note when its row closes.

Contents:

1. Launching
2. State, worktrees and restarts
3. When `passed` is not done
4. Reading a failure
5. Reviews, closeouts and merges
6. Wave mode

## 1. Launching

- **A Mac app lane verifies UI in Atlas when it can.** If `atlas doctor` reports `ready`,
  brief the lane to open its build in Atlas's helper login (the `atlas` skill) and end with
  `atlas cleanup --apply`. Lanes share one helper, so many UI lanes run slower, but none
  touches the user's mouse. Atlas cannot do a drag-and-drop between apps (`coduo-mac-drag`,
  at the user's desk).
- **Without Atlas, say at launch which lanes will drive the screen.** `agent-device` runs an
  XCUITest runner that takes over the mouse and windows, and an unwarned takeover reads as a
  hijack. After every attempt ends, `ps` for `agent-device|AgentDeviceRunner|xcodebuild test`
  and stop any whose builder is gone: the daemon outlives the command, even a failed one.
- **Config is read once, at process start.** Editing `maxParallel` or anything else in
  `.afk-setup/config.yaml` mid-run changes nothing until the next `afk epic`.
- **Install dependencies per wave, on the base.** No lane can install (manifests and
  lockfiles are reverted). Install only what this epic needs: a native SDK installed months
  early still has to build, and the epic may switch provider before it runs.
- **Clearing one blocker does not unblock the epic.** A missing dependency, a `gate: before`
  root, an external epic and a cross-repo ticket are independent. Report them as a list.
- **Strip a pasted test addendum from a ticket before launch.** A lane's prompt is cut at
  dispatch and never re-reads the issue, so a fix after dispatch reaches no running lane.
- **`git fetch && git log HEAD..origin/<base>` before auditing anything.** An epic branch is
  often behind by exactly the commits that did the preparatory work. When an audit says a
  whole kind of file is missing, check the branch before believing it.
- **Prove the base is green under load.** `afk preflight --baseline` runs every
  `baselineChecks` command on the base. A test that passes alone and fails under full-suite
  load will fail inside the run too; fix it before launch.

## 2. State, worktrees and restarts

- **To re-run one task after an epic closed, `afk reset <id>` and relaunch.** The Runner
  reopens the close record itself. Do not hand-edit `epicClose` in `state.json`.
- **A lane branch you fixed by hand goes through `afk salvage`, not `afk reset`.** Reset
  starts a new builder and throws the fix away. Commit on the lane branch, run
  `afk salvage <id> --lesson=<lesson> --root=<epic checkout>`, then relaunch. Never copy the
  builder's verification note onto your commit.
- **After a run, diff the local branch against its remote** before trusting a fix you
  committed mid-run. Integration rebuilds the branch and can drop a local commit.
- **Never link a shared build cache** (`target`, `.next`, `.turbo`) into lanes through
  `worktreeSetup.link`. One lane cleaning it breaks the main checkout, and `/target/` in
  `.gitignore` does not match a symlink, so the link gets committed. Linking `node_modules`
  is fine for webpack or Vite and wrong for Turbopack's `next build`, which rejects the
  symlink: put a real install (`pnpm install --offline --frozen-lockfile`) under
  `worktreeSetup.run`.
- **Run `afk reset` and `afk salvage` with `--root=<epic checkout>`, one bare command each.**
  Both take `--root`, and the classifier has refused `cd … && afk salvage` as log tampering.
  The read-and-record verbs with no `--root` (`status`, `fate`, `close`) still need the `cd`.

## 3. When `passed` is not done

- **Write criteria a lane cannot satisfy with prose.** "Accepted with a reason or avoided by
  design" let a lane ship a comment-only diff. Require a non-comment diff in a named file, or
  a test that fails against HEAD before the change.
- **Every gate can pass over a control wired to nothing.** When a lane adds an exported
  function, grep for non-test callers before believing `passed`.
- **Prove an env-gated test both ways.** A new `skipIf` let a fix commit pass with the whole
  block skipped after an env var was renamed. Wrong config must fail, missing config may
  skip; report it as the escape hatch it is.
- **Re-running a ticket a lane declined:** revert the lane's doc and JSDoc artifacts off the
  branch first (the next lane reads them as the house position), rewrite the criteria to be
  checkable, then quote the lane's objection in the ticket and overrule it explicitly.

## 4. Reading a failure

- **Rerun a failed baseline command yourself before theorising.** The log may not name the
  failing test.
- **A red gate has three explanations: regression, flake, or CPU contention.** Contention
  also shifts the failing set between attempts. Its signs are `waitFor` timeouts, empty
  renders and `Test timed out in 5000ms`. Run once on an idle machine: green idle and red
  under load is contention, and the fix is to stop running two heavy things at once.
- **`max_parallel` is per epic.** Two epics at 3 and 5 lanes are eight lanes on one machine.
  Add them up before launching.
- **`blocked` or `failed` against `integration_failed`.** The first means the builder never
  produced a good branch. The second means the branch was good and the merge was not; the
  base was restored and the branch and worktree are kept (`docs/runbook.md` section 3).
- **A herdr lane stuck on a command that never exits can be steered through its pane.**
  Paste the guidance first (the ruling and the expected exit), then kill the blocking child
  processes, found by cwd with `lsof`. Either half alone fails.
- **A `webServer` timeout:** run `lsof -nP -iTCP:<port> -sTCP:LISTEN` on the ports the
  repo's e2e config derives from the checkout path before any relaunch. A squatter fails
  every relaunch from the same path.
- **"Port … already in use" from `test:stories`:** it binds 63315, so two story runs collide.
  That is a reset, not a ticket defect.
- **A baseline red on DNS:** Supabase's direct host is IPv6-only. If `getaddrinfo` says
  ENOTFOUND while `dig AAAA` and `curl -6` work, fix the network or use the IPv4 pooler URL.
- **The Runner dies removing a lane worktree after a good integration:** an earlier attempt
  left processes there (`vite`, a devtools Chrome). `lsof +D <worktree>`, kill them, remove
  the folder, `git worktree prune`, relaunch.
- **A screenshot that differs by about 1% and passes on retry:** raise that assertion's
  `maxDiffPixelRatio`. A difference the same size every run is a real change.
- **A sub-agent that stops "waiting for X" with no live children is stalled.** It
  backgrounded its own long command. Tell it to run long commands in the foreground of its
  turn, and put that line in any brief that runs a full suite.

## 5. Reviews, closeouts and merges

- **`afk finish` prints the closeout on disk, which is history.** It may predate later
  commits and rest on skipped gates. Re-verify before quoting it. `pruned 0 lane(s)` is
  normal.
- **The Runner does not post lane reports to their issues.** A lane's deferrals and rulings
  live in `.afk/runs/<task>/` and have no public record. At closeout, post the substantive
  parts on each child issue, rebuilt from the verifier's per-criterion verdicts and the task
  commit.
- **Verify a reviewer's hard claim with a grep before relaying it.** Two reviewers said no
  `READER_TOKEN` remained; the Playwright config still set it.
- **A fixed finding comes back unless its lesson is a rule.** Repeats are the norm: one
  ungated server action was fixed three times, each fix testing only its own site. Two traps:
  ESLint `no-restricted-syntax` entries in different config blocks replace each other, so
  give each lesson its own rule under a local plugin; and a rule without a red fixture can
  be loosened by the next lane without going red.
- **Hand commits during a walkthrough stale the acceptance review.** `--accept` then
  refuses. Relaunch without `--accept` (it reviews the head, runs the fix pass and parks),
  then accept. On a closed epic use `afk close --redo <n>`. `afk verify` does not count.
- **`docs/progress.md` conflicts on every second epic merge.** Each epic appends at the same
  spot. Merge the base into the branch keeping every block before handing over the merge.
- **Resolve every merge conflict with `/resolving-merge-conflicts`**, and name the skill in
  any merge brief. A brief that did not name it got hand-rolled text surgery.

## 6. Wave mode

`docs/wave-mode.md` is the reference.

- **Launch and resume from the base-branch checkout.** The driver refuses any other.
- **Stop a wave with `afk wave stop`, then check by cwd.** Lanes are separate processes;
  find survivors with `lsof -a -d cwd | grep <wave>`, never by command-line grep. A SIGTERM
  from a sandboxed shell can fail while `kill -0` reads as dead: re-check with `lsof`.
- **Teardown order is worktree, prune, branch.** `git branch -D wave-NN` fails quietly while
  a worktree holds it, and the next launch reuses the stale branch. Check with
  `git branch | grep wave-`.
- **A commit to the base mid-wave strands the wave**, because the fast-forward needs the base
  as an ancestor. A fix committed after launch never reaches a recorded wave: wipe that
  zero-work record and relaunch. A task dead after its attempts is terminal, and its passed
  siblings still land.
- **A partial `.afk-setup/config.yaml` is worse than none.** It replaces the defaults
  wholesale. Write `defaultChecks`, `agent.runtime` and `maxParallel`, or nothing.
- **Check `tasks-todo/` for lane-written files at every wave boundary.** A `needs-human` file
  refuses the whole directory at the next cut. `afk wave validate` names it. Fix on the base,
  `git mv` it to `tasks-done/` with status `ready-for-agent`.
- **Diff `tasks-done/` against `.wave-log.json` at each boundary.** A task with no `passed`
  record re-runs in every later wave, including tasks a closeout fixer wrote and finished.
  Use `afk wave accept <dir> <task-id>` for a blocked no-op.
- **Tests in an unattended repo never execute AppleScript.** It raises a macOS consent
  dialog nobody is there to click, and the suite hangs behind it. Prove scripting through a
  sending seam; a suite that must touch `NSAppleScript` runs `.serialized` on the main actor.
- **Untrack `Package.resolved` in a repo built by both SPM and xcodegen.** Its hash depends
  on the worktree path, so no committed copy survives the dirty-tree gate.
- **A root view or app delegate that many tasks own:** give a mid-run task `blocked_by` on
  every earlier owner of its files, or the driver's cut drops it.
