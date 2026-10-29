---
name: coduo-discuss
description: |
  Capture an idea, exploration or side-quest into one durable file — 
  `docs/product/<idea>/discussion.md` in the repo that owns the idea, or
  `brain/discussions/<idea>/` in the owner's knowledge base (an OpenKnowledge project named in CLAUDE.md) when no repo does. Written live as
  the discussion happens, so the reasoning survives the thread and a later
  `coduo-epic` has something to read. Use when the user opens with an idea
  rather than a task — "let's think about", "what if we", "I've been wondering"
  — or asks to document a discussion. Reach for it unprompted once a
  conversation has run several exchanges of open-ended reasoning with no code
  touched: that is a discussion, and it is about to be lost. One idea, one
  file. Many linked topics with dependencies and a rendered map is `coduo-flow`;
  arguing back rather than recording is `grilling`.
disable-model-invocation: false
---

# Coduo discuss

A discussion is knowledge with no home. A ticket has a tracker, code has a
repo, a decision has an ADR — but the hour spent working out whether an idea is
real leaves nothing behind, and six months later the same argument runs again
from zero. This skill gives that hour a file.

**One idea, one folder, one file.**

```
docs/product/<idea-name>/discussion.md     the idea belongs to this repo
brain/discussions/<idea-name>/discussion.md  it belongs to no repo
docs/product/README.md                       the index, regenerated
```

The folder rather than a bare `<idea-name>.md` because ideas accrete —
a screenshot, a pasted competitor page, synced design markup — and a rename
later breaks every link already pasted into an issue.

The template is [`references/discussion-template.md`](references/discussion-template.md);
[`references/example.md`](references/example.md) is a filled-in one. Read the
template before writing the first file of a session — its section order is the
skill's actual output contract, and the example is what stops the file reading
like "Decisions made: we decided to proceed."

## Phase 0 — Open the file, in the first minute

The file exists before the discussion is any good. A session that dies at 2am
still leaves an artifact, and that is the whole point: end-of-session capture
is what already fails.

1. **Find the home.** The idea belongs to the current repo when the repo's
   subject *is* the idea's subject. It belongs to the knowledge base when the idea
   names a product or question this repo is not about — riffing on a new
   product while sitting in a tooling repo is the common case, and the knowledge base is the
   right answer there. Write to it with its MCP tools.
2. **Check for a near-match first.** `ls docs/product/` and search the knowledge base's
   `discussions/` for the same idea under a different slug. Two half
   discussions of one idea is worse than none.
3. **Name it.** Propose a kebab-case slug from the topic and say so, once:

   > 📝 Documenting this discussion as `docs/product/<idea-name>/discussion.md`. Let me know if you want to change it.

   No confirmation gate — asking permission mid-thought breaks the thought, and
   silence means the file is never found. If the idea's subject drifts from its
   slug later, offer the rename; the folder makes that a one-line change.
4. **Write the skeleton and the opening message.** Copy the template's
   headings, then put the user's first message — the one that opened the
   discussion — verbatim under **In your words**. It is the sharpest statement
   of the idea that will exist, it costs nothing, and paraphrase erodes it.

**Done when** the file exists on disk with the opening message in it.

## Phase 1 — Keep it live

Append to **Session log** as each sub-topic closes, in the user's terms, rough.
Raw notes in the right file beat polished notes in no file. Promotion into the
tidy sections is Phase 2's job; if Phase 2 never runs the material is still
there.

Two things to do while the discussion runs:

- **A decision recorded without a reason is worthless later.** When something
  gets settled and the *why* was never said, ask for it — "why not X?" — and
  record the answer beside the decision. A strong default also names what
  would reopen it: a metric, a date or an event. This is the capture doing its job, not
  a change of posture. Argue about the idea itself in `grilling`, which runs
  fine inside a discussion.
- **Keep more verbatim on request.** Anything the user flags — "keep this" —
  goes into **In your words** with its date. Everything else stays paraphrased;
  a full transcript at the bottom of the file is the original problem
  relocated, not solved.

## Phase 2 — Close the session

1. **Offer the adversarial take.** One prompt, at the end, before the tidy
   pass: a sub-agent whose brief is to attack the idea — the assumption nobody
   stated, the reason this fails, who has tried it. Run it under a strong model
   (`fable` or `opus`); a cheap adversary produces cheap objections. Its output
   lands in the file **unfiltered**, as its own dated section, with the user's
   reaction beneath it. A critique they rejected today is exactly what they
   will want to reread when the idea has changed shape.
2. **Promote.** Move what the session settled out of Session log into
   Decisions, Rejected, Open questions, Risks and Next steps. The Session log
   keeps the raw text; it is a log, not a draft.
3. **Rewrite "Where this stands."** One paragraph plus a status, always
   current. It is the first screen, and it is what a later `coduo-epic` reads.
4. **Next steps carry their tool.** A step a future session can act on names
   the skill that does it: `- [ ] GTM research on the pricing assumption — /coduo-wayfinder`.
   Half of them will be "ask Ankit" or "check whether Apple allows this", which
   is fine — free text carries the thought, the skill name makes it actionable
   a month later.
5. **Regenerate the index.** `docs/product/README.md` (or the knowledge base's equivalent):
   one line per idea — slug, status, the one-line hook, date of last session —
   read out of each file's header. Never hand-maintained; that goes stale by
   the third idea.
6. **Leave it uncommitted and say so.** Name the file path in the closing
   message so the user can stage it with whatever else they are doing.

**Done when** the file's first screen tells the truth about where the idea
stands, and every decision in it carries a reason.

## Status, and the three exits

`exploring` · `parked` · `dead` · `ready-for-epic` · `became-epic-#123`

`dead` is kept on purpose. An idea ruled out and deleted gets reinvented in six
months; an idea ruled out with its reason on file does not.

A discussion leaves in one of three directions:

- **Forward** — it is ready to build. `coduo-epic`, and the epic's issue link
  becomes the file's top line. The file stays appendable: people keep
  discussing an idea after it is filed, and leaving that conversation nowhere
  to go recreates the problem one level up.
- **Sideways** — it grew into several sub-topics with dependencies between
  them. That wants `coduo-flow`'s notes-and-map. Watch for it and offer once,
  then drop it: not noticing the moment a thing outgrew its container is the
  same failure this skill exists to fix, one scale up.
- **Parked** — status set, next steps written, index updated. Nothing else.
