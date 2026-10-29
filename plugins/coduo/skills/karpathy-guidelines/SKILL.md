---
name: karpathy-guidelines
description: Baseline discipline for writing, reviewing, or refactoring code — keep changes surgical, keep solutions minimal, state assumptions instead of guessing, and end every step on a verifiable check.
license: MIT
disable-model-invocation: false
---

# Karpathy Guidelines

Baseline discipline for any non-trivial coding task, derived from [Andrej Karpathy's observations](https://x.com/karpathy/status/2015883857489522876) on LLM coding pitfalls. Biases toward caution over speed; for trivial edits, use judgment.

## 1. Surface assumptions, keep moving

State the assumption you are working under, in one line, then build on it. Where two readings of the request would produce materially different work, name both and pick one out loud.

Ask before building only when either reading would be unsafe or would waste the work. A foreseen failure gets fixed now, not filed in the report.

Where a simpler approach exists, say so and push back.

## 2. Ship the minimum

The minimum code that solves the stated problem. Every feature, abstraction, config knob and error branch traces to something that was asked for or something that actually happens.

Single-use code stays inline. Two hundred lines that could be fifty get rewritten as fifty.

The check: would a senior engineer call this overcomplicated?

For work where the user explicitly wants the laziest viable path, load `ponytail` — it is this section taken to its limit.

## 3. Surgical changes

Every changed line traces directly to the request.

Adjacent code, comments and formatting stay as they are, in the style already there. Broken things get fixed; working things get left alone. Unrelated dead code gets mentioned in the report and stays in the file.

The one exception is your own wake: imports, variables and functions that _your_ change orphaned come out with it.

## 4. Goal-driven execution

Restate the task as something checkable, then loop until the check passes:

- "Add validation" → "tests for invalid inputs pass"
- "Fix the bug" → "a test reproducing it passes"
- "Refactor X" → "the suite passes before and after"

For multi-step work, state the plan as pairs:

```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
```

A criterion the agent can grade itself against lets it run independently. "Make it work" does not, and buys a round of clarification later.

Where the work genuinely warrants test-first discipline, load `tdd`; this is the lightweight version.
