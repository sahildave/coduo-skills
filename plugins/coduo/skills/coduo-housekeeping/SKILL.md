---
name: coduo-housekeeping
description: |
  Make a project's tracker and repo tell the truth again. Finds shipped-but-open
  tickets and closes them against code evidence, files work that exists only in a
  handoff doc or a commit, assigns release and priority to what is left, and
  routes each ticket to an unattended agent or a human. Works on any tracker by
  reading the project's own conventions first. Use for "clean up the issues",
  "what's next for this repo", "why is the backlog so big", "triage the
  backlog", before planning a release, or before an agent run so no lane burns
  on work already done. Runs before `coduo-epic`.
disable-model-invocation: false
---

# Coduo housekeeping

A backlog **drifts**: the code moves, the tracker does not. Every artifact that
describes the work — a status table, a manifest, a run report, a prior audit —
drifts in the same direction, toward claiming done. Only the code on the
integration branch is current.

Housekeeping is closing that gap, in six phases plus a binding step. The output
of each is the input of the next, so run them in order. Every phase that changes
the tracker stops at an approval gate.

You are working with the human, not reporting to them. Present findings grouped
with their evidence, then act on what they approve.

---

## Phase 0 — Bind

This skill carries no tracker, no vocabulary and no commands of its own. Bind
them from the project before anything else, and use these bindings wherever a
later phase names one.

Establish five things:

- **Tracker.** The project's adapter doc names it and gives the real commands —
  look for a file describing the issue tracker under the repo's agent docs. With
  no adapter doc, infer from the environment: a hosted-git clone with its CLI
  installed and authenticated, a tracker CLI on `PATH`, an MCP server for one, or
  ticket files in the tree. Confirm the inference with the human before writing.
- **Vocabulary.** The label or state strings this project actually uses. A triage
  vocabulary doc is the source of truth if one exists; otherwise read the live
  label list. Where the two disagree, that gap is a Phase 6 finding, not
  something to fix now.
- **Release grouping.** Milestone, cycle, fix version, project — or none. When
  the tracker has no such concept, Phase 4 assigns priority only.
- **Integration branch.** What shipped code merges into. It is often not the
  default branch: check where recent merge commits land.
- **Gates.** The project's own verification commands, read from where it declares
  them — package scripts, task runner, CI config, or an agent-runner config.
  Never assume a language or a command name.

State the five bindings in one short block before proceeding. A wrong binding
makes every later phase confidently wrong.

**Done when** all five are named, and any you inferred rather than read have been
confirmed by the human.

---

## Evidence

The rules that make a close trustworthy. They bind every phase; read them once
and apply them throughout.

**Verify against the code on the integration branch.** Read the file, run the
search, check the commit. A `passed` status, a progress table, a manifest entry,
a run report and a prior audit doc all describe a moment that has passed. Treat
each as a lead to check, and expect it to be stale in the "more got done since"
direction as often as the reverse.

**Read the acceptance criteria, not just the artifacts.** A file existing proves
code was written. It does not prove the ticket is done. Criteria that demand live
sandbox proof, a published dashboard, legal sign-off, or a manual pass stay open
no matter how complete the implementation looks. A ticket that cites a design
board closes on a screenshot of the built screen beside that board — a grep
proves a token is referenced, not seen, and quillnote ran 55 such tasks green
on greps before a human opened the app to a settings footer no board has. This
single check is what
separates a defensible close from a plausible one.

**Match ticket identifiers exactly.** A substring search for `#295` hits a commit
about #2951 and a commit that merely mentions #295 in passing. Search for the
implementing artifact — the file, the function, the migration, the test name —
and confirm a merge commit by reading it.

**An empty body is a signal about the reporter, not the ticket.** Title-only
tickets are often dogfooding: someone using the product filed them from inside
it. Ask who made them and why before proposing any of them for closing.

**Every close carries its evidence** in the closing comment: a `file:line`, a
commit id, or the acceptance criterion now met. A close without evidence is just
a smaller backlog, and the next person re-derives it from scratch.

---

## Phase 1 — Survey

Establish the size of the drift before touching anything.

Count open tickets. Break them down by release grouping, by priority, and by
whether they carry any classification at all. List the release groupings with
their open and closed counts.

Report the distribution to the human in a few lines. Two numbers usually tell the
story on their own: how many tickets have no release grouping, and how many have
nothing on them at all.

**Done when** you can state the open count, the per-release split, and the size of
the unclassified bucket.

## Phase 2 — Reconcile

Find every open ticket that is already resolved, and close it against evidence.

Work in **waves**. A wave is a cluster filed together — one epic's children, one
audit's findings, one rollout's fix list. Clusters drift together because they
shipped together, so finding one stale ticket means checking its siblings. Expect
a second wave after the first: clearing the loudest cluster reveals the next one
underneath.

For each candidate, establish which category it falls in:

- **Shipped** — implementation is on the integration branch and its acceptance
  criteria are met.
- **Superseded** — the intent changed. The thing it asked to remove now holds a
  feature that shipped; the decision it asked for went the other way.
- **Decided and recorded** — a decision ticket whose decision is now written
  somewhere durable. Cite where.
- **Cannot reproduce** — an attempt to reproduce it failed. Name the failed
  attempts, especially any committed as passing tests, and mark it so a
  recurrence reopens it rather than filing a duplicate.
- **Not planned** — test tickets, placeholders, duplicates.

Present the candidates to the human **grouped by category, with a one-line reason
each**, and render every ticket as a link with its full URL so they can open it.
State plainly which tickets you checked and left open, and why — that list is what
proves the pass was thorough rather than eager.

On approval, write the closes as a script rather than firing them one by one. A
script is reviewable before it runs, re-runnable if it half-fails, and gives each
category a shared closing comment. Check the tracker's re-run behaviour first:
closing an already-closed ticket is harmless on some, an error on others.

**Done when** every open ticket has been checked against the code and is either
closed with evidence or explicitly kept, with a reason.

## Phase 3 — Surface

Find the work that exists but has no ticket, and file it.

A backlog that only ever shrinks is getting less true, not healthier. Look in the
places work hides: handoff and audit documents, `TODO` and `FIXME` comments,
commit messages describing a known-broken thing, and any test committed as a
recorded negative result.

The strongest signal is a document whose first section says START HERE. That is
unfinished work with a reader and no tracker entry.

Hunt **stubs** on purpose, because they are the most expensive thing here. A
stub is code that claims behaviour it doesn't perform: a function that only
logs, a handler that returns early, a dialog with nothing behind it, a
`return null` under a ticket reference. Other tickets are built on the
assumption that it works, and the user has been bitten by this several
times.

Not everything found earns a ticket; `coduo-implement` rule 5 is the test. A
stub always gets one. So does real product work: user-facing behaviour, a
real bug, or a launch blocker. Group several small findings in one area into
a single ticket. Hardening, refactors and nice-to-haves are not filed; list
them in the report as dropped, one line each, so the user can overrule you.

File each one with the evidence already gathered — the ruled-out hypotheses
belong in the ticket body, so the next person does not re-run them. Then link the
source document to the new ticket in both directions, so the two cannot drift
apart.

**Done when** every stub and every real product gap you found has a ticket
that its source document points at, and everything else is on the report's
dropped list.

## Phase 4 — Triage

Give release grouping and priority to everything that lacks one.

Propose the whole set as one table before changing anything: ticket, current
state, proposed grouping, proposed priority, and a short why. One table the human
scans in a minute beats a stream of questions.

Anchor priority to the release's own gate, using the project's scale. Where the
scale is a launch gate: top priority blocks the release, middle is correctness
that can follow it, low is polish. Say what the gate is when you present the
table, so the human is checking your reasoning rather than your taste.

An open ticket that is hardening, a refactor, an enhancement with no
user-facing effect, or a rare edge case a normal user will not hit gets **propose close: over-engineering** in the same
table, with the one-line why. Before launch, the only work that counts is
launch blockers and real bugs. The user has had to close these by hand in
batches.

Where the body genuinely does not support a call, propose the project's
triage-needed state instead of guessing. A guessed priority reads exactly like a
considered one, and that is what makes the whole scheme untrustworthy.

**Done when** every ticket with a usable body has a grouping and a priority, and
every ticket without one is marked for triage rather than assigned a guess.

## Phase 5 — Route

Split what remains into who can do it.

- **Agent-ready** — fully specified, and every input lives in the repo.
- **Human-gated** — needs something outside the repo: console or DNS access,
  credentials for a live third-party sandbox, a published dashboard, legal
  sign-off, a physical device, or a decision nobody has made.
- **Needs triage** — the body cannot carry either call yet.

Route on the *inputs*, not the difficulty. A hard refactor with everything in the
repo is agent-ready; a five-minute change that needs someone to click through a
vendor console is gated.

Then check what is already on each ticket and remove anything that now
contradicts. A stale agent-ready mark on gated work is the expensive one: an
unattended run picks it up and burns a lane discovering it cannot finish. When you
flip a call a human made, say so explicitly and name the tickets, so the judgement
is visible and reversible.

**Done when** every open ticket carries exactly one routing state, none carries
two that contradict, and every flip of a human's earlier call has been named to
them.

### The routed board

Phase 5 produces the artifact the whole pass exists to hand over. Render it as
**four tables**, in this order, every ticket a link with its full URL:

1. **Agent-ready** — columns: ticket, priority, task. Sorted by priority, then
   number. Where the project has release groupings, put the next release's rows
   in the table and list any later-release rows on one line beneath it.
2. **Human-gated** — columns: ticket, priority, task, **what blocks it**. That
   last column is the point of the table: it turns a queue into a list of asks,
   and a row whose blocker you cannot name is not really gated, it is unexamined.
3. **Needs triage** — columns: ticket, task, **the question that unblocks it**.
   One question per row, answerable in a sentence. A bare list of ticket numbers
   here hands the human back the same ambiguity that put them in this table.
4. **Reporter-owned** — the title-only tickets from the Evidence rule, as a plain
   list of links under a one-line note saying whose they are. They are in the
   board so the count reconciles, not because anyone should act on them.

Every open ticket appears in exactly one of the four. State the total and confirm
it matches the open count from Phase 1 — a board that does not reconcile is
hiding a ticket that fell between two states.

## Phase 6 — Harden

Close the gap that let the drift happen, so the next pass is smaller.

Three checks:

- **Vocabulary.** Every state the project's own docs describe exists in the
  tracker. Create the missing ones.
- **Contradictions.** No ticket carries two marks that cannot both be true.
- **Stale guides.** Any document that steered you wrong this pass gets fixed or
  deleted. A superseded audit doc left in place will mislead the next reader
  exactly as it misled you.

**Done when** the documented vocabulary and the live states match, and no document
you found stale is still in the tree saying the same wrong thing.

---

## Repo drift

The same rot reaches the files. Run this when the human asks to clean up docs, or
when Phase 6 turns up documents that lie.

Look for: directories a migration was supposed to remove and half did; docs with
zero inbound references; several handoff or audit docs covering one event, where
the newest supersedes the rest; numbered series such as ADRs or migrations where
one number holds two different entries; and links pointing at files that have
moved or gone.

Two rules keep this safe:

**A directory that looks like cruft may be load-bearing.** Check what reads it
before deleting — a runner, a hook, a script, an ignore-file comment explaining
why it stays tracked. Read the comment that defends it, and if you remove the
thing, carry the warning forward in its place.

**Fix the references in the same pass.** Deleting a file and leaving eleven
documents pointing at it trades one kind of drift for another. Sweep every
remaining doc for links the deletion broke, and expect to find pre-existing breaks
alongside them.

Finish on the gates bound in Phase 0, so a docs pass cannot quietly break a build.

---

## Reporting

The routed board from Phase 5 is the deliverable. Everything here wraps it.

Lead with the number that moved: the open count before and after. Then the
findings that change what the human does next — the top-priority ticket that
turned out to be unreproducible, the one you nearly closed and did not, the mark
that would have burned a lane. Close with the board.

Under the board, name the first move: the smallest set of agent-ready tickets that
could run together, and any file overlap between them that wants a dependency edge
or a shared lane. That is the handover into `coduo-epic`.

State what you could not verify. A housekeeping pass that reports total success is
the same artifact as the status table you just spent six phases distrusting.
