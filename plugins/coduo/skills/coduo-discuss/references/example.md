# Worked example

A real-shaped `docs/product/calendar-nudge/discussion.md` after one session.
The point of this file is the *texture*: decisions that name their reason,
rejections that stay on the page, a status paragraph a stranger could act on.

Compare against the failure mode, which every generic capture produces:

> ## Decisions made
> - We decided to proceed with the calendar approach.
> - Pricing to be determined.

That records that a conversation happened. It does not record the conversation.

---

```markdown
# Calendar nudge

## Where this stands

**Status:** exploring
**Last session:** 2026-09-09

A menu-bar app that reads the next calendar event and nudges you into the
right app for it — the Zoom link, the doc, the ticket — 60 seconds before it
starts. Plausible enough to prototype, but the whole thing rests on EventKit
giving us the event body reliably across Google-synced calendars, which nobody
has checked. That check is the next move; everything else waits on it.

## The idea

A single menu-bar item that watches the next event and, a minute out, surfaces
one button: the thing you are about to need. Not a calendar client. Not
notifications. One button, then it disappears.

## Why

The 60 seconds before a meeting are spent hunting for the link — in the invite,
in Slack, in a doc someone pasted. The owner does this six times a day. Existing
calendar apps show you the event; none of them get you *into* it.

## Decisions made

- **Menu bar, not a window** — because the value is the 60-second window, and
  anything that needs to be opened first has already lost. It has to be
  present without being asked for.
- **EventKit rather than a Google Calendar API integration** — because it
  inherits whatever the user already has synced on the Mac, so there is no
  auth flow, no OAuth review, and it covers Exchange for free.
- **One action per event, never a list** — a list is a decision, and the whole
  premise is removing the decision.

## Rejected, and why

- **A full calendar UI** — rejected: the market is saturated and the thing we
  are actually good at is the last minute, not the week view. Revisit only if
  the nudge alone cannot carry a paid tier.
- **Notification-centre-only, no app surface** — rejected: macOS coalesces and
  delays notifications unpredictably, and a nudge that arrives at T+2min is
  worse than none.

## Open questions

- Does EventKit reliably expose the event *body* (where Zoom/Meet links live)
  for Google-synced calendars, or only the structured fields? **Blocks
  everything.**
- What happens with back-to-back meetings — does the nudge for the next one
  fire while you are still in the current one?
- Is this a $3 one-off or a subscription? No signal yet.

## Risks / unknowns

- Link extraction is regex against free text — it will break on the invite
  formats we have not seen. Would be told by: running it against a month of
  The owner's real calendar before building any UI.
- Sandboxing + calendar entitlement means a TCC prompt on first run, which is
  the highest-drop-off moment in the product and arrives before any value has
  been shown.

## Next steps

- [ ] Spike EventKit against a month of real Google-synced events, check body
      access — /prototype
- [ ] Look at what Vimcal and Amie do in the last minute before an event
- [ ] Ask Ankit whether his Exchange calendar exposes bodies the same way

## Adversarial take — 2026-09-09

> The premise is that finding the link is the pain, but the actual pain is
> context-switching *into* the meeting, and a button does not solve that. Every
> calendar app has shipped a "join" button for five years; Fantastical has had
> one since 2019. So the differentiator is not the button, it is the 60-second
> timing — and that is a notification-scheduling problem, not a product. The
> thing that would make this real is knowing *which* app, and that is exactly
> the part being handwaved as "regex against the body."

**Reaction:** Half right and worth keeping. The join-button point stands and
means we are not differentiated on meetings at all — but the interesting cases
were never Zoom links, they were "open this Linear ticket" and "open this doc",
which no calendar app does. That reframes the idea: it is a *link router*,
and meetings are one case. Did not accept "not a product" — the timing is
genuinely the mechanism.

## Session log

### 2026-09-09

- Started from the six-times-a-day link hunt.
- Went round on calendar UI vs menu bar; menu bar won on the 60-second framing.
- EventKit vs Google API — EventKit wins on no-auth, but nobody knows if the
  body is exposed. Flagged as the blocking unknown.
- Adversarial pass reframed it from "meeting joiner" to "link router". Kept.

## In your words

> **2026-09-09** — what if there was just a thing in the menu bar that knew
> what meeting was next and put the zoom link right there, i keep losing 30
> seconds digging through the invite and i do it like 6 times a day
```
