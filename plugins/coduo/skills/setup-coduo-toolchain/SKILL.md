---
name: setup-coduo-toolchain
description: Provision a repo's lint / format / type toolchain on the base branch - install the dev dependencies and write the config (eslint.config.mjs, Prettier, tsconfig strictness + a typecheck script, .swiftlint.yml + swift-snapshot-testing, clippy/rustfmt) and an empty lessons home, keyed on the platform, idempotently and confirm-before-write. Use when the owner says "set up the toolchain", "wire up eslint/typescript here", "add linting/formatting to this repo", as the follow-up to setup-coduo-agents, or before an AFK run so lanes inherit deps they cannot install themselves.
disable-model-invocation: false
---

# Provision a project's toolchain

Install and wire the lint / format / type toolchain the project's platform
needs, so every session and every AFK lane starts from the same enforced
baseline. This is the **Layer 2** companion to `setup-coduo-agents`: that skill
wires agent context (plugins, AFK roles); this one changes the repo itself.

**Check the marketplace block first.** This skill assumes `setup-coduo-agents`
has already run: read the repo's `.claude/settings.json` for the
`extraKnownMarketplaces` entry for `coduo-agents`. If it is absent, say so and
offer to run `setup-coduo-agents` first - the two are ordered, because this
skill installs the commands that the repo's `defaultChecks` will then name, and
a toolchain wired into a repo with no agent context is half a setup.

Two invariants run through every step:

- **Install on the base branch, never in a lane.** AFK protects `package.json`,
  so a lane that adds a dependency has the edit reverted after it runs and its
  green invalidated - the epic then dies at the first lane that reaches for the
  package, with an error that never names it. Installing here, on the branch the
  epic forks from, is the only place deps reach the lanes. (`bun.lock` is not on
  the protected list, so on a bun repo commit the lockfile too.)
- **Idempotent.** Re-running converges to the same state: detect what is already
  wired and skip it. Never append a second config block or reinstall a present
  dependency.

## Steps

1. **Detect the platform.** Read `package.json` (deps + scripts), the lockfile,
   and top-level config files. Classify into exactly one: React web (Next.js /
   Vite), React Native / Expo, SwiftUI / native Apple, Tauri, other. Read the
   lockfile name to fix the package manager - `bun.lock`/`bun.lockb` → bun,
   `pnpm-lock.yaml` → pnpm, `package-lock.json` → npm, `yarn.lock` → yarn - and
   use it for every install command. Done when the platform and the package
   manager are both named.

2. **Diff against wired.** For the platform's row in the dispatch table below,
   check each dependency (present in `package.json`?) and each config file
   (present, and carrying the intended rule?). Produce one **missing list**:
   every dep not installed and every config not yet written or not yet strict.
   Done when every cell in the row is marked present or missing. If the missing
   list is empty, report "toolchain already provisioned" and stop here.

3. **Confirm before writing.** One compact message: the platform, the exact
   install command you will run, the exact files you will create or edit, and
   the base branch you are on. Ask whether to proceed, and whether any listed
   package is deliberately absent. Wait for the answer. Detection proposes; the
   user approves.

4. **Install.** Run the one install command for the missing deps with the
   detected package manager, as dev dependencies, from the repo root. On a bun
   repo, stage `bun.lock` alongside `package.json`.

5. **Write config, merging.** For each missing config, extend what the framework
   already ships before writing rules by hand: a React/Next repo's
   `eslint.config.mjs` extends `eslint-config-next` (or the flat preset) and
   adds only the plugins below; `tsconfig.json` gets `"strict": true` set
   in place, not a rewritten file. If a config file already exists, edit it -
   add the plugin to its existing array, flip the one field - rather than
   replacing it. Never emit a second `eslint.config.*`. Write the lessons home
   from `templates/` as the Lessons home section says.

6. **Verify by re-running.** Run the linter and the type check once
   (`<pm> run lint` / `<pm> run typecheck` / `<pm> run format:check`, or the platform equivalent) and
   confirm they execute. Then re-run step 2's diff: a correct run now reports an
   empty missing list. That empty second diff is the idempotency proof - record
   it. Then run the lesson probe (Lessons home section); done when it went
   green, then red, and the sample is gone. Do not commit; repo owners commit
   their own changes.

7. **Report.** The platform, the deps installed, the files written, and the
   verify result. Add the reminder that carries the whole point: **for an AFK
   run, these deps and the lockfile must be committed on the base branch before
   the epic starts** - a lane cannot install them. Any check line this run added
   to `.afk-setup/config.yaml` still needs a tier: send the user to `coduo-afk`
   S.3, which decides per-lane versus post-merge by the host singleton a command
   touches.

## Dispatch table

The platform decides the toolchain. Each row is this skill's single source of
truth for what that platform installs; the packages live nowhere else.

| Platform | Install (dev deps) | Config |
|---|---|---|
| React web (Next.js / Vite) | `eslint-plugin-react`, `eslint-plugin-react-you-might-not-need-an-effect`, `@shadcn/lint` (Tailwind v4 only), `@eslint-community/eslint-plugin-eslint-comments`, `prettier` + `prettier-plugin-tailwindcss` (exact versions); `cn` as a runtime dep in place of `clsx` + `tailwind-merge` (Tailwind v4 only) | `eslint.config.mjs` extending the framework preset + the two react plugins (`react-you-might-not-need-an-effect` at `recommended`) + the core `complexity` rule on + the `@/` import rule + `@shadcn/lint` registered with zero rules enabled + the ESLint lessons home; `.prettierrc.json` + `.prettierignore` and one format commit; `format`, `format:check` and `typecheck` scripts, each a check line; `.vscode/settings.json` + `extensions.json` for format and fix on save; `tsconfig.json` `"strict": true`; `src/lib/utils.ts` re-exporting `cn` |
| React Native / Expo | same two react eslint plugins + `@eslint-community/eslint-plugin-eslint-comments`; `@shadcn/lint` only if the repo uses NativeWind (Tailwind classes) | `eslint.config.mjs` (flat, no Next preset) + the core `complexity` rule on + `@shadcn/lint` registered (NativeWind only, zero rules enabled) + the ESLint lessons home; `tsconfig.json` `"strict": true` |
| SwiftUI / native Apple | SwiftLint via the SwiftLintPlugins SPM dependency, run through its **command plugin** as an explicit check line (`swift package plugin --allow-writing-to-package-directory swiftlint lint Sources App`); `pointfreeco/swift-snapshot-testing` (`from: "1.18.0"`, product `SnapshotTesting` on the test target); `brew install swiftlint swiftformat` only for a local-only convenience; when the repo ships `scripts/design/` board renderers (factory design-conformance, mac recipe ≥ 1.9.0): `python3 -m pip install --user --break-system-packages playwright && python3 -m playwright install chromium` — host-level, once per machine (brew's Python is PEP 668-managed; bare pip refuses); `brew install ast-grep` — host-level, once per machine | `.swiftlint.yml` at repo root; add the lint line to the repo's check lists (`.afk-setup/config.yaml`); one committed snapshot test with its `__Snapshots__/` reference; the ast-grep lessons home |
| Tauri | the React-web eslint deps for the webview; `@shadcn/lint` if the webview is Tailwind v4; `@ast-grep/cli` | `eslint.config.mjs` (with the core `complexity` rule on + `@shadcn/lint` registered, zero rules enabled) + the ESLint lessons home for the front end; `rustfmt.toml` + `clippy` (via `cargo clippy`) + the ast-grep lessons home for `src-tauri` |
| other | none automatic | ask the user what the project lints with before writing anything |

Notes that do not fit a cell:

- **`react-doctor`** is a plugin, wired by `setup-coduo-agents`, not an npm
  lint dep - do not install it here. If the repo wants its diff-scoped CI gate,
  add that as a separate CI step, not to `eslint.config.mjs`.
- **`eslint-plugin-react`** fills a real gap: Next does not bundle the full
  `plugin:react` ruleset, so a Next repo still needs it.
- **`@shadcn/lint` ([shadcn-ui/lint](https://github.com/shadcn-ui/lint)) is registered here, never configured here.** Per its own
  `SETUP.md`: install the package, add `plugins: { shadcn }` to the flat
  config, and stop — do not enable `shadcn/no-restyle` or any other rule, and
  do not add a component-override block. Choosing what a design system
  allows (contracts, `allow`/`deny`, custom messages) is a project decision
  made later, by the repo owner, against their own component set — this
  skill only makes the rule namespace available. Requires ESLint ≥ 9.30 and
  Node ≥ 20.19 (or Oxlint ≥ 1.80 if the repo lints with Oxlint instead — use
  `jsPlugins` in `.oxlintrc.json` there, same zero-rules rule). It targets
  Tailwind v4 class usage, not JSX/TS shape, so skip it entirely on a repo
  with no Tailwind (a bare React Native repo without NativeWind has nothing
  for it to check).
- **Prettier, matched to the code that is there.** Install `prettier` and
  `prettier-plugin-tailwindcss` with `-E`. Read the repo's majority style first
  and set only what differs from Prettier's defaults; a Coduo web repo is
  usually `{"semi": false, "printWidth": 100}`. Add `"plugins":
  ["prettier-plugin-tailwindcss"]`, `"tailwindStylesheet"` pointing at the CSS
  file with `@import "tailwindcss"` (v4 has no `tailwind.config`), and
  `"tailwindFunctions": ["cn", "cva"]` so classes inside those calls sort too.
  `.prettierignore` (Prettier already skips `.gitignore`): the lockfile,
  `vendor/`, `public/`, `*.md` and markdown content, and every **generated or
  synced** file — a test that compares generated output to a fresh build fails
  the moment Prettier touches it (Riverbend, 2026-10-21: the Style Dictionary
  token CSS), and a file synced from another repo drifts from its source. Grep
  for `do not edit`, `Generated by` and `synced from` before the format run.
  Then run `<pm> run format` as **its own commit** with no hand edits, and add
  that sha to `.git-blame-ignore-revs`. Skip `eslint-config-prettier`: the Next
  preset and the plugins above carry no formatting rules, so nothing conflicts.
- **One import form inside `src/`: the `@/` alias.** Editor auto-import copies
  whatever form sits nearby, so a mixed repo stays mixed. Add a
  `no-restricted-imports` pattern `{ regex: "^\\.\\./(?!.*\\.mjs$)", message:
  "Import from inside src/ through the @/ alias, not ../." }` over `src/**`.
  The `.mjs` exception lets `src/` tests reach scripts and configs outside it
  (`../../scripts/x.mjs`); check that every `../` left after the rewrite is one
  of those. ESLint replaces a rule's options between config objects, so put the
  pattern into any `no-restricted-imports` block the repo already has, and
  repeat it in a block for each folder that block `ignores`. Rewrite the
  existing `../` imports to `@/` before turning the rule on (a short node
  script that resolves each specifier against the file's directory).
- **Format and fix on save, in VS Code.** Write `.vscode/settings.json` at the
  repo root (merge into one that exists): `"prettier.requireConfig": true`, so
  only folders with a Prettier config format; a
  `"[javascript][javascriptreact][typescript][typescriptreact][json][jsonc][css]"`
  block setting `editor.defaultFormatter` to `esbenp.prettier-vscode`,
  `editor.formatOnSave: true` and `editor.codeActionsOnSave: {
  "source.fixAll.eslint": "explicit" }`; `"eslint.workingDirectories": [{
  "mode": "auto" }]` for a package in a subfolder; and
  `"typescript.preferences.importModuleSpecifier": "non-relative"` (and the
  `javascript.` twin). The last one is what makes auto-import match the `@/`
  rule: VS Code's default, `shortest`, wrote `../landing/closing` between two
  sibling folders on Riverbend. `.vscode/extensions.json` recommends
  `esbenp.prettier-vscode` and `dbaeumer.vscode-eslint`. The Prettier extension
  (v12) finds a subfolder's `.prettierignore` from the edited file, so leave
  `prettier.ignorePath` alone.
- **`typecheck` is `next typegen && tsc --noEmit`** on Next (plain `tsc
  --noEmit` on Vite). Without `next typegen`, a fresh worktree reports
  `RouteContext` and `LayoutProps` as missing names. `typegen` loads
  `next.config.ts`, so the check line takes the same inline env values as the
  build line. Add `<pm> run format:check` and `<pm> run typecheck` to the check
  lists next to `<pm> run lint`.
- **`cn` ([shadcn-ui/cn](https://github.com/shadcn-ui/cn)) replaces `clsx` +
  `tailwind-merge`** on Tailwind v4: same output, about 30× faster. Install it
  `-E` (it is 0.x), remove the two packages if nothing else in `src/` imports
  them, and keep `src/lib/utils.ts` as `export { cn } from "cn"`: `shadcn add`
  writes components that import `cn` from `@/lib/utils`. On Tailwind v3 keep
  `tailwind-merge` v2.
- **Cyclomatic complexity is eslint core, not a dependency.** The `complexity`
  rule ships with eslint itself and is off by default; turn it on in the flat
  config rather than adding a linter for it - `rules: { complexity: ["warn",
  { max: 20 }] }` (20 is eslint's own default threshold). Set it in the same
  config object as the plugins above; if a `complexity` entry already exists,
  leave the repo's chosen threshold alone.
- Prefer the framework's own lint command if one exists (`next lint` history,
  `expo lint`) over inventing a `lint` script.
- **Snapshot testing is toolchain, not a feature.** It is the only test gate
  that sees a screen: quillnote ran 55 tasks green through five gates and
  shipped screens matching no board. Prove it the way SwiftLint is proved: a
  test that snapshots `NSHostingView(rootView:)` with a frame set — the SwiftUI
  `.image` strategy is iOS/tvOS only, and a zero-sized hosting view **traps**
  (`Fatal error: View not renderable`) rather than failing — first run records
  and fails, second passes — then commit the reference. Views the package
  compiles run under `swift test`; views in `App/` need the **host-app test
  target** run by `xcodebuild … test` (factory recipes ≥ 1.6.0 ship it; an
  older repo copies quillnote' `project.yml`: a `bundle.unit-test` target with
  explicit `TEST_HOST`, `BUNDLE_LOADER` and `PRODUCT_MODULE_NAME`, because a
  `PRODUCT_NAME` with a space breaks all three derived values). After renaming
  or adding a test file, `xcodegen generate` again — the gate line's prefix
  already does.
- **Prefire turns every `#Preview` into a snapshot test** — one generated test
  per preview, zero hand-written snapshot code; proven on quillnote
  (2026-09-03: 17 tests from 17 previews). Pin the package to `main` revision
  `a895478bf5a4e9dfe6bad9c1b6e1bf30d6c2602d`: the 5.7.1 tag does not build for
  macOS (unconditional UIKit import) despite Swift Package Index's claim. The
  xcodebuild gate needs `-skipPackagePluginValidation` for its plugin, and a
  `PreviewTests.generated/` folder is grouped-mode leftover — never commit it.
  Before the recording run, audit every `#Preview` for a live singleton,
  on-disk store or clock and hand it a deterministic stand-in: the recording
  is a committed baseline, and quillnote baked the author's real notes and a
  trial-day countdown into PNGs — the countdown went red twenty minutes after
  recording and failed two waves' baseline gate. Budget for the determinism
  pass to surface defects, not cause them: rendering a branch the live
  preview never reached is new coverage, and on quillnote it showed the
  empty state drawn outside the note card against a board that draws it
  inside — there since day one, never in a snapshot.
- **A board-versus-build comparison is a shell check, and it runs on Opus.**
  `claude -p` reads a local PNG named in the prompt (verified 2026-09-04:
  `claude --model claude-haiku-4-5-20251001 -p "Read the image at <path>
  ..."` returned a board frame's icon count and hint text), and checks run
  in the lane's worktree with `claude` on `PATH`, so an element inventory
  can be a `checks:` entry. The model is Opus, measured, not preferred:
  three sub-agents, identical prompts, the same five board-versus-build
  pairs, the closed icon set supplied to each, six decisive findings scored.

  | Model | Found | Tokens | Time |
  |---|---|---|---|
  | Haiku 4.5 | 2/6 | 45,423 | 34s |
  | Sonnet 5 | 4/6 | 70,030 | 70s |
  | Opus 5 | 6/6 | 61,701 | 54s |

  Haiku found a defect in one pair and missed it in another on the same
  image, and missed a live regression outright. Opus spent fewer tokens than
  Sonnet: the task is input-heavy, and a smaller model spends its output
  describing where a larger one decides. Every coduo skill that compares a
  screen against a board points here for the model.
- **The vision pass has two dependency tiers, and only one is usually
  missing.** The shell gates (`vision-judge.sh`, `vision-pass.sh`,
  `vision-pass-all.sh`) need `claude`, `jq` and `sips` — all present on any
  machine running this skill. The Python board renderers
  (`render-boards.py`, `board-regions.py`, `board-spec.py`,
  `render-mutants.py`) need Playwright with its Chromium fetched, plus
  network at render time (the boards load Google Fonts). This is a
  host-level install, not a repo dep — lanes inherit the host's Python
  environment — so check `python3 -c "import playwright"` and install once
  per machine, before the first design wave, or the first design task dies
  in an unattended lane on a ModuleNotFoundError no ticket explains. On a
  Homebrew Python the install needs `--user --break-system-packages`
  (PEP 668), and a `brew upgrade` that bumps the Python minor version
  empties the user site — re-run the check after brew upgrades. Verify with
  a real launch, not the import: `python3 -c "from playwright.sync_api
  import sync_playwright"` then a one-page `chromium.launch()`.
  (Learned 2026-09-05, promoting the quillnote pass into the factory: the
  templates ship the scripts, nothing shipped the interpreter's deps.)
- **The SwiftLint build-tool plugin form is a trap** (found on quillnote,
  2026-09-02, SwiftLintPlugins 0.65.1 / Swift 6.2): attached to targets it
  compiles and reports nothing — a deliberate `force_unwrapping` violation
  built clean. The command plugin lints the same config correctly and also
  covers `App/` sources the package plugin never sees. Wire the command
  plugin as a check line and prove it with a violation probe before
  reporting done.

## Lessons home

A **lesson** is how a fixed review finding stays fixed: a lint rule written
test-first (its red fixture is the pre-fix code and must report; its green
fixture is the fixed code and must stay silent) or a standards line. Closeout
writes lessons (afk-claude#152); this skill gives each repo an empty,
already-gated home for them, so the first closeout has somewhere to write.
Worked example: harbour `eslint.lessons.mjs` and
`docs/agents/lesson-rules-audit.md`.

**ESLint lessons home** (React web, React Native, Tauri front end):

- Copy `templates/eslint.lessons.mjs` to the repo root: a local `lessons` plugin
  with zero rules, one rule per lesson, each built by the `lesson(selector,
  message)` factory. One rule per lesson because ESLint replaces a rule's
  options across config objects rather than merging them, so lessons written as
  `no-restricted-syntax` entries overwrite each other on overlapping files.
- In `eslint.config.mjs`: `import { lessons } from "./eslint.lessons.mjs";` and
  spread `...lessons` into the exported array.
- Copy `templates/eslint.lessons.test.mjs` into the repo's unit suite (wherever
  its runner collects tests; fix the import path). It iterates every rule in the
  plugin and fails when one lacks an `invalid` (red) or a `valid` (green) case.
  The template is vitest; on jest, drop the `vitest` import and the three
  `RuleTester.*` lines.
- Described suppressions: spread `comments.recommended` from
  `@eslint-community/eslint-plugin-eslint-comments/configs` and set
  `"@eslint-community/eslint-comments/require-description": "error"`, so every
  `eslint-disable` carries `-- <why>`. ESLint core parses `--` descriptions but
  has no option to require one (checked against the 10.x docs, 2026-09-28).
- The repo's existing lint and unit-test check lines already run the lessons.

**ast-grep lessons home** (SwiftUI / native Apple, Tauri `src-tauri`):

- **Swift: the factory is the source.** A repo generated from
  coduo-swiftui-factory already carries this home (`sgconfig.yml`,
  `.ast-grep/`, the check lines); verify and skip. For any other Swift repo,
  copy those files and check lines from the factory's
  `recipes/<recipe>/template/` rather than from the bullets below, which
  describe the shape (coduo-swiftui-factory#45).

- Install: on a Swift repo, `brew install ast-grep`. The repo has no
  `package.json`, and a host binary is lighter than bringing Node in to pin one
  linter; lanes inherit the host's `PATH`, so confirm `ast-grep --version` here,
  once per machine. On Tauri, `@ast-grep/cli` as a dev dep: the lockfile pins
  the version and lanes inherit it. Call the binary `ast-grep`; `sg` is a
  system command on Linux.
- `sgconfig.yml` at the repo root, with `.ast-grep/rules/` and
  `.ast-grep/test/` created empty (a `.gitkeep` in each):
  ```yaml
  ruleDirs:
    - .ast-grep/rules
  testConfigs:
    - testDir: .ast-grep/test
  ```
- Add three lines to `defaultChecks` in `.afk-setup/config.yaml` (prefix
  `<pm> exec` on Tauri). `ast-grep test` passes a rule with no test file, so
  the third line is the fixture gate:
  ```yaml
  - ast-grep scan --error
  - ast-grep test --skip-snapshot-tests
  - 'for r in .ast-grep/rules/*.yml; do [ -e "$r" ] || continue; id=$(sed -n "s/^id: *//p" "$r"); grep -lqs "^id: *$id$" .ast-grep/test/*.yml || { echo "lesson $id has no fixtures in .ast-grep/test/"; exit 1; }; done'
  ```
- SwiftLint `custom_rules` holds token bans only; structural lessons live here.
  Wiring SwiftLint itself into the factory is coduo-swiftui-factory#45.

**Lesson probe** (step 6's done-criterion, once per lessons home):

1. Add one throwaway sample lesson with a red and a green fixture. ESLint:
   selector `CallExpression[callee.name='eval']`, red `eval(x)`, green
   `evaluate(x)`. ast-grep, Swift: `pattern: try! $E`, red
   `let a = try! load()`, green `let a = try load()`.
2. Run the suite (`<pm> exec vitest run <test file>` / `ast-grep test
   --skip-snapshot-tests`): it passes.
3. Loosen the rule to match everything (`CallExpression`; `kind:
   call_expression`): it fails on the green fixture. Record both outputs.
4. Remove the sample and its fixtures and re-run: it passes on the empty home.

## When to reach for it

After `setup-coduo-agents` on a fresh repo, and again whenever a repo gains a
platform whose toolchain it lacks. Safe to re-run any time - step 2 makes a
no-op run cheap and silent.
