# Audit method

How to run audit mode's steps 2 to 7. The evidence rule and the benefit rating are
adapted from littlebearapps/pitchdocs `feature-benefits` (MIT); the baseline and the
tiering follow April Dunford's positioning order: competitive alternative first,
then unique attributes, then value.

## The baseline alternative and named competitors

Dunford's question: if this product did not exist, what would the buyer do? Answer
with their **default**, the thing they already have:

- **The platform underneath, used as is.** A client or layer built on someone else's
  service is measured against that service's own UI and API. The buyer already has
  it, for free.
- **The status quo.** A spreadsheet, a doc, a shared inbox, doing nothing.
- **An incumbent the buyer already pays for**, only when memory or research shows
  the target buyer has it today (a `Substitute` PM entry, a study naming switchers).

Product memory and pricing docs usually name **rivals** instead: the paid tools the
owner wants to be compared with. They go on the `Named competitors:` header line, each
with its source, and never replace the baseline. Every named rival is a row of the
competitor roster with `Named: yes` ([competitor-roster.md](competitor-roster.md)); add
the row when it is missing. When memory and research disagree,
cite both and pick the buyer's default, not their best option.

A Differentiator aimed at a rival still has to beat the baseline to be Must-have:
"your data stays in GitHub" beats a SaaS rival and is parity against GitHub itself.

## Scope: what counts as a feature

A feature is something an end user reaches in the shipped build: a user-facing route,
screen, command, MCP tool or CLI. Walk every such surface. Use the repo's own map
first (`CONTEXT.md`, an architecture doc, `graphify explain` when a graph exists),
then confirm in code:

| Surface | Where to look |
|---|---|
| Screens and routes | router config, `app/` or `pages/` directories, view registries, command palettes |
| Actions | command registries, keyboard shortcut maps, menu definitions, context menus |
| API and webhooks | `api/`, route handlers, server actions |
| Agent and CLI surface | MCP tool lists, CLI entry points, `bin` in the manifest |
| Integrations | OAuth scopes, third-party clients, import and export paths |
| Plans and limits | entitlement checks, paywall gates, plan constants |
| Platform properties | offline cache, local-first storage, sign-in model, data custody |

Out of scope, and named in the one-line `## Scope notes`: dev-only and debug routes
(`import.meta.env.DEV`, `NODE_ENV`, harness-only endpoints), internal and test routes,
mock harnesses, lifted code no route reaches, and strings no component renders. A
feature behind an allowlist or env flag is in scope as an `Extra` with `(gated)` in
its Benefit.

Group the sub-capabilities of one job under one row ("issue detail editing: comments,
sub-issues, dependencies"). Internal plumbing is not a feature; it becomes one only
when it gives the buyer a property they can notice: speed, offline use, data that
never leaves their account. Name the property, cite the plumbing.

## Evidence

Each Evidence reference is `path:line`, or `path` plus a symbol name a grep finds
(`src/x.ts` `fnName()`). Write the full path every time, never `:351` for "same file
as before". A bare directory is not evidence. A test file is supporting evidence
only; cite the code it tests.

## Claims

Read the public website (the `landing/` app, a `site/` or `web/` folder, or marketing
routes inside the app), its pricing and policy copy, the README, user docs and product
proposal docs. Quote each feature claim and match it to a feature. Pricing and policy
lines ("All future features included", "cancel anytime") are claims too. A claim from
a proposal doc carries `(proposal)` after its source.

- **Claimed but not found in code**: no code does it at all. Record the greps you ran.
- **Claims the code contradicts**: code exists and does something else ("4 modules"
  while six render, "published the moment you tag" against an hour's cache, a free
  tier promising features the entitlement code keeps paid). Cite the contradicting
  code.

Search with two vocabularies (the page's word and the code's word) before declaring a
miss; a single empty grep is one search, not proof.

## Benefit and strength

Write each benefit as an outcome for the buyer, with the mechanism behind it:
`<outcome> — <mechanism>`. "Has caching" is a feature; "boards open instantly from
cache" is the benefit.

- **Strong**: the code directly produces the outcome.
- **Medium**: a reasonable inference from the code.
- **Weak**: speculative, or the outcome needs something the code does not do. Drop
  the benefit; when no Strong or Medium benefit is left, the feature goes to
  `## Dropped (weak benefit)` with its evidence and a one-line reason.

No "simple", "easy" or "powerful" without the mechanism that shows it.

## Tiering

Apply in order.

1. **Must-have: 1 to 3 rows.** All of: the baseline lacks it, the benefit is Strong,
   and a buyer choosing between this product and the baseline would name it. Only a
   `decided` or `supported` memory entry, or an owner-decided doc (an ADR, a
   `decision.md`), breaks a tie; `proposed` docs inform the reading and decide
   nothing. Fewer than three is fine; padding the tier is the failure. Landing use is
   `Hero` or `Features section`.
2. **Good-to-have: up to 5 more rows (ranks 4 to 8).** Either it beats the baseline
   less decisively, or it is parity the target buyer would refuse to switch without.
   Landing use is `Features section`, `Pricing page` or `FAQ`.
3. **Extra: every other row.** True and evidenced, but not a reason to switch.
   Landing use is `Optional` by default; see the format rules in SKILL.md.

A feature the baseline also has is never Must-have, however good the implementation.
Better execution of a baseline feature (faster, fewer clicks) is Good-to-have at most
unless product memory records buyers switching for exactly that.

**Positioning flags.** When the owner's headline promise (a `decided` Product promise,
the live hero line) tests as parity with the baseline, tier the row on its merits and
add a `## Positioning flags` entry: the promise quoted, its source and status, what it
tests as, and which row carries it. The tier never moves silently to hide the
mismatch, and the flag never promotes the row.

## The check

Step 7 runs this from the repo root, at the commit the header names. It reads refs
from two places only: the table's Evidence column and the `## Sources` list. Prose
elsewhere (a domain, `process.env`, a URL) is never read as a file. A ref is a file
when `git ls-files` lists it, dotfiles and extensionless names such as `Makefile`
included; a path-like ref that is not listed is `MISSING`, and any other backticked
token in the cell (a symbol, a version) is skipped. It prints `check finished` and
nothing else when every cited file is tracked, every line number is inside its file,
and every Evidence cell has at least one ref that resolves to a tracked file.

```bash
f=docs/product/features.md   # or the caller's output path
awk -F'|' '
  function refs(row, s) { print row "\t"; while (match(s, /`[^`]+`/)) { print row "\t" substr(s, RSTART + 1, RLENGTH - 2); s = substr(s, RSTART + RLENGTH) } }
  /^## / { src = ($0 ~ /^## Sources/) }
  { gsub(/\\\|/, "") }
  $3 ~ /^ (Must-have|Good-to-have|Extra) $/ { refs($2, $4); next }
  src { refs("-", $0) }
  END { print "-end-\t" }' "$f" |
while IFS=$'\t' read -r row ref; do
  if [ "$row" != "$cur" ]; then
    case $cur in ''|-) ;; *) [ "$hit" = 1 ] || echo "NO-FILE  $cur" ;; esac
    cur=$row; hit=0
  fi
  [ -n "$ref" ] || continue
  p=${ref%%:*}; l=${ref#"$p"}; l=${l#:}; l=${l##*-}
  case $l in *[!0-9]*) l= ;; esac
  case $p in *'*'*|*://*) continue ;; esac
  if [ -f "$p" ] && git --literal-pathspecs ls-files --error-unmatch -- "$p" >/dev/null 2>&1; then
    hit=1; n=$(awk 'END{print NR}' "$p")
    [ -n "$l" ] && [ "$l" -gt "$n" ] && echo "PAST-EOF $ref (file has $n lines)"
  else
    case $ref in */*|*:[0-9]*|*.[A-Za-z]*) echo "MISSING  $ref" ;; esac
  fi
done
awk -F'|' '{ gsub(/\\\|/, "") } $3 ~ /^ (Must-have|Good-to-have|Extra) $/ && $4 ~ /`:[0-9]/ { print "SHORTHAND" $2 }' "$f"
echo "check finished"
```

A `MISSING` line for a doc listed under "Not present" means it was written in
backticks; write missing files as plain text.
