# Scenario presets

The machinery does not care what the notes are about. What changes per scenario
is the **kind vocabulary**, what an **edge** means, and what the **spine**
traces. Copy the closest block into `flow.json` and adjust.

Reach for the preset that matches the question being asked, not the artefact
being produced — two people can both want "a roadmap" and need different maps.

## First: a kind is a **noun**, never a lifecycle state

This is the mistake every vocabulary makes, and it is invisible until something
contradicts itself on screen. Four fields, four different questions:

| Field | Answers | Example values |
|---|---|---|
| `kind` | **What is this note about?** A noun. | screen, decision, epic, concept |
| `status` | How settled is the thinking? | open, proposed, validated, decided |
| `epics` | Which tracker epics have landed on this card? | `[68, 91]` — the map reads their state |
| `executor` | Who has to be present? | unattended, human, mixed |

**The test: can the same note keep this value for its whole life?** A note about
the Settings screen is a `screen` before it exists, while it is being built, and
after it ships. That is a kind. "Not built" and "Shipped" are true only for a
stretch — they are the *same note* at two moments — so they are lifecycle, and
lifecycle belongs on the other three axes, which the card already renders: a
tick when the epic closed, a dim under **Dim what is built**, a hatched Gantt
bar when no epic exists.

Put lifecycle in `kind` and you get a card that contradicts itself. A note
marked `gap` / "Not built" whose epic has closed is drawn red for *not built*
and dimmed as *built*, at the same time, and a reader has no way to tell which
is current. `check_flow.py` warns on exactly this, and the remedy is always to
move the lifecycle out of the kind rather than to add a second lifecycle kind
beside it — "Shipped" as a kind is the same error wearing the opposite label.

The pull is strongest on a map whose *point* is what has not been built yet,
because a red "missing" card is the thing you want seen from across the room.
Get it from the data instead: an empty `epics` list is what makes a Gantt bar hatch, and it
is the same fact.

## Lanes are depth slots, not narrative acts

`build_flow.py` lays cards out strictly by **dependency depth**: lane 1 holds
every note with no `depends_on`, lane 2 holds everything depending only on lane
1, and so on. A lane name therefore has to describe *what being that far down
the chain means*, because you cannot put a card in a lane by choosing to.

Count before you name. An honest evidence → implication → constraint → open
question → decision → action chain is six layers, so four lane names leave the
last two blank and the checker warns. When a name and a depth disagree, the
depth wins — so either rename the lane or add the intermediate note that makes
the depth real.

## Soft constraints are not edges

"Ops would prefer S3 before the billing split" is a preference, not a
dependency. Drawing it as an edge makes it look date-moving, and a reader
planning around it loses parallelism that was never actually blocked.

Put a soft constraint in the note body and, if it deserves to be visible, in
`facts`. Reserve edges for "this could not happen without that." The cost of
being loose here is a critical path that is wrong in the direction that makes
you slower.

## Idea validation / strategy

An edge means *this conclusion rests on that evidence*. The spine is the
argument's critical path.

```json
"kinds": {
  "finding":   {"tone": "plain",  "label": "Finding"},
  "decision":  {"tone": "warn",   "label": "Decision"},
  "blocker":   {"tone": "danger", "label": "Blocked"},
  "action":    {"tone": "ok",     "label": "Action"},
  "reference": {"tone": "none",   "label": "Reference"}
},
"lanes": ["EVIDENCE", "WHAT IT MEANS", "CONSTRAINTS",
          "OPEN QUESTIONS", "DECISIONS", "EXECUTE"]
```

Keep `finding` and `decision` apart even when it feels pedantic. A reader needs
to know which claims are load-bearing evidence and which are choices someone
made — that is the difference between arguing with the data and arguing with
the judgement.

## User-flow mapping

An edge means *this screen leads to that one*. The spine is the happy path.
Because layout follows depth, a lane name here doubles as a stage of the
journey only when the graph really is that linear — check the depth before
committing to the names.

```json
"kinds": {
  "screen":   {"tone": "plain",  "label": "Screen"},
  "sheet":    {"tone": "sheet",  "label": "Sheet"},
  "state":    {"tone": "muted",  "label": "State"},
  "decision": {"tone": "warn",   "label": "Decision"},
  "recovery": {"tone": "danger", "label": "Recovery"},
  "terminal": {"tone": "ok",     "label": "Terminal"}
},
"lanes": ["ONBOARDING", "THE APP", "THE TASK", "THE RESULT"],
"spineLabel": "Happy path"
```

Every `decision` node needs its branches to actually leave it. A flow whose
only drawn path is the happy one is the flow you already knew.

Real flows loop — a free tier that offers an upgrade, a retry after a failure.
Use `loops_to: [id]` for a return path: it is drawn as a dashed back edge and
kept out of the layering, so it neither trips the cycle check nor forces you to
leave a real path undrawn. A `recovery` with no way out is a dead end, and
leaving it a childless leaf is how the map says so.

## Multi-epic planning

An edge means *that has to land before this can start*. The spine is the
critical path in the project-management sense, and it is the whole point —
it is what tells you which slip moves the date.

```json
"kinds": {
  "epic":      {"tone": "plain",  "label": "Epic"},
  "milestone": {"tone": "warn",   "label": "Milestone"},
  "risk":      {"tone": "danger", "label": "Risk"},
  "gate":      {"tone": "ok",     "label": "Gate"},
  "reference": {"tone": "none",   "label": "Reference"}
},
"nodeWord": "epics",
"categories": {"code": "Code", "product": "Design & product"},
"doneStatuses": ["validated"],
"issueUrl": "https://github.com/you/repo/issues/",
"lanes": ["START NOW", "AFTER THE FOUNDATIONS", "MID-QUARTER",
          "LATE", "CLOSE"],
"spineLabel": "Critical path"
```

Name these lanes for *when work can start*, since that is what dependency depth
means in a plan. Resist journey-style names here — depth is a schedule fact.

**There is deliberately no "Shipped" kind here**, though earlier versions of this
preset had one. An epic that ships is still an epic; shipping is `status:
validated` and a closed epic in its `epics` list, and the card renders both — a green tick, a
green Gantt bar, and dimming under the built switch. A `done` kind beside
`epic` splits one thing across two colours and guarantees that half the map is
mislabelled the day nobody updates it.

Use `facts` for the numbers a planning reader wants without opening anything:
size, target, the ticket count. Use `status` for where each epic actually is,
and **`executor` for who can do it** — `unattended`, `human` or `mixed`.

For a solo developer running agents, executor is a more useful sort key than
dependency depth, because dependency tells you what is *possible* and executor
tells you what can *start tonight*. Sorting by dependency alone front-loads
whatever needs credentials and leaves every agent idle behind it. Before you
mark an epic `human`, look for its unattended half: a seam, a mock, a stubbed
interface. Most human-gated epics have one, and building it first both fills the
agent window and shortens the human sitting when it comes.

This is the scenario the **Gantt** exists for. Add a `timeline` to `flow.json`
and give each epic a `start` and `length`, and the map's "what blocks what"
gains a "when" underneath it:

```json
"timeline": {
  "units": 13, "unitLabel": "week", "rowLabel": "Workstream",
  "title": "When each piece runs",
  "bands": [{"from": 5, "to": 9, "label": "February - billing owner away"}]
}
```

Shade the stretch where people are away. A plan usually breaks on a calendar
collision rather than on an estimate, and the band is what makes that visible.

## Wayfinder / orientation

For someone new to a system, a codebase, or a domain. An edge means *understand
that before this makes sense*, so the graph doubles as a reading order.

```json
"kinds": {
  "concept":  {"tone": "plain",  "label": "Concept"},
  "gotcha":   {"tone": "danger", "label": "Gotcha"},
  "decision": {"tone": "warn",   "label": "Decision of record"},
  "howto":    {"tone": "ok",     "label": "How to"},
  "glossary": {"tone": "none",   "label": "Glossary"}
},
"lanes": ["START HERE", "THE MODEL", "THE MOVING PARTS", "DOING THE WORK"],
"spineLabel": "Read this first"
```

The spine is the shortest honest path from nothing to productive. A `gotcha`
earns a card when it cost someone real time — that is the knowledge that never
survives in a codebase otherwise.

## Rolling your own

Pick four to six kinds. Fewer and the map says nothing; more and the legend
stops being readable and the colours stop meaning anything. Reserve `danger`
for the thing you want a reader to see from across the room.

Then read the list back and apply the noun test above to every entry. If a kind
would stop being true once the work lands — `todo`, `gap`, `missing`, `done`,
`shipped`, `wip` — it is a status, and it will eventually be drawn contradicting
the tick beside it.

Two kinds must never share a `tone`. The legend is a colour key; two swatches of
one colour with different labels stops it keying anything, and it reads as a
rendering fault rather than as a decision.

**If your notes carry `epics:`, leave `danger` out of the vocabulary entirely.**
The map spends red on the state it derives — scheduled work with no epic gets a
dashed red outline over its kind's fill, matching the hatched Gantt bar — and a
red *kind* beside it puts two unrelated claims in one colour. The user-flow
preset's `recovery` is the case to watch: on a map that also tracks epics, move
it to `sheet` or `state`.
