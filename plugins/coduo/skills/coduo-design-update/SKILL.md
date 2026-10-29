---
name: coduo-design-update
description: Treat a UI branch's design as final and bring everything else into line with it — tests, screenshot and accessibility baselines, the design-system docs and the product docs. Asks before any removal that breaks a business rule or an ADR.
---

# Coduo design update

The design on this branch is **final**. Its JSX, Tailwind classes, copy and
layout are the spec. Every test, baseline and doc that describes the old
design is stale, and your job is to bring each one into line with the branch.

This exists because designs were being overwritten. A designer's branch
landed with tests written against the old design, her machine could not
re-record the baselines, and the next agent "fixed" the red tests by editing
the design back. Here the direction is always the same: **the tests follow
the design.**

## The one exception: a removal against a rule

A design can remove something a business rule or an ADR requires: a consent
step, a price shown before payment, a link the ADR makes mandatory. That is
the only reason to stop. Everything else goes ahead on the fact that the
design is final.

## Step 1 — Read the design diff

```bash
git fetch origin
git log --oneline origin/<base>..HEAD
git diff origin/<base>...HEAD --stat
```

`<base>` is the branch this one will merge into, usually `main`. List what the
design changed, per screen or component: elements **added**, **changed**
(copy, order, role, route, styling) and **removed**. Read the JSX, not just the
stat: a renamed button or a removed heading is what breaks a locator.

**Done when** you have a list of every added, changed and removed element,
each with its file.

## Step 2 — Check every removal against the rules

For each **removed** element or behaviour, search the repo's business rules
and ADRs for it. Find where they live from `AGENTS.md`, `CONTEXT.md` or
`docs/README.md` (harbour: `docs/product/business-rules.md` and `docs/adr/`).
Search by the element's purpose, not only its name: a removed "You'll be
charged $X" line matches a rule about showing the price.

- **A rule or ADR requires it:** stop. Ask the user, quoting the rule with its
  file and line, the removed element with its file, and what would happen
  without it. Carry on with everything else while you wait, and leave that
  one removal alone until they answer.
- **No rule requires it:** the removal stands. Note it for Step 4.

**Done when** every removal is either cleared or put to the user as a
question.

## Step 3 — Bring the tests into line

Run the gate the way the repo's `AGENTS.md` or `.afk-setup/config.yaml` defines
it. Reset any local database or stack state first (harbour: `pnpm run test:db`
before `pnpm run test:e2e`), because leftover state from an earlier run fails
tests for reasons that have nothing to do with the design.

Run the e2e suite **once**, recording only the snapshots that differ:
`pnpm run test:e2e --update-snapshots=changed`. A design that touches shared
components (buttons, global CSS, the header) moves baselines on screens no
file filter would name, so this one full pass is how you find them all.

Then go through what changed, in two kinds:

- **It describes the old design.** A re-recorded aria snapshot or screenshot,
  a locator for a renamed element, an asserted string that changed. For each
  re-recorded PNG, open it next to the old one (`git show HEAD:<path>`) and
  confirm the difference is this branch's design and nothing else; revert any
  that is not. Update locators and strings to the new design.
- **It asserts behaviour the design did not change.** A broken link, a crash, a
  lost handler, a form that no longer submits. The design is still final, so
  leave the JSX as it is and report the break to the user with the failing
  test and the element. The test stays red until they decide.

To confirm, rerun only what failed: `pnpm run test:e2e --last-failed`. Do not
run the full suite a second time; the first pass already ran everything else
green. Run unit tests and typecheck as the gate defines them.

Record baselines on the platform the repo's baselines come from. Harbour's
PNGs are macOS renders, so run on a Mac; a Linux run re-records every
screenshot and breaks them for everyone else.

**Done when** the `--last-failed` rerun and the rest of the gate pass, or every remaining failure is one you have
reported as a behaviour break.

## Step 4 — Bring the docs into line

- **Design system**: the tokens, components and screen references the repo
  keeps (harbour: `docs/design/`, including `INDEX.md` and the screen folders).
  Update each entry the design changed, so the next agent builds from the new
  design.
- **Accessibility**: the accessibility baselines (`.aria.yml`) moved with
  Step 3. Also update any written accessibility notes whose element was
  renamed, restructured or removed.
- **Product docs**: for each removal cleared in Step 2, update the glossary
  (`CONTEXT.md`), the product docs and any help or content page that still
  describes it.

**Done when** a search for each removed or renamed element's name finds no
doc that still describes the old design.

## Step 5 — Commit and report

Commit on the design branch, separate from the design's own commits, so the
two can be read apart:

```
test: follow the final design of <branch>
docs: follow the final design of <branch>
```

Push only when the gate is green and the user asked for a push. Then report:

- the tests changed, and why each one was stale
- every baseline re-recorded, with a one-line description of what changed in it
- the docs updated
- each removal put to the user, with the rule it touches
- each behaviour break left red, with its test
- before/after screenshots of every route whose rendering changed, posted
  on the PR as the side-by-side table in `coduo-implement` rule 9 (blob
  `?raw=true` URLs). Evidence only: it blocks nothing.
