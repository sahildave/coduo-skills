---
name: coduo-code-flow
description: |
  Build the interactive flow map for a repository: an architecture JSON model
  (nodes, edges, user and system flows, manual and automated QA) rendered into
  a standalone HTML explorer under `docs/architecture/`. Use when asked for a
  flow map, an architecture explorer, a QA dashboard of user journeys, or when
  an existing map needs new flows after a feature lands.
disable-model-invocation: false
---

# Coduo flow map

Two artifacts, one direction:

```
docs/architecture/<name>.json     the model      <- you write this
docs/architecture/<name>.html     the explorer   <- render.py generates it
```

The JSON is the **single source of truth**. The HTML carries no data of its
own: `scripts/render.py` injects the model into `assets/flow-map-template.html`.
Edit the JSON, re-render, commit both. An edit made in the HTML disappears at
the next render.

The map answers three questions a reader brings to an unfamiliar repo: what
are the parts, how does a request move between them, and how do I check that a
journey still works. That third one is why every flow carries QA — the map is a
manual-test dashboard, not just a diagram.

## Phase 1 — Mine the repo, not your memory

Every node label, path, and flow step names something that exists in the repo.
Read [`references/discovery.md`](references/discovery.md) for where the
material lives and the order to read it in.

Record `generatedFrom`: the docs and directories you actually read. It is what
the next agent re-reads when the map goes stale.

**Done when** you can name every entry point, every boundary the data crosses,
and every user journey the product ships — each with the file paths that
implement it. A node you cannot attach a path or an external system to is a
node you invented.

## Phase 2 — Write the model

Write `docs/architecture/<repo>-flow-map.json` against
[`references/schema.md`](references/schema.md), which carries every field, the
layer and kind vocabularies, and the canvas coordinate rules.
[`examples/notes-app-flow-map.json`](examples/notes-app-flow-map.json) is a
small complete model to copy the shape from.

Three rules the schema cannot enforce:

**Edges are the graph; steps are a path through it.** A flow's `steps` list the
nodes it touches in narrative order, and its `edgeIds` list the existing edges
it traverses. When a flow needs an edge that isn't there yet, add the edge to
`edges` — never invent an id inside the flow.

**Every user flow gets manual QA with an `expected` result.** A check that says
what to do but not what should happen is untestable by the human who opens the
dashboard six months from now. Automated checks carry a runnable command from
the repo's own scripts.

**Positions are hand-placed.** There is no auto-layout. Flow direction runs
left to right, layers stack in rows, and `layout.lanes` label the row bands.

**Done when** every flow the product ships appears once, with its trigger,
success outcome, failure behaviour, source paths, and QA.

## Phase 3 — Validate, render, look at it

Both scripts live beside this file — [`scripts/validate.py`](scripts/validate.py)
and [`scripts/render.py`](scripts/render.py). Run them with the skill directory
you loaded this from as the prefix:

```bash
python3 scripts/validate.py docs/architecture/<name>.json
python3 scripts/render.py docs/architecture/<name>.json
```

`validate.py` errors on dangling ids, duplicates, and missing positions;
it warns on overlapping cards, orphan nodes, and flows whose `edgeIds` don't
cover their own `steps`. Clear the errors. Read the warnings and fix the ones
that are real — an overlap means two cards sit on top of each other on the
canvas, and only you can decide where the second one goes.

Then open the HTML and look at it. Select a flow: its nodes and edges light up
and everything else mutes. Crossed or overlapping edges are a layout problem,
so move the node and re-render.

**Done when** validate reports no errors, and a selected flow reads as a legible
path across the canvas.

## Phase 4 — Land both files

Commit the JSON and the HTML together. A map whose HTML lags its JSON tells the
reader something false, and the reader is the one person who cannot tell.

## Updating an existing map

Read the JSON first and extend it. Keep node and edge ids stable — flows
reference them by id, and the dashboard keys stored QA state on flow and check
ids, so a renamed id silently discards a human's tick marks. Re-run validate
and render, and commit both.
