---
name: coduo-product-prototype
description: Build or extend a product's binding interaction prototype — the pre-approved frontend an unattended run later wires a backend behind. Runs state list → design variants → build on the real shell → freeze, with the owner reviewing in Lavish at each gate. Use when the user says "build a prototype for this idea/product", when coduo-wayfinder needs a full product prototype, or when freezing a prototype before an AFK run. For a throwaway prototype answering one design question, use `prototype` instead.
---

# Coduo product prototype

The prototype you build here is the product's frontend, not a sketch of it.
The owner tunes and approves it live; the unattended run then wires the
backend behind its seam and may not rebuild what you made. Everything below
serves that: build on the **real shell**, behind a **seam**, toward a
**freeze**.

The doctrine — why the real shell, the state list, the freeze contract — is
`brain/cookbooks/prototype-first.md` in the owner's knowledge
project. Read it once per product, before step 1; if the project's location
is unknown on this machine, find it with
`mcp__open-knowledge__search({ query: "prototype-first" })`.

## The owner reviews in Lavish

Steps 1 and 2 end on an owner decision, and the owner makes it in **Lavish**
(`lavish-axi`): a browser review surface over an HTML file, with annotations
and form answers sent back to the agent. Before writing any Lavish HTML, open
the playbooks the artifact uses (`npx -y lavish-axi playbook <id>`): `diagram`
for the state diagram, `input` for questions and picks, `comparison` for
variants, `design` for the design source. Render in the product's own design
system, as Lavish's design rule requires.

Open with `LAVISH_AXI_TELEMETRY=0 npx -y lavish-axi <file>`, then wait with
`npx -y lavish-axi poll <file>` in the foreground; re-run the poll if it times
out, because feedback stays queued. Answers arrive as prompts: write each one
back into the source file before doing anything else. `npx -y` only; never
`lavish-axi share`, which publishes the page.

**The poll needs the owner at the screen.** When this skill runs in a
sub-agent, the sub-agent builds the files and returns their paths; the main
session opens Lavish and polls. Never poll from an unattended run.

## 1. The state list comes first

Before any code, list every surface and its states (populated, empty, error,
first-run, …). This list is the outside artifact the prototype is later
counted against: a state invented during building joins the list the moment
it is invented, never left implicit. Mark each state **settleable** (a rest
state a picture can capture) or **in-flight** (only a behavioural test can pin
it), and say how to open it.

- **Source of truth:** `docs/prototypes/<feature>/states.json` — surfaces,
  states (id, name, kind, how to open), and `questions` (id, question,
  options, answer). Agents edit this file; everything else is rendered from it.
- **Diagram:** render the list with the `diagram-design` skill into
  `docs/prototypes/<feature>/states.html`: one node per state, grouped by
  surface, edges for the transitions a Client can cause. Regenerate it
  whenever `states.json` changes; never hand-edit the SVG.
- **Open questions:** every assumption the list makes that the spec does not
  settle becomes an entry in `questions`, rendered on the same page as a
  Lavish `input` form (one question per form, a Queue answer button each).

Done when: `states.json` and `states.html` are committed, the owner has
confirmed the list in Lavish, and every question has an answer written back
into `states.json`.

## 2. Design variants, before any prototype code

Variants come at two levels, and the owner picks at both:

- **The whole feature first.** Two or three variants of the complete feature
  in place: where it lives in the product (its own page, a section of an
  existing modal or settings screen, a panel), drawn inside the product's real
  surrounding chrome, with every surface in it. A fragment shown on its own
  cannot be judged; in the Harbour theming round the owner rejected three of
  four isolated surfaces and asked to "show the full UI" before the placement
  (inside the existing Settings modal) was even on the table.
- **Then each surface with a real design question** (a control's shape, how a
  choice is presented, an error treatment): two or three variants, each drawn
  inside the picked whole-feature frame, never as a floating fragment. A
  surface whose shape follows directly from the spec needs none; say so in
  `states.json` rather than inventing alternatives.

Show conditional UI only in the state that triggers it: a warning appears in
the failing frame, not in the passing one.

- **Where:** on a design canvas when one is connected (the Claude Design
  canvas MCP, or Doop at `https://doop.design/mcp`). Canvases are for
  exploring variants only; the prototype still runs on the real shell. When no
  canvas is connected, build the variants as HTML using Lavish's `comparison`
  playbook, one surface per section, side by side.
- **Canvas layout:** one Page for the whole-feature variants, then one Page
  per surface. Claude Design lists only
  root-level `.html` files as Pages, so write each surface's board at the
  project root (`D1-<surface>.dc.html`), with `support.js`, shared CSS and an
  `assets/` folder beside it and every path relative (`./assets/...`). A board
  in a subfolder is missing from the Pages menu and the canvas looks empty.
- **Fidelity:** each variant uses the product's real tokens, fonts and
  components, and shows the surface's populated state plus its hardest state
  (usually error or empty).
- **Into the repo:** the canvas root is mirrored into
  `docs/prototypes/<feature>/variants/` (same layout, so the relative paths
  work in both), and each Page's canvas URL is recorded in `states.json`; a variant that lives only on a canvas never reaches the build.
- **Picks:** the owner picks per surface through a Lavish `input` form. Record
  each pick, and the reason when one is given, in `states.json`.

Done when: the whole-feature variant and every surface flagged with a design
question have an owner pick recorded in `states.json`. The picks bind step 3's build.

## 3. Build on the real shell

Build the picked variant of each surface. Pick the branch by platform.

### SwiftUI (macOS / menu bar)

Work inside the generated product repo; if none exists yet, the
`coduo-swiftui-factory` generates it first (`validate → plan → generate`
from a manifest). The product's own AGENTS.md section **"Prototypes run on
the real shell"** is the binding contract for this branch; follow it over
this file where they differ.

- The recipe ships the starting point: `App/PrototypeScene.swift`
  (screen-sized transparent panel, real level and materials) reading the
  shipped store protocol from the preview fixture. Grow that scene; every
  prototype view renders from the store protocol, never from literals.
- **The prototype is product code, never gated.** Build it ungated on a
  feature branch; it ships when the branch merges, and the freeze is that
  merge. If the recipe's scene still starts with `#if DEBUG`, remove the gate
  in the first commit. `#if DEBUG` wraps developer tools only (tuning
  inspector, replay, debug menus), never a feature, a view or a live data path.
  Sample data runs only under an explicit launch flag and never mixes into
  live data. Nothing fake stands in for a missing feature: a gap shows as a gap
  and gets a ticket. Never add a feature flag or env-variable switch without
  The owner's explicit yes, asked with the flag's name and what it turns on or
  off.
- **Phase A**: everything happens inside the one panel — motion as
  interruptible springs in SwiftUI, tuning knobs in a separate `#if DEBUG`
  inspector window. This keeps slider-speed iteration with real coordinates,
  level, and materials.
- **Phase B**: split into the real window population (panel per display,
  window per sticky/item) the first time a tuning value has to be read from
  `NSScreen` — edge reach, reveal thresholds. Finish tuning in Phase B.
- Decide the **drag ruling** in writing the moment any window is draggable:
  own the drag (event loop; tuned release momentum works) or delegate it
  (`isMovableByWindowBackground`; AppKit snapping, no release velocity).
  The two are mutually exclusive.

### Next.js (web)

The real shell is the real route in the real app: mount the prototype at its
production route behind a flag, inheriting the live layout, providers, and
data-fetching boundary. The seam is the store: in-memory data behind the same
interface the product will implement. A prototype stranded in Storybook or a
`/playground` route inherits none of the shell and will be rebuilt — the
failure this skill exists to prevent.

### Both branches

- Sample data flows through one fixture; tuning values live as data in one
  file. A number the owner tuned appears in code only through a token.
- The owner approves by running it. Feel decisions are theirs; when a change
  alters something they approved, show them the running result, not a diff.

Done when: every state on the list is reachable in the running prototype and
The owner has approved each surface live.

## 4. Freeze — before every unattended run

A freeze is the commit after an owner approval, cut before every unattended
run: the first one, and again after each offline iteration on the prototype.
Between runs the owner iterates freely; unattended tasks never own prototype
files. Each freeze re-runs the whole list — re-export what changed,
re-capture the states whose surfaces moved, re-approve what the owner has
not yet seen running.

- The freeze sha is recorded in the product's `docs/prototypes/`.
- The tuning file is exported and a test pins the tokens to it — the test
  fails when a token drifts.
- Every settleable state on the list is captured through the product's one
  capture path (SwiftUI branch: `docs/design/baselines/P<NN>-<state>.png`,
  validated by `scripts/design/freeze-frames.sh` exiting 0).
- The census names every production file the motion ruling governs and its
  check exits 0 (SwiftUI branch: `docs/design/physics-surfaces.txt` +
  `scripts/design/physics-census.sh`) — and was seen exiting non-zero at
  least once first, on a planted violation.
- The drag ruling (SwiftUI branch) is written into the product's GOAL.md.

Done when: every bullet holds on the freeze commit, and the state list from
step 1 (`states.json`) has no uncaptured settleable state and no unpinned
in-flight state.
