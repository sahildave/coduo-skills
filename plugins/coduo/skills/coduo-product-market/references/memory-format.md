# Product memory format

The format contract for `docs/product/product-market.md` and
`docs/product/business-rules.md`. Any skill that writes either file uses it.

## product-market.md

Living memory for language and product-market insight. It does not claim
product-market fit. Create it when the first signal appears:

```markdown
# Product market

Memorable product-market signals. Status distinguishes what was noticed, proposed, supported, decided, or rejected.

## PM-001

- Kind: Product promise
- Status: hypothesis
- Statement: We never store user data. It all sits in your GitHub.
- Why it matters: A concrete trust promise and possible landing-page line.
- Source: <ticket, research artifact, or conversation date>
- Evidence: <links or "None yet">
- Landing-page use: Trust section
- Tension: <counterevidence, tradeoff, or "None recorded">
```

- **Kind**: reuse a kind already in the file first. Common kinds: Product promise,
  Audience, Job, Trigger, Advantage, Disadvantage, Differentiator, Objection,
  Substitute, Pricing wedge, Product boundary, Distribution mechanic, Tone, and
  Note for a converted field no other Kind fits.
  The audit reads four of them:
  - **Product promise**: a headline the owner makes to buyers. A `decided` one that
    tests as parity with the baseline becomes a Positioning flag in `features.md`.
  - **Differentiator**: what this product does that a named alternative does not.
    Name the alternative in the Statement; a rival is not the baseline.
  - **Advantage**: something the product does better, not something only it does.
  - **Substitute**: what a buyer uses instead. Say whether it is their default (the
    audit's Baseline alternative) or a paid rival (its Named competitors line).
- **Status** is one of `observation`, `hypothesis`, `supported`, `decided`,
  `rejected`. Agent-proposed language starts as `hypothesis`; only the owner or a
  recorded decision moves it to `decided`. Only `supported` and `decided` entries
  break a tie in the audit's tiering.

Use the next stable `PM-NNN` ID for a new meaning. Update the existing entry when
later evidence changes its status or wording. Keep rejected entries and explain what
rejected them so an old idea does not return without new evidence.

## business-rules.md

Constraints that govern product or business behaviour. Create it when the first rule
appears:

```markdown
# Business rules

Rules discovered or decided for this product. Proposed rules remain open to challenge; decided rules constrain later specs and implementation.

## BR-001

- Area: Data custody
- Status: proposed
- Rule: User content remains in GitHub; the product stores no copy.
- Applies when: The product reads or writes repository content.
- Rationale: <trust, product, legal, operational, or market reason>
- Implications: <what design, copy, pricing, or implementation must honor>
- Source: <ticket, product signal, research artifact, or conversation date>
```

Use the next stable `BR-NNN` ID for a new rule. Change `proposed` to `decided` only
when the user or a canonical decision settles it. Mark replaced rules `superseded` and
link the replacement.

## Shared rules

- IDs are never reused or renumbered. A gap from a deleted entry stays a gap.
- Cross-reference by ID (`see BR-013`), so a reword never breaks a link.
- A PM entry the audit relies on is cited in `features.md` by ID, in "Beats the
  baseline because" or in a Positioning flag.
