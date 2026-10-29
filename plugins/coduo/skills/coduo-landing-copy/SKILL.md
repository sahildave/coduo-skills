---
name: coduo-landing-copy
description: "Landing-page copy consultant for a Coduo product: grade each section of the existing landing page as placeholder, draft or polished, suggest copy grounded in the product's features list, and show 2-3 options per changed section on the real landing route behind a variant switcher, then fold the pick in and remove the switcher. Use when reviewing, rewriting or filling in landing or homepage copy, or when the hero, section text or calls to action need work."
disable-model-invocation: false
---

# Landing copy

The page stays; the words change. This skill works on the landing page the product
already has, in its own components and styling. A new layout or a redesign is
`coduo-product-prototype` or the repo's design skill, not this one.

Three leading words run through it:

- **Maturity**: how finished a section's copy is. One of `placeholder`, `draft`,
  `polished`. It decides how hard you touch the section.
- **Variant**: one candidate version of a section's copy, rendered on the real page.
- **Fold**: putting the picked variant into the real component and deleting the rest.

## Voice

Plain, down-to-earth and dry by default: the `unslop` voice, which is the house voice.
No boasting, no hustle, no hype. If the user names another preset in the request
("technical", "warm", "playful"), use it for tone and keep every rule below anyway.

These rules bind every line you write for the page:

1. Hero and section copy stays at 20 words or fewer per sentence.
2. Use concrete verbs and nouns in place of "innovative", "seamless", "world-class",
   "supercharge" and "unlock".
3. Claim only what ships today. A feature that is not built yet is not on the page.
   features.md's Evidence column is the test.
4. **Swap test.** A line that would work unchanged on a competitor's site gets
   rewritten until it names something only this product does or says.
5. If a section reads like a SaaS landing page, rewrite it drier.
6. Each section passes the **5-second test** on its own job: a visitor can say what it
   is, what is in it for them, and what to do next. The hero must pass all three.

The repo's own voice doc wins where it is stricter (step 1 finds it).

## Steps

### 1. Read the inputs

Read, in this order:

1. The repo's `AGENTS.md` and `CLAUDE.md`, the root ones and any inside the landing
   folder. Note i18n (are strings in locale files?), screenshot or e2e baselines that
   cover the landing page, and anything that owns the landing folder.
2. `docs/product/features.md`. It is the `coduo-product-market` skill's output: a table
   `Feature | Tier | Evidence | Benefit | Beats the baseline because | Landing use`,
   tiers Must-have, Good-to-have and Extra, and a header naming the **Baseline
   alternative** (what a visitor uses today instead) and the **Named competitors**
   (paid rivals the owner compares against). Its `## Positioning flags` and
   `## Claims the code contradicts` sections are findings for step 2: a flagged
   promise is parity, so it never leads the hero as the reason to switch, and a
   contradicted claim is copy to rewrite. If it is missing, stop and tell the
   user to run `coduo-product-market` in audit mode first, and offer to run it. Copy
   written without it has nothing to be true to.
3. `docs/product/product-market.md` if present: the PM-NNN signals and their
   "Landing-page use" fields.
4. The repo's design or voice doc: a design skill under `.claude/skills/*-design/`
   (its copy or voice section), `docs/design/`, or a `DESIGN.md`.
5. The landing source: the file that serves `/` on the marketing site. List the
   candidates from tracked files, so build output and agent worktrees stay out:

   ```bash
   git ls-files | grep -E '(^|/)(app/(\([^/]*\)/)?page\.[jt]sx?|pages/index\.[jt]sx?|index\.astro|routes/\+page\.svelte|index\.html)$' \
     | grep -vE '^(docs|\.claude|e2e|tests?)/'
   ```

   A product app's shell (a bare Vite `index.html` mounting a root div) is not the
   landing page; the marketing route usually sits in `landing/`, `web/`, `site/` or a
   route group like `app/(landing)/`. If two candidates remain, ask. Read the page file,
   every section component it renders, top to bottom, and any data or content file
   those components take their strings from (a `landing-data.ts`, a content folder).
   Note the tests that assert on copy strings: the fold has to update them.
6. Any discussion or spec already deciding landing copy: `ls docs/product/` for a
   folder named for the landing page, and open landing-copy tickets. A decision recorded
   there is input, not something to re-propose.

**Done when** you can name the landing route file, every section component in render
order, the baseline alternative, the Must-have features, the voice doc (or "none"), and
the repo rules that touch landing copy (i18n, baselines). If features.md is missing,
you have stopped and told the user.

### 2. Grade maturity, then report

Walk the page section by section (hero, each feature block, social proof, pricing
teaser, FAQ, final call to action, footer) and give each one a maturity:

| Maturity | Signs | What you do |
| --- | --- | --- |
| `placeholder` | lorem ipsum, TODO, template copy ("Build faster", "Your all-in-one platform"), a feature that does not exist, sample names | Write new copy from features.md |
| `draft` | real and about this product, but vague, long, boasting, fails the swap test, or buries the benefit | Full review with the `copy-editing` skill's sweeps |
| `polished` | specific, passes the voice rules and the 5-second test | Minimal edits; say "leave it" when nothing is wrong |

Then map features.md onto the page. Every Must-have feature the page never mentions is
a finding, and these go first in the report. A section that mentions an Extra-tier
feature while a Must-have is missing is the second finding.

Write the report before changing anything:

```markdown
## Landing copy: <product>, <date>
Route: <file>. Baseline alternative: <from features.md>. Voice: <preset>.

### Missing Must-have features
- <feature>: not on the page. Belongs in <section>. Evidence: <features.md Evidence>.

### Sections
| # | Section (component) | Maturity | Why (quote the line) | Proposed action |

### Quick wins / High impact
- Quick win: <one-line edits on draft and polished sections>
- High impact: <hero clarity first, then missing Must-haves, then placeholder sections>
```

Put the value proposition (the hero) first under High impact whenever it fails the
5-second test: nothing lower on the page helps a visitor who left at the hero.

**Done when** every section in render order has a row with a quoted line as evidence,
every Must-have feature is either matched to a section or listed as missing, and the
report is in front of the user. Ask which sections to work on before step 3.

### 3. Build variants on the real page

For each section the user picked, write 2 or 3 variants. Variants differ in message or
angle (lead with the baseline pain, lead with the Must-have feature, lead with the
outcome), not in wording. Two variants that make the same point in different words are
one variant: replace one. A `polished` section the user picked still gets variants,
but one of them is the current copy.

Render them with the `prototype` skill's UI branch, sub-shape A: the existing landing
route and the `?variant=` search param. That skill calls copy-only variants an
anti-pattern; here they are the point, so this skill overrides it: variants change
copy only, and the page's components, styles and layout stay untouched.

The switcher is a **DialKit** panel (npm `dialkit`, github.com/joshpuckett/dialkit), not
that skill's `PrototypeSwitcher` bar: one select per picked section, listing its
variants. DialKit is the view; the URL is the state. The panel reads its defaults from
`?variant=` and writes each pick back to it, so a link reproduces the selection.

- Read DialKit's README and `node_modules/dialkit/dist/*.d.ts` before writing the panel,
  and use the calls they declare. The working reference is harbour
 : `src/components/dev-persona-bar/dev-persona-bar-view.tsx`
  (`DialRoot`, `useDialKitController`; DialKit exposes values, not a change event, so
  write the URL on the difference) and `dev-persona-bar.tsx`, which loads that view
  through `next/dynamic`. Load the panel the same way, so no route bundles it statically.
- Import a local `dialkit.css`: the package's `dist/styles.css` with its Google Fonts
  `@import` removed. Never import the package's own CSS.
- Render the panel only when `process.env.NODE_ENV !== 'production'`.
- If the landing package lacks `dialkit`, run `npm install -D dialkit` there: a dev
  dependency, never a runtime one (harbour keeps it in `devDependencies`). Say so in
  your step 3 message: the fold uninstalls it.

Three rules make the fold check in step 5 reliable:

- `variant` is the only search param you add. Its value names the section and the
  variant: `?variant=hero-A`, `?variant=features-C`. To show a mix, list values in the
  same param (`?variant=hero-A,features-C`); never add a second key such as `?hero=`.
- Every variant component's name starts with `CopyVariant` (`CopyVariantHeroA`).
- Every branch that reads `variant`, every variant string constant, and every file you
  add (the panel and `dialkit.css` included) carries the comment marker
  `landing-copy-variant`, on the same line or the line above.

If the repo keeps strings in locale files, put variant strings next to the component as
marked constants; locale files get only the winner, at the fold.

Run the landing dev server (the repo's `.claude/launch.json` entry or its `package.json`
script) and open each variant once to check it renders.

**Done when** each picked section has 2-3 variants with distinct angles, every variant
URL loads, and the user has the URLs, with one line per variant naming its angle.

### 4. Pick

The user picks per section, or asks for another round. Another round replaces the
losing variants; keep at most 3 alive.

### 5. Fold

Nothing checks the landing page for a leftover switcher except this step. Some repos
leave the landing folder out of their screenshot gate on purpose, so a stray `?variant=`
branch can reach production unseen. Fold before any commit:

1. Write the winning copy into the real components (and locale files, if the repo has
   them), with no variant condition around it. Update any test that asserted on the old
   strings.
2. Delete the DialKit panel and its `dialkit.css`, every losing variant and its
   constants, every `CopyVariant*` component and every file you added for variants. If
   step 3 installed `dialkit`, run `npm uninstall dialkit` in the landing package (or
   its package manager's equivalent).
3. Run the fold check from the repo root, with `<landing>` set to the landing folder.
   The first grep covers the whole repo, because the panel can sit outside the landing
   folder (`src/components/`). It names DialKit's symbols and CSS file, never the bare
   package name, so a lockfile cannot match. The second reads the `variant` param,
   which docs mention in prose, so it stays inside `<landing>`:

   ```bash
   landing='<landing>'   # quoted: route groups such as src/app/(landing) have brackets
   git grep -nE --untracked \
     'landing-copy-variant|CopyVariant|DialRoot|useDialKitController|dialkit\.css' ; \
     echo "repo-check exit=$?"
   grep -rnE --exclude-dir=node_modules --exclude-dir=.next --exclude-dir=dist \
     '[?&]variant=|get\(.variant.\)|searchParams\??\.variant\b' "$landing" ; \
     echo "landing-check exit=$?"; git status --short
   ```

   Both greps must print nothing and both exits must be `1`. Show the output to the
   user verbatim. A match is a leftover: remove it and run again. The one exception is
   a DialKit panel that was in the repo before step 3: leave it, and name it to the
   user. In `git status`,
   every new file must be one the user meant to keep; an untracked variant file is a
   leftover too.
4. Run what the repo's rules (from step 1) require for landing changes: its lint and
   typecheck for the landing package, and its screenshot or e2e tests if they cover the
   landing page. A screenshot that changed on purpose is re-baselined in the same commit,
   the way the repo's rules say.

**Done when** both fold-check greps printed nothing with `exit=1`, their output is in front of the
user, the repo's landing checks pass, and the winning copy renders on the plain route
with no `?variant=`.

## References

[references/sources.md](references/sources.md) credits the ideas borrowed here and
their licences. Read it when you change the rules.
