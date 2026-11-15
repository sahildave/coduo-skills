# Lessons

Every fix of a defect or a review finding ends in one lesson. Assume the next
contributor is an agent that sees only the files it opened, copies the
nearest example and takes the shortest path that compiles. A lesson it never
reads does not stop it, so take the first level that works:

1. `structure`. Make the mistake impossible to write: give the state one
   owner, give the task one supported way, hide the internal so the wrong
   import fails, or use a type the bad value cannot be built in. Delete the
   old way so nobody copies it.
2. `rule`. The bad code still compiles but has a shape a linter can see. Its
   message names what to use instead and ends with the PR or finding it came
   from. If the shape is already common in the repo, fail only when a change
   adds more.
3. `test`. No linter can see it, but behaviour can: a test through the
   user's interface that fails before the fix and passes after. Say in one
   line why it is not a `rule`. A test guards one site; a rule guards the
   class.
4. `standard`. Judgement, or a one-off external API fact (a Stripe or GitHub
   behaviour). Append one line with an example of the failure to the repo's
   coding-standards doc. Nothing fails when an agent skips it, so this is
   the last resort.
5. `none`. One line of reason a reviewer could overrule. "One-off" needs the
   reason the shape cannot recur.

**A repeat moves up.** Before you class the lesson, search the coding
standards, `AGENTS.md` and the lessons home for the mistake. If a `standard`
line already said it, the lesson is `structure`, `rule` or `test`. If a
`rule` already covers it, the rule has a gap: fix the rule, red fixture first.

## Writing a rule

Test-first. The red fixture is the real pre-fix code, the green fixture the
fixed code.

1. Run the red fixture with no rule and show it passes unflagged.
2. Add the rule.
3. Show red flagged and green clean, real output.

The lessons home is whatever the repo's lane gate already runs:

- **ESLint.** One rule per lesson under the repo's local `lessons` plugin
  (gitback's `eslint.lessons.mjs` is a working example), fixtures run by
  `RuleTester` in the unit suite. Keep lessons as separate rules: ESLint
  replaces a rule's options across config blocks, so two
  `no-restricted-syntax` lessons on overlapping files override each other.
- **Swift and Rust.** ast-grep, with `valid:` and `invalid:` cases run by
  `ast-grep test`. SwiftLint `custom_rules` only for a plain token ban.

The fixtures are the rule's contract. Narrowing its matcher or file scope
turns a fixture red, which stops a later change from passing the gate by
loosening the lesson. Where a hit is intended, suppress it at the site with a
reason (`// eslint-disable-next-line lessons/<id> -- <reason>`), never with a
file ignore.

A repo with no lessons home: class the lesson anyway and say in the report
that the repo has none. `setup-coduo-toolchain` adds one; do not build it
inside this fix.

## Reporting it

Interactive: the report names one lesson per fix (`structure` with its
commit, `rule` with rule id and fixture path, `test` with the test name and
why it is not a rule, `standard` with the line, `none` with the reason), and
each `structure` or `rule` lesson has its own commit.

AFK lane: use the `LESSON:` line the lane prompt gives. Its format knows only
`rule`, `standard` and `none`. Until the runner learns the other two, write a
`structure` or `test` lesson as `none:"structure: <what changed, where>"` or
`none:"test: <test name>, not a rule because <reason>"`.
