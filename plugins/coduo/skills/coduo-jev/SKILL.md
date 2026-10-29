---
name: coduo-jev
description: Design a TypeSafe Jev integration for a decision you name — refused, decomposed, or shipped in shadow.
disable-model-invocation: true
---

# Coduo Jev

The request arrives as "put Jev in front of X". Two jobs: decide whether X is a
Jev-shaped decision at all, and if it is, cut it into the smallest questions that
answer it. One wide question is how this model loses to a regex.

Stay adversarial the whole way. The user is enthusiastic and arrived from a
thread, so the first move is refusal and the strongest deliverable is often a
smaller integration than the one asked for.

## What Jev is

`POST https://api.typesafe.ai/v1/systemone` ingests one `state` and answers a map
of typed questions against it in parallel, returning **probabilities, never
text**. Three primitives: **Choice** (one of up to 255 options, with the
distribution), **Score** (a probability-weighted position on 2–10 ordered
levels), **Noul** (the probability a yes/no condition holds).

Request and answer shapes: [`API.md`](API.md). The live docs outrank both, and
WebFetch is off here — read a page with `curl -sL "<url>.md"`. Before designing a
question, read that primitive's page under `https://docs.typesafe.ai/primitives`
and the **jaggedness** page for the model you are calling
(`https://docs.typesafe.ai/model-jaggedness/<model>.md`), which lists what it is
measurably bad at. `https://docs.typesafe.ai/llms.txt` indexes everything.

## Step 1 — Try to kill it

Five tests. Run all five against the request as stated, and write a verdict for
each that cites the artifact in the user's own system that settles it — the file,
the table, the endpoint, the existing prompt. A verdict resting on a guess about
their system is not a verdict; go read the thing or ask.

- **It writes.** The output is prose, code, a summary, a commit message. Jev
  emits no text, so no version of this works.
- **You have labels and a frozen question.** A small model you host beats Jev on
  latency and price and needs no key. Jev earns its place when the answer set
  keeps moving and nothing is labelled.
- **Code already knows.** A lookup, an exact match, arithmetic, a schema check,
  a date comparison. Semantic judgment is the only thing worth paying for.
- **No shortlist.** Options have to be enumerated from something real — the DOM,
  the retriever's hits, the tool registry, a config file, a directory listing. A
  candidate list that must be invented means there is no question yet. Build the
  list first.
- **Irreversible and unsupervised.** Deletion, a payment, a force-push, a
  published post. A 0.85 threshold is a policy, not a safety net.

Most requests are several decisions wearing one sentence, and they routinely die
in half: split the request into its parts and run the five tests on each part
separately. A part that fails gets one sentence saying which test killed it and
the nearest thing that does work.

Everything still standing is Jev-shaped. Read [`WORKED-EXAMPLE.md`](WORKED-EXAMPLE.md)
for one such request carried end to end, including the half of it that was
refused.

## Step 2 — Name the position

Jev sits in front of the expensive call and decides whether it runs. Three
positions; make the user say one of these three words back:

- **Router** — picks which handler, model or tool runs next, and fills its typed
  arguments. The expensive model runs only on the branch that needed it.
- **Gate** — checks a proposed action *before* it runs. The cheapest place to
  catch a bad tool call.
- **Judge** — verifies an output *after* it exists, against the thing it claims.

Two shapes worth offering unprompted. **Compaction**: score every tool call in a
transcript, drop the dead ones, keep the survivors *verbatim* rather than
summarising them — usually the highest-yield first integration in an agent. And
the **cascade**: one cheap request ranks a whole roster, a second reads only the
top few in full detail and is free to reject them all. The cascade is what makes
a router over hundreds of options affordable.

Step 2 is done when the answer names the position, the exact call it stands in
front of, and what happens on each branch out of it.

## Step 3 — Split the question

This is the lever. Ask Jev for the final answer alone and you get the one thing
it is worst at.

1. Write the wide question the user was about to ask.
2. Write what a competent person checks *before* answering it. Usually four to
   six things.
3. Make each check its own **atomic** question in the same request. They run in
   parallel against one ingested `state`, so a fan-out of twenty barely moves
   latency over a fan-out of two.
4. Combine them in your own code, with your own weights and your own threshold.

**Code owns the verdict. Jev supplies the observations.** Fan out speculatively
while you are at it — output tokens are free and the state is ingested once, so
questions you may throw away cost close to nothing.

Step 3 is done when every question could be answered by someone shown only the
`state` and that one question — no question waiting on another's answer.

## Step 4 — Write the questions

Jev is **literal**: it answers the words written, not the intent behind them.
When a wrong answer makes you explain what you really meant, that explanation is
the missing half of the instruction.

- One judgment per question. Split where each half is independently useful, and
  keep a relationship in a single question when its pieces mean nothing apart.
- The judgment goes in `instructions`, the answer space in `criteria`. Question
  ids stay in your code and never reach the model, so put every id's meaning
  inside the question too.
- When a question carries evidence, make `instructions` an object: one field per
  piece, referenced from the question by backticked name.
- Write Score levels as concrete situations that stand alone, and Choice rubrics
  that say what the option covers and what belongs to a neighbour.
- Give every question an outcome for "none of these". Without one the
  distribution has nowhere to put a non-match and it lands on the nearest option.

Step 4 is done when every question is written out in full — type, instructions,
criteria — and every Choice option names the code branch it triggers. An option
meaning "escalate because I am unsure" belongs to Step 5 instead.

## Step 5 — Read the confidence

`confidence` comes back on every Choice and Score, calibrated from the shape of
the distribution, and it is where uncertainty lives. Read it on every answer.
Set each threshold from what that action costs to undo: low for a read, high for
anything you cannot take back. Everything under the threshold goes to a human or
to the expensive model, which is the position from Step 2 doing its job.

A Noul carries no confidence — its probability *is* the answer. When uncertainty
has to gate the action, ask that decision as a Choice or Score as well, and keep
the thresholds separate: a number tuned on a Noul does not transfer to a Choice.

Guardrail: questions of the form *do you have enough information* answer yes
almost always, because the model cannot see what it was not given. The
distribution reports that, not an option.

Step 5 is done when every action in the design has a threshold beside it, the
cost of undoing that action named, and one named path for everything below it.

## Step 6 — Shadow it first

Ship it in **shadow** before it decides anything.

- The existing path stays in charge. Send the same input to Jev, discard the
  answer, log both answers and the confidence into one table.
- A week later, read only the rows where they disagreed. Normal traffic built
  your test set for free.
- Switch over the cases where Jev was right, behind a one-line switch.

Three measurements before any number in the design is believed:

- **Reorder the options and diff the buckets.** TypeSafe documents System One as
  self-consistent across *repeated* evaluations of the same request. That is a
  different property from invariance to how the options are ordered, and the
  second one is not promised. Measured on this machine, 20 Sep 2026: reversing
  the option order of a Choice over six roles moved 5 skills of 116 across a
  bucket boundary, and every one of them sat within 0.05 of the threshold. Run
  it both ways and treat the skills that move as unsettled, not as answers.
- **Re-ask in a second shape.** Send the same decision as its negation, or as a
  Choice instead of a Noul, and diff. Jev guarantees no arithmetic identity
  between separately worded questions, so a pair that disagrees is telling you
  the wording is carrying the answer.
- **Score 100 examples whose answer you already know**, and tune the Step 3
  weights against those. Every number in the hand-back comes from the user's own
  data; a figure carried in from a thread or a benchmark is not evidence.

Step 6 is done when the shadow table's columns are named, the switch is one
line, and each threshold traces back to one of those three measurements.

## Step 7 — Hand back

Deliver, in this order: the position; the question list; the combining rule; the
thresholds; the fallback; the shadow plan. Name the file each piece lands in.

The hand-back is finished only when all of this holds, item by item:

- Every part killed in Step 1 is listed with the test that killed it and the
  alternative that works.
- Every question appears with its type, full `instructions` and full `criteria`.
- Every Choice option and every Score level maps to a named branch in the
  caller's code.
- Every threshold names the action it gates and the cost of undoing that action.
- The fallback path says what runs when Jev returns 429 or 529, when the key is
  missing, and when confidence lands under every threshold.
- The shadow table's columns are listed and the kill switch is identified.
- Anything you could not settle is written as an open question naming the
  artifact that would settle it, rather than being answered by assumption.
