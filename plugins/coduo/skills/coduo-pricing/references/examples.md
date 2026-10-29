# Worked examples

Two deep pricing runs, both decided. Read them before a fresh run: the method below was
copied from Harbour to Atlas, and each run left a gap the next one should close.

## Harbour (decided 2026-10-06, ADR 0015)

Repo `harbour`, epic harbour#398.

| Artefact | Path |
| --- | --- |
| Profiles (33 tools) | `docs/research/<slug>.md`, flat, mixed with non-competitor notes |
| Matrix | `docs/research/competitor-matrix/<slug>.json` |
| Prototype | `docs/prototypes/pricing/` (`build-competitors.mjs` → `competitors.js`, `revenue.js`, `personas.js`, `pricing-models.js`, `lavish/report.html`) |
| Decision | `docs/product/pricing/discussion.md`, `docs/adr/0015-final-plan-prices.md` |

Produced: five pricing models debated down to the Board ladder; Pro $16, Ultimate $49, +$6
per extra private Board.

Lessons:

- **The rival set's reason lived in a code comment.** `revenue.js` `MAJOR` names six rivals
  and says why, but undated and with no revisit trigger. The 27 others have no row anywhere.
- **Profiles and matrix drifted.** `feedvote.json` has no profile; `github.md` has no JSON.
  A roster with Profile and Matrix columns shows this at a glance.
- **Price rivals at the buyer's real setup.** Pricing every rival as one board showed an
  agency $29 at Featurebase instead of $99 for 12 boards (`discussion.md`, "Rival prices
  count boards").

## Atlas (decided 2026-09-30, ADR 0027)

Repo `atlas-workspace`. Method copied from Harbour (`plan.md`).

| Artefact | Path |
| --- | --- |
| Research brief and JSON schema | `docs/research/competitor-matrix/BRIEF.md` |
| Profiles (19 tools, 5 groups) | `docs/research/competitors/<slug>.md` |
| Matrix | `docs/research/competitor-matrix/<slug>.json` |
| Method | `docs/product/pricing/plan.md` |
| Prototype | `docs/prototypes/pricing/` (same kit; `pricing-models.js` `RIVALS`) |
| Decision | `docs/product/pricing/decision.md`, ADR 0027 |

Produced: Free web, Pro $4.99 per person, Team $9.49 for 2 Seats then $4.49 a Seat.

Lessons:

- **The brief made the matrix comparable.** One schema with `soloPrice` and `teamOf5Price`
  let the calculator price every rival at the buyer's setup. Reuse it.
- **Dropped models were logged; dropped rivals were not.** `plan.md` gives a reason for each
  dropped model. The calculator prices 6 of 19 tools and `decision.md` says only "The owner
  named" them. The later pain-point pass then covered 6 tools and never mentioned Huly. A
  Not covered table in `plan.md` would have carried the reasons forward.
- **Name a price anchor as one.** Tower is in `RIVALS` as the price of a paid Mac developer
  tool, not as a rival. Say so in the roster's Group column.
