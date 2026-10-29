# Discovery — where the model comes from

Read in this order. Each pass answers one question and feeds the next.

## 1. The repo's own architecture docs

`docs/CODE-MAP.md`, `docs/architecture.md`, `docs/developer/*`, `AGENTS.md`,
`CLAUDE.md`, `README.md`. These name the boundaries the maintainers care about
and the vocabulary they use for them. Adopt their words for node labels; a map
that invents its own names for known parts reads as a map of a different repo.

If a `graphify-out/` directory exists, `graphify explain "<concept>"` answers
"where is X defined, who calls it" in one call — cheaper than grepping for the
same edge.

## 2. Entry points and boundaries

Grep for the places control enters or leaves the process:

- entry files (`src/main.*`, `src/entry-*.*`, `app/layout.*`, `index.*`)
- route tables, router config, page directories
- HTTP and RPC clients, generated API operations
- persistence: caches, stores, databases, local files, keychains
- external services: third-party APIs, auth providers, payment, telemetry
- build and CI: the scripts a maintainer runs before merging

Every boundary is at least one node, and every crossing is at least one edge.
These are what a reader most needs the map for; internal helper modules are
what they least need.

## 3. Flows

Two categories, both required.

**User flows** start with a human action. Find them in the UI: dialogs, forms,
drag handlers, row actions, command palettes. One flow per journey a user would
name ("create an issue", "move a ticket"), not one per function.

**System flows** run without a human in front of them: startup, hydration,
auth exchange, background sync, cache restore, CI gates. Find them in entry
files, providers, and workflow definitions.

For each flow, chase the call chain from trigger to durable effect and record:
what the user does, which components it passes through in order, what changes
on success, and what happens when it fails. The failure path is the half most
maps omit and most readers need.

## 4. QA

For each flow, find its tests: the test files that already cover it, and the
repo's own runner command (`package.json` scripts, `Makefile`, CI workflow).
The `command` you record must be one a maintainer can paste and run.

Manual checks come from the parts a test cannot see — what the human should
watch happen on screen, especially the optimistic state and the failure
recovery. Write each as an action and its expected result.

## 5. Constraints and known issues

`architecturalConstraints` are the invariants the codebase enforces — the rules
a reviewer would reject a PR for breaking. Take them from the docs and from
lint or boundary configuration, not from inference.

`knownIssues` are documented defects in the structure itself: import cycles,
layering violations, dead adapters. Cite the doc that records each one.
