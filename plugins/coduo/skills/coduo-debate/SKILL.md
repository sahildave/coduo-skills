---
name: coduo-debate
description: |
  Settle a plan, diagnosis, review finding or design choice by debating it
  with an independent Fable 5 sub-agent until you both agree, then report
  what was agreed and what is still open. Use when the user asks for "a
  second opinion", "a review from Fable", "debate it", or "make sure you both
  agree", and reach for it yourself before bringing the user a judgement call
  you are not confident about.
disable-model-invocation: false
---

# Coduo debate

A second model that starts cold catches what you stopped seeing: an
assumption you never checked, a finding you took on trust, a plan that grew
past what the product needs. The value is in the *disagreement*, so set
the debater up to disagree. Then settle each point with evidence, not by
deferring to whoever sounds more confident.

Don't debate decisions the user has already made. Debate how to carry them
out.

## 1. Write the brief

The debater sees none of this conversation, so the brief is all it gets:

- **The question**, in one sentence.
- **Your position** and the reasoning behind it.
- **The evidence**: file paths with line numbers, the commands you ran and
  what they printed, and any issue or PR links. Make it concrete enough to
  re-check, not a summary to accept on faith.
- **The constraints**: where the product stands (unreleased, launch week,
  in-house tool) and any ruling the user has already made, quoted.
- **What you are least sure of.** Point the debater at it.

## 2. Start the debater

Use the `Agent` tool with `model: "fable"` and give it this standing
instruction ahead of the brief:

> You are reviewing another agent's position adversarially. Assume it is
> wrong somewhere and find where. Re-check every factual claim yourself
> (read the file, run the command) rather than accepting it. For each point,
> answer **agree** or **disagree**, give your evidence, and propose an
> alternative when you disagree. Ask of the whole thing: is this more than
> the product needs right now? End with a table: point · verdict ·
> evidence.

## 3. Settle each point

For each disagreement, run the cheap check yourself. Then either **concede**
and say what changed your mind, or **rebut** with new evidence, meaning
something you actually ran and not a restatement. Send your answers back
with `SendMessage` to the same agent, so it keeps its context.

Stop after three rounds. A point still split after three rounds is a real
judgement call, and it belongs to the user.

**Done when** every point is agreed or conceded, or has been through three
rounds and is marked open.

## 4. Report

Keep it short:

| Point | Where it landed | Evidence |
|---|---|---|

"Where it landed" is one of: **agreed**, **you conceded**, **Fable
conceded**, or **open**. For each open point, lay out the two positions as
options, give your recommendation, and say what the choice turns on. Then
do whatever was agreed without waiting to be asked. Only the open points
need the user.

If the debater is still running when you are done, stop it with `TaskStop`.
