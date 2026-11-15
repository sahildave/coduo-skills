# Acceptance criteria a lane can meet

A criterion is satisfied by a builder in a lane, alone, with no human and no
live services. `afk validate` refuses some shapes; the rest are yours to catch.

## Refused by `afk validate`

Each applies to lines inside `## Acceptance criteria` (or `**Done when**`).
The same line elsewhere in the body is a warning.

- **A protected path** (`unsatisfiable_criterion`). The runner reverts lane
  edits to lockfiles, `AGENTS.md`, `docs/progress.md` and `.afk-setup/`. Name
  them in prose if you need to point at them; a criterion requiring an edit to
  one can never pass. `protectedEdits` in the config is the owner's way to
  allow one.
- **A person** (`human_in_criteria`). "Ask the owner", "sign-off", "wait for
  the human", "approved by". Make the task `gate: before` or `gate: after`, or
  say what the lane does instead ("any pixel change fails the lane"). Gated
  tasks are not checked.
- **The whole suite** (`whole_suite_in_criteria`). `check:all`, `test:all`,
  "the e2e suite passes", "all tests pass", or a `baselineChecks` command that
  is not in `defaultChecks`. The integrator runs the whole suite at every
  merge, and a lane that runs it too spends its clock on it. Name the spec
  files the change adds or re-records. For a cross-platform consumer, either
  name the touched suites (for `xcodebuild`, `-only-testing:<Target>/<Suite>`
  before `test`), or put the platform's whole-suite command in a
  `## Platform gate` section outside the criteria and write "the gate in
  `## Platform gate` passes". `## Platform gate` is a convention; the runner
  does not read it.

Warned, not refused: a bullet with "or" in it (`criterion_escape_hatch`). The
lane will take the cheaper branch. Say which one you mean, or name something
the diff must show.

## Yours to check

- **Evidence is a committed file on the branch**: a test, a fixture, a doc.
  The closeout reads the branch, so a criterion that cites the lane report,
  the PR body or pasted output ends `unknown` every run.
- **A live service, a secret, hardware or the owner** goes on a gate ticket,
  not a lane ticket.
- **A named command is one a gate runs**: in `defaultChecks` or
  `integrationChecks` in `.afk-setup/config.yaml`, or in the task's
  `checks:`. A command no gate runs is never verified.
- **A new test is wired in.** `package.json`'s `scripts` block is open to
  builders, so "a new `scripts/test-<area>.ts`, appended to the `test` chain"
  is a fair criterion. A test file no chain names never runs.
- **Assert a presence.** "`grep …` prints nothing" also passes when the task
  shipped nothing.
- **A check that cannot fail is not a check.** `agent-device diff screenshot`
  exits 0 on a failing pixel diff, so a pasted diff is supporting evidence,
  never the criterion.

## Screens and controls

- **A screen criterion is a picture**: a snapshot test the lane records. The
  snapshot library must already be on the base branch
  (`setup-coduo-toolchain`), since a lane cannot change dependency
  manifests. A snapshot proves the screen did not change, not that it is
  right, and a token `grep` proves a token is referenced, not seen.
- **A design criterion names its board** under `docs/design/` and asks the
  report for an inventory: every element the board draws, present or absent,
  and every element the app draws that the board does not, each extra
  removed or ticketed. The extras list is what no grep produces. Where the
  repo can check it, one falsifiable sentence judged against the board ("the
  banner draws exactly two buttons, Re-push and Stop Mirroring") in `checks`
  is stronger. Keep the inventory beside it.
- **A control criterion is a state change.** A drawn button wired to an empty
  closure passes the snapshot and the accessibility tree. Drive the built
  app and assert the state moved (`agent-device click <target> --settle`,
  then `wait text` or `is` on the result, or an XCUITest). The fallback a
  lane can always run: the handler has a non-test call site, shown by
  `grep -n <handler>`.
- **Lock the environment before recording baselines.** Appearance, locale,
  timezone, clock and display scale all reach the renderer. A child that
  records its own baseline in an unpinned environment can record the bug as
  the expected result. Land the lock on the base first
  (`setup-coduo-toolchain`); if it has to ship in this epic, it is a
  depth-0 ticket every screen child depends on, split for reason 2.
