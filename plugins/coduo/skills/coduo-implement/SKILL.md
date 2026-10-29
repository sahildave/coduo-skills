---
name: coduo-implement
description: "Implement a spec or set of tickets. Replaces `implement` everywhere — interactive sessions and AFK implementor lanes alike. Layers the atlas agents post-mortem fidelity checks over `/implement`: experience criteria before code, bounded resource words, every payload field accounted for, every stub finished or ticketed, working references copied not rewritten, verification demonstrated not described, every fix ending in a lesson."
disable-model-invocation: false
---

Implement the work by following `/implement`, with the checks below layered on.
Each exists because a nine-day feature passed every gate and shipped unusable;
the failure history is atlas's
`docs/architecture/agents-replacement/10-postmortem.md` — read it only if a
check's reasoning is disputed, not to run this skill.

You may not be able to ask questions mid-task (AFK lanes cannot). Where a check
says "post on the ticket", the fallback is always: state it in your run report
instead. Never skip a check because the tracker is unreachable.

## Before writing code

1. **Experience criteria first.** The ticket must carry at least one criterion
   phrased as something a user sees or does — checkable by running the app,
   not by reading the diff. "A tool call shows as running, then settled" is a
   state-transition criterion: a title and a status dot passes it. "While the
   agent edits a file, I can read the diff it proposes" is an experience
   criterion. If the ticket has none, derive them from its intent, post them
   on the ticket, and implement against them. Done when every criterion you
   will verify against is written down somewhere the reviewer will see.
2. **Bound every resource word.** For each criterion or design line containing
   "persisted", "streamed", "queued", "cached" or "history", write the bound:
   how often, how much, how many. An unbounded "persisted as it progresses"
   became a full-transcript SQLite write per streamed chunk.
3. **Name your branch through any "or".** An "or" in a criterion is an escape
   hatch you will be tempted to take. Before starting, state which branch you
   are satisfying and why.

## While implementing

4. **Account for every field.** When handling an event, message or payload,
   enumerate the fields the upstream contract carries and state which ones you
   are not handling and why. A dropped field is a decision with a sentence
   attached. (The defect class this catches: data arrives and is thrown away.)
5. **A stub is a deferral; finish it or ticket it.** A stub is code that
   claims behaviour it does not perform: a function that only logs, a
   `return null` under `// #NNN`, a handler that drops its payload. Later
   tickets build on it believing the work is done. Implement it now, or file a
   ticket and name the stub in your report, with the ticket number in the same
   sentence. A follow-up earns a ticket only when it is real product work AND
   too big for this PR. Finish small follow-ups here; drop hardening, refactors
   and enhancements with one line in the report saying why.
6. **Copy a working reference; state the delta.** When a working
   implementation of the thing already exists on disk, copy it and rewire,
   then report what you changed. Rewriting a working implementation from its
   description is how the original feature failed.

**Fail loudly when a shared instance is missing.** When a lookup of a shared
instance — an app-wide environment, store, client or container — fails, throw,
assert or precondition; never construct a private instance as a fallback. A
private copy is never started or configured, so the feature runs against
nothing while every gate stays green, and the wrong lookup ships as working.
Failing at the lookup is what turns it into a finding instead. (The defect
class this catches: a silent fallback built a second, never-started copy.)

## Verification

7. **Demonstrate every fix.** Show the test red before the change and green
   after, or revert the change and show the failure reproduce — real output,
   pasted. A claim that a test has teeth counts for nothing without it.
   And verify the revert actually took before trusting the red run: a stash
   or checkout with a wrong pathspec reverts nothing, silently, and the
   "red" run then tests the fixed code. The tell is a "red" run whose
   pass/fail counts equal the green run's — confirm with `git diff` that
   the tree really changed before reading the failure as proof.
8. **Run the artifact.** Exercise the experience criteria against the running
   app (or the closest runnable surface) and report what you saw, not what
   the code should do. When the ticket cites a design board, put a screenshot
   of the built screen (`agent-device screenshot`, or the snapshot test's
   reference image) beside the board and inventory it: every element the
   board draws, present or absent, and every element the app draws that the
   board does not. The second half is the one a difference list skips —
   quillnote's compose icon appears in no board and passed a 16/16 closeout
   that listed differences and never listed extras; 26 of 30 design tasks
   before it cited their board and shipped a settings footer no board has.
   When the inventory is delegated, the sub-agent's model is `opus`
   (`setup-coduo-toolchain` has the measurement). A control is driven, not
   inventoried: click it and report the state that moved — six quillnote
   buttons drawn to the board and wired to empty closures passed both the
   snapshot and the accessibility tree, since an empty closure is still an
   enabled button.
   If no surface can run in your
   environment, say so explicitly in the report; the diff is not a substitute.
9. **Evidence is classed, committed, and rendered.** Pick the evidence class
   before capturing, keep the same class before and after the fix, and name
   it in the report so the reviewer knows why other artifacts are absent:
   `static-visual` — one failing-state screenshot and one fixed-state, not
   one per navigation step; `temporal` — a recording for animation, gesture,
   or a crash sequence, plus a still only when a distinct final frame
   matters; `structural-runtime` — the exact log, assertion, or red-first
   test, no media. A diff that changes what a route renders (a page,
   a screen, a landing section) is `static-visual` at minimum, whatever the
   ticket says: one before (base) and one after (branch) capture of each
   changed route. `structural-runtime` is for changes nothing draws. Commit image evidence to
   `.agents/evidence/<task-or-issue>/`, numbered by step
   (`03-after-save-crash.png`), on the work branch. The directory is
   disposable after merge and is never gitignored during the work — the
   curl check below depends on it being pushed. A PR body renders
   before/after side by side — a bare image URL renders as a link, which is
   not acceptable:

   ```markdown
   | Before (`main`, `<sha>`) | After (this branch, `<sha>`) |
   | :---: | :---: |
   | <img src="https://github.com/<owner>/<repo>/blob/<sha>/.agents/evidence/<id>/<before>.png?raw=true" width="380" alt="failing state"> | <img src="…/<after>.png?raw=true" width="380" alt="fixed state"> |
   ```

   Hotlink by commit sha, never by branch name. A branch URL 404s the moment
   the merged branch is deleted, so every past PR's before/after rots; a sha
   URL keeps resolving after the path is deleted from the tree, so the
   closeout sweep can remove `.agents/evidence/<id>/` after merge with
   nothing breaking. The sha is the commit that added the screenshots —
   `git rev-parse HEAD` once that commit is pushed, re-derived if you amend
   or add a later evidence commit. Use the `blob/<sha>/…?raw=true` form, never
   `raw.githubusercontent.com`: on a private repo the raw host gets no
   viewer token and the image renders blank (atlas PR #1118), while the blob
   form redirects with the viewer's session and renders (PR #1045). Push the
   branch, then check each file with
   `gh api "repos/<owner>/<repo>/contents/<path>?ref=<sha>" -q .size` —
   anonymous `curl` 404s on a private repo, so it proves nothing there.
10. **Every fix leaves a lesson.** When the work fixes a defect or a review
    finding (a review comment, a post-merge correction, an AFK lane's fix),
    end each fix in one lesson, classed:
    - `rule`: a code shape that can recur. It goes in the repo's lessons home.
    - `standard`: judgement, or a single-use external API fact (a Stripe or
      GitHub behaviour). Append one line to the repo's coding-standards doc
      (e.g. `CODING_STANDARDS.md`), which `/code-review` reads next time.
    - `none`: one line of reason, specific enough for a reviewer to overrule.

    Write a `rule` lesson test-first, `/tdd` style. The red fixture is the
    real pre-fix code, the green fixture the fixed code. Run the red fixture
    before the rule exists and show it passing unflagged; add the rule; show
    red fire and green stay clean, real output as in check 7. ESLint: one
    rule per lesson under the repo's local `lessons` plugin (copy the shape
    of harbour's `eslint.lessons.mjs`, message ending in the PR number),
    fixtures run by `RuleTester` in the unit suite. Separate rules, because
    ESLint replaces a rule's options across config blocks, so two
    `no-restricted-syntax` lessons on overlapping files silently override
    each other. Swift and Rust: ast-grep, `valid:`/`invalid:` cases run by
    `ast-grep test`; SwiftLint `custom_rules` only for a token ban. The
    fixtures are the rule's contract: narrowing its matcher or its file
    scope turns a fixture red, which is what stops a later lane passing the
    gate by loosening the lesson.

    Each intended hit carries its exception at the site with a reason
    (`// eslint-disable-next-line lessons/<id> -- <reason>`), so the
    exception shows in the diff that adds it and the rule's scope stays
    whole.

    The lessons home is the one the repo's lane gate already runs (an ESLint
    lessons file, `sgconfig.yml`, a SwiftLint `custom_rules` section). A repo
    with none: class the lesson anyway, say in the report that the repo has
    no lessons home, and name `setup-coduo-toolchain` as the step that adds
    one; the gate stays as it is.

    Done when the report carries one lesson per fix: `rule` with rule id and
    fixture path, `standard` with the line, or `none` with the reason.
11. **Finish as `/implement` says**: full test suite once, `/code-review`,
    commit to the current branch. Exception: inside an AFK runner lane the
    runner owns git history and builders never commit — stop after the review.
