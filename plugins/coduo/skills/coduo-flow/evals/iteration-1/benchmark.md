# Skill benchmark: coduo-flow, iteration 1

Three prompts, one paired run each: the same prompt handed to a subagent
with the skill and to a subagent with no skill at all. The prompts and
assertions live in `../evals.json`; grading is `../grade.py`. Spreads are
sample standard deviation over the three evals.

## Consistency is the headline

Read the spread before the mean. The skill's claim is not that a capable
model cannot produce a good flow map unaided - sometimes it does. The
claim is that the same structure comes out every run, which is what makes
the output something a teammate can open and trust.

| Metric | With skill | No skill | Delta |
|---|---|---|---|
| Pass rate | 88% +/- 0% | 4% +/- 7% | +0.83 |
| Wall time | 454s +/- 90s | 284s +/- 117s | +171s |
| Tokens | 92756 +/- 5830 | 68960 +/- 13874 | +23796 |

The skill costs about 60% more wall time and 35% more tokens. That is
the price of the structure, and it belongs in the decision about whether a
given task needs a map at all.

## Per eval

| Eval | With skill | No skill |
|---|---|---|
| eval-0-idea-validation-capture | 7/8 | 0/8 |
| eval-1-user-flow-mapping | 7/8 | 1/8 |
| eval-2-multi-epic-planning | 7/8 | 0/8 |

Assertion 7 - do the standfirsts state a conclusion a reader could repeat?
- needs human judgement and is always recorded unmet, so 7/8 is a clean
mechanical sweep rather than a near miss.

## What the baselines actually did

Both failure modes turned up, and they are opposites. The idea-validation
baseline split into nine notes unprompted; the user-flow and multi-epic
baselines each wrote one long document plus an HTML rendering, and the
multi-epic one hand-rolled a `dependencies.json` beside it. All three were
readable prose. None wired the notes into a graph, so none produced a map
you can click through.

That is why the first assertion asks for connectivity rather than a file
count. Counting files does not separate the two arms - the nine-note
baseline would have passed it on instinct. Wiring separates them.

Notes whose kind maps to tone `none` are exempt from that check: an
off-graph reference note is a documented pattern, not an orphan.
