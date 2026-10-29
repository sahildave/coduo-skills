# Competitor roster and coverage ledger

The shared rule for every Coduo skill with a competitor step (`coduo-pricing`,
`coduo-seo-pain-point`, `coduo-seo-ai-answers`, `coduo-seo-writer`, and this skill's
`Named competitors:` line). Each of them starts from the roster and ends with every
roster tool either covered or logged as not covered. A drop with no row is a **silent
drop**, and a silent drop is the one outcome this rule exists to prevent.

## The roster

One file per product repo: `docs/research/competitors/README.md`. It lists every tool
the product has met, profiled or not. Profiles stay where the repo keeps them; the
roster points at them.

| Tool | Slug | Group | Named | Profile | Matrix | Profiled | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Linear | linear | issue tracker | yes | `linear.md` | `../competitor-matrix/linear.json` | 2026-09-30 | active |
| Tower | tower | price anchor | no | `tower.md` | `../competitor-matrix/tower.json` | 2026-09-30 | active |

- **Group** says what the tool is to this product: a rival, the baseline platform, or a
  `price anchor` (a tool priced against, not competed with).
- **Named** is `yes` for the owner's comparison set. The `Named competitors:` line in
  `features.md` lists exactly the `yes` rows, so the subset is readable from the roster.
- **Profile**, **Matrix**: a path, or `none`. A row with one and not the other is a gap
  to close or to note.
- **Status** is `active` or `retired <YYYY-MM-DD>: <reason>`. Retire a tool; never
  delete its row.

## Keeping it current

Every competitor step begins with the **roster diff**: list the profile and matrix
files, compare them with the roster rows, and add a row for any tool the step met that
the roster lacks (a rival named in a complaint thread, an AI answer, a pricing page).
A new row may say `Profile: none` until someone profiles it.

The monthly pain-point refresh carries the diff, so the roster is reviewed at least
monthly without a clock of its own.

**Done when** every profile and matrix file has a roster row, and every tool the
current step met is on the roster.

## The coverage ledger

An exercise that chooses a subset of the active roster (a pricing rival set, a
pain-point register) records the rest in a `## Not covered` section of its own record
doc, one row per active roster tool left out:

| Tool | Profiled | Reason not covered | Decided | Revisit when |
| --- | --- | --- | --- | --- |
| Huly | 2026-09-30 | Self-hosted all-in-one; buyer overlap unproven | 2026-10-12 | A pain-point thread names Huly as a GitHub Projects alternative |

- **Profiled** is the profile date at the time of this pass, or `no`. The roster holds
  the current date; this cell records what the exercise had to go on.
- **Reason** says why this tool, not why the exercise is narrow. "Owner scoped the pass
  to four" is a reason; it applies row by row.
- **Revisit when** is a condition someone can observe, not "later".

Steps that only seed from the roster (AI-answer prompts, keyword seeds) take the active
rows and need no ledger.

**Done when** covered tools plus Not covered rows equal the active roster.
