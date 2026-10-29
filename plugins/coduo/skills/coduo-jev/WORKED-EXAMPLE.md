# Worked example: which skills does this project need?

One run, 20 Sep 2026, against the AFK runner's problem: a project's
`.afk-setup/config.yaml` carries a `roles:` block naming which installed skills
each agent role gets as `always` (a rule) or `offer` (a choice). It was
hand-maintained from memory and drifting, while ~100 installed skills were never
named anywhere.

Read it for the shape. Every number below is from this one run on this one
machine.

## Step 1 — what survived the refusal

- Writes? The `always`/`offer` lists are enumerated names, not prose. But the
  block's third field, `notes`, **is** prose, which Jev cannot produce. That
  field stayed hand-written. Half the task was refused, and saying so was the
  useful part.
- Labels? None. The roster changes every time a plugin is installed.
- Code already knows? No. It is a semantic match between a skill's description
  and what a project is.
- Shortlist? Yes — every `SKILL.md` on the machine, read from disk.
- Irreversible? No. The output is a YAML block a human reads before committing.

## Step 2 — position

**Router**, at setup time: it selects which skills each role is told about. It
runs once per project rather than per lane, and a human reviews the output.

## Step 3 — the split

The wide question — *"produce the roles block"* — would have asked one model to
do roster ranking, role assignment and strength grading at once. Split into two
atomic questions **per skill**, both in the same request:

- `role::<skill>` — a **Choice** over `{implementer, integrator, verifier, fixer,
  plan-reviewer, none}`, each option's rubric describing what that role actually
  does during a run. `none` is the non-match outcome, and it earns its place:
  without it every irrelevant skill lands on the nearest role.
- `strength::<skill>` — a **Score** whose three levels *are* the buckets:

```
0  Not relevant to this project at all — wrong stack, wrong platform,
   or work this project never does.
1  Relevant on some tasks only. Read it when the ticket calls for it.
2  Applies to essentially every task this role performs. Apply it before
   starting, every single time.
```

`state` is a 24-line project profile: stack, platform, what it explicitly does
*not* have (no backend, no accounts, no Android), the build system's gotcha, and
what the agent roles do. Written by hand, ingested once per request.

Each question's `instructions` is an object carrying the skill's name, its
description, and the first 500 characters of its `SKILL.md`, with the question in
a fourth field.

## Step 4 — the verdict, in code

```
drop   when role == "none"
drop   when role confidence < 0.50
drop   when strength score  < 0.50
always when strength score >= 1.50
offer  otherwise
```

Three thresholds, all in the caller, none of them asked of the model. 33 of 116
skills survived.

## What it cost

116 skills → 232 questions → 6 requests of 20 skills each → 101,680 input
tokens, about 40 seconds, **$0.0043**.

## What it got right, and where it was wrong

Right: it found a Swift skill the hand-written block had never named, and it
dropped every payment-SDK skill because the profile said that integration was
planned but not yet in code — exactly the distinction the profile was written to
carry.

Wrong, and instructive: it assigned `none` at 0.81 to a design skill that is
obviously relevant to the product. The skill's own description explained it —
the description says the approach is "translated for the web", and the project is
native iOS. Jev read the evidence it was given, literally. **The failure was in
the roster's descriptions, not in the ranking**, and it was visible only because
the run printed the score and the winning probability beside every skill name.

Print the numbers beside every decision. A bucketed list with the probabilities
stripped off cannot be audited, and this one needed auditing on its first run.

## The measurements

**Reorder — run, and it found something.** The whole roster was re-ranked with
the six role options reversed. 5 skills of 116 crossed a bucket boundary. One
of them, `pstack:show-me-your-work`, had been `verifier`/`always` on a winning
probability of 0.51 — a hair over the floor — and disappeared entirely on the
second pass. Every skill that moved sat within 0.05 of a threshold. The reorder
did not find a bad model; it found which entries the thresholds had decided by
coin-flip.

The two that did not happen before the output was used:

- **Second shape.** The role Choice was never re-asked as a per-role Noul, so
  nothing tested whether `none` at 0.81 means the same thing as a low relevance
  Noul would. Ask both on the disagreement rows before any `always` entry is
  trusted.
- **Known answers.** No labelled set was scored, so all three thresholds are
  guesses that happened to produce a plausible list.

TypeSafe's own [skill suggestion cookbook](https://docs.typesafe.ai/cookbooks/skill_suggestion.md)
solves a near-identical problem as a cascade — a wide ranking request, then a
narrow one that re-reads the top few in full and may reject them all — and is
worth reading beside this before designing a router over a large roster.
