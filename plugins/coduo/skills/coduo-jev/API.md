# Jev API shape

Reference for writing the call. The [live docs](https://docs.typesafe.ai/api.md)
are the source of truth: WebFetch is off here, so read a page with
`curl -sL "<url>.md"`. Read them for anything not here, and always before
quoting a rate limit, a price or a context budget — those move without notice
and are pinned to a model version.

## Request

```
POST https://api.typesafe.ai/v1/systemone
Authorization: Bearer $TYPESAFE_API_KEY
Content-Type: application/json
```

```json
{
  "state": "…text, object, or array…",
  "model": "jev-latest",
  "questions": {
    "your_id": { "type": "noul", "instructions": "…", "criteria": {…} }
  }
}
```

All three fields are required. `state` is ingested once and every question is
evaluated against it in parallel. `model` takes an alias (`jev-latest`,
`jev-preview`) or a pinned version id; the response's `model` field always
reports the version that answered. Pin the version once a threshold is tuned
against it, because an alias moves under you.

Question ids are yours and come back on the answers. They are **not sent to the
model**, so an id carries no meaning into inference.

## The three primitives

| Type | `criteria` | Returns |
| --- | --- | --- |
| `noul` | optional `{"true": "…", "false": "…"}` | `{"type":"noul","noul":0.99}` |
| `choice` | required map of option → rubric (or `null`), max 255 | `{"type":"choice","choice":"x","confidence":0.95,"probabilities":{…}}` |
| `score` | required ordered array of 2–10 level descriptions | `{"type":"score","score":1.33,"confidence":0.4,"legend":{…},"probabilities":{…}}` |

A Noul has no confidence: the probability *is* the answer. Use one Noul per
label when several labels can be true at once — but a Choice over options and one
Noul per option answer different questions. The Choice is relative and settles
*which*; each Noul is absolute and can be low for all of them.

Score levels are indexed from `0`, and both `legend` and `probabilities` are
keyed by that index as a string. The returned `score` is the probability-weighted
position across them, so `1.33` on a three-level scale sits between levels 1 and
2. Threshold on the value; read `confidence` as a separate signal about how
sharply the mass is concentrated. The gap between two levels is not a calibrated
magnitude — a real number reconstructed by interpolating it is noise.

## Structured instructions and criteria

`instructions` accepts a string, object or array. Use an object to separate the
question from the evidence it refers to, and point at a field by backticked name:

```json
"instructions": {
  "skill_name": "pstack:blast-radius",
  "what_it_does": "Find what a change could break…",
  "question": "Which role should be told this skill is installed?"
}
```

Reference a nested `state` value the same way: `` `ticket.messages[0].text` ``.

A Choice option's rubric can be an object too. Use the same field names across
every option — what it covers, what belongs elsewhere, a couple of examples — so
the model compares them on matching axes.

## Budget and errors

One request carries the `state` plus every question inside a single context
budget, with a tighter sub-budget covering the state plus the *longest* single
question. Both numbers are on the [models page](https://docs.typesafe.ai/models.md);
read it rather than trusting a number cached anywhere.

The practical consequence: chunk by questions, not by state. Repeating the same
state across several requests re-ingests and re-charges it, so pack as many
questions per request as the budget allows before cutting a new one. Input tokens
are charged; output tokens are free, which is what makes a speculative fan-out
nearly free.

Accuracy falls as the state grows with material the questions do not use, so
filter in code and send only the fields a question reads.

`401` is a bad key. `422` is a malformed request and the body names the offending
field. `429` (rate limit) and `529` (overloaded) both want exponential backoff,
honouring `retry-after` when the response carries one; the official SDKs do this
by default and a hand-rolled HTTP client has to do it itself.
