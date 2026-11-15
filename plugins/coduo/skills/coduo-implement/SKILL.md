---
name: coduo-implement
description: "Implement a spec or a set of tickets, in an interactive session or an AFK implementer lane. Use instead of `implement`. Adds checks that the result works for a user: experience criteria, no dropped data, no silent stubs, verification shown with real output, and a lesson for every fix."
disable-model-invocation: false
---

In an AFK lane the lane prompt wins over this skill. You do not commit,
spawn sub-agents, run `/code-review` or write to the tracker. What this skill
says to post or ask goes in your report.

## Before code

1. **Write the experience criteria.** Each is something a user sees or does,
   checked by running the app: "while the agent edits a file, I can read the
   diff", not "a tool call shows a status". If the ticket has none, derive
   them from its intent and put them in the report.
2. **Bound resource words.** Where the ticket says persisted, streamed,
   queued, cached or history, write how often and how much. Left unbounded,
   "persisted as it progresses" becomes a full write per chunk.
3. **Pick a side of every "or"** in a criterion and say which, so the easier
   branch is a choice and not a default.

## While building

4. Work test-first with `tdd` where a test can reach the behaviour. In a
   lane nobody confirms the seams, so choose them and name them in the
   report.
5. **Account for every field** of an event or payload you handle. Name the
   ones you drop and why, or data arrives and is thrown away unseen.
6. **No silent stubs.** Code that claims behaviour it lacks (logs only,
   `return null`, drops its payload) is finished now, or named in the report
   (interactive: with its ticket). Later tickets build on a stub as if it worked.
7. **Copy a working reference** when one exists in the repo, rewire it, and
   report the delta. A rewrite from a description loses what made it
   work.
8. **A missing shared instance is an error.** If a lookup of an app-wide
   store, client or environment fails, throw. A private fallback copy is
   never started, so the feature runs against nothing while gates pass.

## Verify

9. **Show red, then green.** Paste real output of the test failing without
   the change and passing with it. If you reverted to get red, check with
   `git diff` that the revert took; a red run with the green run's counts
   tested the fixed code.
10. **Run the app**, or the closest runnable surface, against each experience
    criterion and report what you saw. Click every control you added and
    report what changed, because an empty handler still draws an enabled
    button. If the ticket cites a design board, list what the board has that
    the build lacks, and what the build has that the board lacks. If nothing
    can run, say so; the diff is not a substitute.
11. **UI change: capture before and after**, one screenshot per changed
    screen. Read `references/evidence.md` for where they go and the PR table.
12. **A fix ends in a lesson**, at the highest level that works:
    `structure` (make the mistake impossible to write), `rule` (a lint rule
    with a red fixture), `test`, `standard` (one line in the coding
    standards), or `none` with a reason a reviewer could overrule. Search the
    coding standards, `AGENTS.md` and the lessons home first: a mistake
    already written down moves up a level, since the prose did not stop it. Read `references/lessons.md` for the recipe.

## Finish

Interactive: run the full suite once and `/code-review`, commit the fix,
then commit each `structure` or `rule` lesson on its own (`lesson: <id>`), so
reverting the fix leaves the guard.

AFK lane: run only the required checks, write the report, and stop. If the
lane prompt asks for a `LESSON:` line, use its format. It knows only `rule`,
`standard` and `none`, so write `structure` or `test` as
`none:"structure: <what, where>"` or `none:"test: <name>"`.
