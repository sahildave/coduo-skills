---
name: coduo-mac-drag
description: Drive a real cross-app drag-and-drop on macOS with the real mouse, e.g. pick up a link in Safari and drop it on another app's window. Use to verify a Mac app's drop target, notch or drop-zone UI, or any drag between two apps. In-app drags belong to XCUITest or snapshot tests instead.
---

# coduo-mac-drag

`macdrag` posts real mouse events (CGEvent) so macOS starts a genuine `NSDraggingSession` in the source app and delivers it to the target app, exactly as a human drag would. The proof of a drop is the target app's unified log, not the driver's exit code.

## Before you drag

- **The drag takes over the real mouse** for 2 to 4 seconds. If a human is at the desk, tell them before each run to take their hand off the mouse. `macdrag` aborts and releases the button if the cursor moves under it, which is what a human nudge looks like.
- **Human desk only, one drag per machine.** Run it in an interactive session, or on a Mac dedicated to the run. An AFK lane on a shared Mac would move the owner's cursor mid-work. `macdrag` holds a lock, so a second drag on the same machine exits 4.
- **Coordinates** are global display points, origin at the top-left of the main display (the one with the menu bar), y down. A secondary display can sit at negative x or y. `macdrag displays` prints every display's bounds; `macdrag window <App>` prints a window's bounds and center in the same space.

## Build and check

```bash
B=$(~/.agents/skills/coduo-mac-drag/scripts/build.sh)   # compiles into ~/Library/Caches/coduo-mac-drag/bin
"$B/macdrag" check
```

`check` passes when posted events move the cursor. Exit 3 means Accessibility is missing: ask the human to open **System Settings > Privacy & Security > Accessibility**, switch on the app the agent's shell runs under (Terminal, iTerm, Ghostty, Claude, Code), then quit and reopen it. `--shot` also needs **Screen & System Audio Recording** for that app.

## The recipe

1. **Open the source.** For a link, use the bundled page, which is one big link, in a fresh Safari window at known bounds:
   ```bash
   osascript -e 'tell application "Safari"
     make new document with properties {URL:"file://'"$HOME"'/.agents/skills/coduo-mac-drag/assets/link.html"}
     delay 1.5
     set bounds of front window to {700, 150, 1300, 650}
     activate
   end tell'
   ```
   If Safari was not running, start it first with `open -a Safari` and wait 3 s; `make new document` fails with -600 on a stopped Safari.
2. **Launch the app under test** (the Debug build) and find the drop point: `macdrag window <App>` for a window center, `macdrag displays` for a notch (top-center of the built-in display).
3. **Note the time, then drag:**
   ```bash
   T=$(date '+%Y-%m-%d %H:%M:%S')
   "$B/macdrag" drag --from-app Safari --to 380,320 --hold 1.2 --shot /tmp/hover.png
   ```
4. **Read the unified log as the evidence.** The app must log its drag callbacks with `os.Logger`:
   ```bash
   /usr/bin/log show --start "$T" --predicate 'subsystem == "<app subsystem>"' --style compact --info
   ```
   A drop passes when `performDragOperation` (or the app's store step) appears with the dropped URL. `draggingEntered` alone means the hover worked and the drop did not.
5. **Screenshot** the end state with `screencapture -x -R x,y,w,h out.png` when the UI matters; the `--shot` frame shows the hover state mid-drag.
6. **Clean up:** quit the app under test, close the Safari window you opened (`tell application "Safari" to close front window`), quit Safari if it was not running before.

To check the driver itself, `"$B/droptarget" 200 200` opens a window that logs every drop under subsystem `co.coduo.mac-drag.droptarget` and prints its center.

## `macdrag drag` options

| Option | Meaning |
|---|---|
| `--from-app <App>` | Start on the app's frontmost window (owner name as in `macdrag window`). Safety check: that window must be topmost there. |
| `--grip fx,fy` | Where in that window to press, as fractions. Default `0.5,0.6`. |
| `--from x,y` | Start at explicit coordinates instead. Add `--expect-app <App>` to keep the safety check. |
| `--to x,y` | Drop point. Required. |
| `--via x,y` | Waypoint, repeatable. Use it to approach a target from a side, e.g. a notch from below: `--via 703,300 --via 683,140 --to 663,38`. |
| `--hold s` | Seconds to hover at the target before release (default 1). Hover-revealed UI needs at least its reveal delay. |
| `--glide-ms ms` | Duration of each leg (default 650). |
| `--shot path` | `screencapture` halfway through the hold. `--shot-region x,y,w,h` overrides the default 300x160 box around the target. |

Exit codes: 0 released, 1 usage or no window, 2 safety abort (wrong window on top at the start, or the real mouse moved), 3 Accessibility, 4 another drag is running.

## What the prototype found

- **The wiggle.** Safari (WebKit) only starts a drag session after a press followed by small movement. `macdrag` holds 400 ms, then posts 12 two-point dragged steps before travelling. A jump straight from the press to the target reads as a click: Safari follows the link and the page under the next attempt is no longer the link page. After any failed drag, reload the source page before retrying.
- **Mouse-up vs `performDragOperation` is a race.** The target's `performDragOperation` sometimes logs before the driver's `released at`, sometimes after. Tests and log checks must accept both orders; match on the log lines, never on their order relative to the release.
- **Floating windows count.** The safety check looks at every app-level window (normal, floating, panels), so an always-on-top overlay over the start point aborts the drag. Move it, or pick a `--grip` clear of it.
- **A hand on the mouse aborts the run.** On 6 Oct 2026 two verification drags exited 2 because the owner was using the mouse on the other display. That is the guard working; wait for an idle desk and rerun.

## Why not an existing tool

Measured on 6 Oct 2026, Safari link onto the bundled drop target: `cliclick` 5.1 dropped 2 of 11 (`dd:`/`dm:`/`du:`, with or without a scripted wiggle). Peekaboo 4.5 `drag` dropped 7 of 7, but it is a 75 MB install needing macOS 15, and has no hold before release, mid-hover screenshot, waypoints or start-window safety check. `agent-device` keeps gestures inside the session app's window, and XCUITest's `press(forDuration:thenDragTo:)` needs a UI-test target in the app under test. If Peekaboo is already installed, `peekaboo drag --from x,y --to x,y --duration 1500 --foreground` works for a plain straight drag.
