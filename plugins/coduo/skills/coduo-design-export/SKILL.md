---
name: coduo-design-export
description: |
  Get a Paper canvas's artboards out of Paper and into the repo as the binding
  spec — standalone HTML per board, Paper's raw JSX, 2× PNG baselines, an
  INDEX.md — and mirrored onto a Claude Design canvas, spending the fewest
  Paper MCP calls possible. Use whenever boards, screens or artboards need to
  leave Paper for a repo or an AFK run: "export the boards", "sync the designs
  out of Paper", "get the screens into docs/design", a `board-sync` task, or a
  Paper weekly-limit error blocking a design gate. Not for editing on the
  canvas (that is the Paper MCP's own guide) and not for turning a board into
  SwiftUI (that is the product's design skill).
disable-model-invocation: false
---

The Paper MCP is **metered**: a weekly limit that, once hit, refuses every
call that touches a file's content (`export`, `get_jsx`, `get_screenshot`,
`list_files`). Every step below exists to spend that meter exactly once per
artboard and never on something a script can do. Paper is the human's
upstream; what this skill leaves in the repo is the working copy, and no lane
ever needs the canvas again.

Scripts live in `scripts/` beside this file; call them by absolute path.

## 1. Preflight — one cheap call

`get_basic_info` with an explicit `fileId` (from the Paper URL,
`app.paper.design/file/<fileId>/<page>`). It is not metered and it gives you
the page's artboard list: ids, names, sizes, world positions. If it answers
but `export` or `get_jsx` return `Weekly MCP limit reached`, the limit is
**per file**: ask the user to duplicate the canvas into a new Paper file and
work from that file's id. That cleared a "wait a week" gate in one session;
try it before proposing an upgrade or a wait.

From the artboard list, settle the census before spending anything:

- **Which artboards are boards.** Screen-sized ones (e.g. 393×852) are; odd
  sizes ("Frame", "Bottom-aligned CTA") are components or scratch. Artboards
  the task or GOAL rules out of scope (camera surface, bin) stay out even if
  they are the right size — say so in INDEX.md rather than exporting them.
- **Same-named artboards are states until proven duplicates.** Two
  `HOME_SEARCHING` boards were the free-tier and subscribed states; the
  audit had called them duplicates. Export both, look, then decide — the
  PNG export is one batched call anyway.
- **Slugs come from downstream, not from Paper.** Read what the consumers
  glob for (`futari-*-perms-partial.png` in a task's `checks:`, the
  `pairs.d/<name>.tsv` names, the gallery IDs) and name each board to match.
  A Paper name that differs is recorded in the INDEX row, not used as the
  filename. A rename after the fact costs a commit; a mismatch costs a
  failed lane.

Write the census down as `manifest.tsv` (one line per board, flow order:
`<paper-name>\t<slug>\t<gallery-id|none>\t<note>`). It drives the rest.

## 2. PNGs — one call

`export` takes a map of every node at once: `{ "<id>": [{format: "png",
scale: "2x"}], ... }`. One call for the whole page. Files land in
`~/Downloads/<ArtboardName>@2x.png`; same-named artboards overwrite each
other there, so export those in separate calls and move each out between.
Move everything into a scratch `png/` named by the Paper artboard name
(`HOME_SEARCHING.png`, `HOME_SEARCHING_SUBSCRIBED.png` for the second).
Confirm every file is exactly 2× the artboard (`sips -g pixelWidth`).

## 3. JSX — one call per artboard, nothing re-typed

`get_jsx` with `format: "inline-styles"`, one call per board. There is no
batch form: on the page root it returns an empty string.

Results are big (50–90 KB per screen) and the harness saves any result over
its cap to a file on disk instead of the context, printing the path. Lift
the markup out with

    python3 scripts/extract_jsx.py <tool-result.txt> jsx/<PAPER_NAME>.jsx

and never re-emit it. A result small enough to arrive inline (a splash, a
paywall) has to be written out with the Write tool; if it repeats an SVG
glyph another board already carries, write `@@GLYPH@@` and let
`scripts/splice_glyphs.py` (`harvest` from the earlier file, `splice` into the
new one) fill the 6 KB `d=` attribute rather than retyping it. Fidelity is the
point: the JSX is the source of every measurement a lane will take.

Raster illustrations appear as `url(https://app.paper.design/file-assets/…)`
— public URLs, no session needed. `scripts/fetch_assets.sh jsx/ <boards-dir>`
vendors them into `<boards-dir>/assets/` and prints the prefix for step 4.

## 4. Convert, place, check

Fonts first: the product bundles its faces (look under the app's
`Resources/`); copy the TTFs into `<boards-dir>/fonts/` so the HTML renders
the real Manrope, not a system fallback, on any machine. Then:

    python3 scripts/place_boards.py manifest.tsv \
      --jsx jsx --png png --boards docs/design/<system>/boards \
      --baselines docs/design/baselines --prefix <product> \
      --assets-url-prefix <prefix from fetch_assets> \
      --fonts <app Resources dir> --family DMMono="DM Mono"

It numbers boards in manifest order (`<prefix>-NN-<slug>`), converts each
JSX to a standalone HTML (`scripts/jsx2html.py`: `style={{}}` → CSS,
unitless props kept unitless, self-closing tags closed, `@font-face` from
`fonts/`), copies the raw JSX to `boards/jsx/`, the PNG to `baselines/`,
writes `INDEX.md` from the manifest, and runs the checks the gate will run:
HTML and PNG stems match, every PNG is 2× the artboard, `blank-check.py`
passes if the repo has one. Exit 0 or it tells you which file.

Then look. `scripts/render_check.sh <board.html> out.png` renders one board
headless at device scale 2; Read it beside Paper's PNG for the same board.
Do this for the densest board and one with a raster asset — a path or
asset bug shows up as a picture here, not in a lane three days later.

Edit `INDEX.md` after: it is a skeleton. Add the export provenance (file
name, id, date, method), the rulings from step 1 (why 15 not 14, what was
left out and where its PNGs are), and a line telling a reader that exact
values come from the HTML/JSX and the PNG is the vision judge's picture.

## 5. Commit and close the gate

Commit boards, baselines, INDEX and the task-file change together on the
branch the run will use as `--base`. If the export was a human gate
(`gate: before` in a task file), delete that line and move the task to
`tasks-done/` with `status: ready-for-agent` (the loader refuses any other
status there). `afk wave validate tasks/` should report it `[done]`.

Update the run's GOAL / spec so lanes read the repo: where the three forms
live, what each is for, and that Paper is out of bounds for a lane. Leave
the Paper URL for humans.

## 6. Claude Design — from disk, not through you

    python3 scripts/gallery_page.py <boards-dir> /tmp/cd-stage \
      --title "<Product> — App Screens" --blurb "<provenance line>"

stages `boards/` plus one gallery page of iframes. Push it with `DesignSync`:
`list_projects` → pick the product's project → `finalize_plan` with
`localDir: /tmp/cd-stage`, writes `["<title>.html", "boards/*.html",
"boards/assets/*", "boards/fonts/*.ttf", "boards/jsx/*.jsx"]`, `deletes: []`
→ `write_files` with `localPath` per file. Contents go straight from disk;
the model never carries a board. (`mcp__claude_design__write_files` only
takes inline data — do not use it for this.)

Record the canvas URL and the repo path together in `INDEX.md`; a canvas
nobody links from the repo never reaches implementation. Re-stage and
re-push whenever a board is renamed, and pass the old path in `deletes`.

## Budget for a 15-board page

1 `get_basic_info` + 2 `export` (one batched, one for the same-name spare)
+ 15 `get_jsx` = 18 metered calls, zero repeats. Anything above that is a
call a script should have made unnecessary.
