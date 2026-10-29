# Evals

What lives here is the *measurement*, not a harness. Running paired
subagents, aggregating, and the review viewer are `skill-creator`'s job and
it already does them well; duplicating that machinery here would mean
maintaining someone else's tooling. What is genuinely specific to
`coduo-flow` — and what would otherwise be re-derived from scratch every
time someone edits `SKILL.md` — is two things:

- `evals.json` — three prompts, one per scenario the skill claims to
  cover, written the way a real user would actually phrase them.
- `grade.py` — what "the skill worked" means, in a form a machine decides.

`iteration-1/benchmark.md` records where the skill stood when it shipped,
so a later change has something to be compared against.

## Running it

Invoke `skill-creator` and point it at this directory. It spawns, for each
prompt, one subagent with the skill and one with no skill at all, and
writes each run to:

    <workspace>/iteration-N/eval-<n>-<name>/{with_skill,without_skill}/outputs/

Then grade every run in one pass:

```bash
python3 evals/grade.py <workspace>/iteration-N
```

That writes `grading.json` beside each run's `outputs/` in the shape the
viewer expects, and prints a per-run tally.

## The assertions

Eight per prompt. Seven are mechanical and `grade.py` decides them:

| # | Checks |
|---|---|
| 0 | The notes form one connected graph — 4+ notes, none isolated |
| 1 | Every note carries `id`, `title`, `node`, `kind`, `status`, `summary` |
| 2 | `depends_on` and `unlocks` are exact inverses, no dangling ids |
| 3 | A `flow.json` exists and declares a title |
| 4 | The generated HTML is self-contained — no external `src`/`href` |
| 5 | Every note's content is embedded, so a card click needs no network |
| 6 | `check_flow.py` exits 0 against the folder |

Assertion 7 — do the standfirsts state a conclusion a reader could repeat,
rather than naming the subject they cover? — is the one thing here that
resists mechanisation, so `grade.py` always records it unmet and leaves it
to the reviewer. **A clean mechanical sweep is 7/8, not 8/8.**

Assertion 0 asks for connectivity rather than a file count on purpose. An
earlier version asked only for "4+ separate notes" and turned out not to
discriminate: one baseline split into nine notes unprompted and passed it
by instinct, while producing nothing you could click through. Wiring is
what separates a folder of prose from a map. Notes whose `kind` maps to
tone `none` are exempt — an off-graph reference note is a documented
pattern, not an orphan.

## Reading the result

Read the spread before the mean. The interesting number in
`iteration-1/benchmark.md` is not 88% against 4%; it is ±0% against ±7%,
and ±90s against ±117s. A capable model unaided will sometimes produce
something good — it just will not produce the same thing twice, which is
the property that makes a map worth handing to a teammate.

The skill also costs about 60% more wall time and 35% more tokens. Keep
that in the table. A regression that buys back consistency at triple the
cost is still a regression.
