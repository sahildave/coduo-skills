// macdrag: drive a real cross-app drag-and-drop on macOS with posted CGEvents.
//
// All points are global display points, origin at the top-left of the primary
// display (the one with the menu bar), y growing down. Secondary displays can
// have negative x or y. `macdrag displays` prints every display's bounds.
//
// usage:
//   macdrag check                      Accessibility + event-posting check
//   macdrag displays                   bounds of every display
//   macdrag window <App>               frontmost normal window of <App>
//   macdrag drag (--from-app <App> [--grip fx,fy] | --from x,y [--expect-app <App>])
//                --to x,y [--via x,y]... [--hold s] [--glide-ms ms]
//                [--shot path [--shot-region x,y,w,h]]
//
// Exit codes: 0 ok, 1 usage, 2 safety abort, 3 Accessibility missing, 4 another drag running.
import AppKit

func die(_ code: Int32, _ msg: String) -> Never {
    FileHandle.standardError.write((msg + "\n").data(using: .utf8)!)
    exit(code)
}

func point(_ s: String) -> CGPoint {
    let p = s.split(separator: ",").compactMap { Double($0.trimmingCharacters(in: .whitespaces)) }
    guard p.count == 2 else { die(1, "bad point '\(s)', expected x,y") }
    return CGPoint(x: p[0], y: p[1])
}

// MARK: windows and displays

typealias WindowInfo = [String: Any]

func onScreenWindows() -> [WindowInfo] {
    CGWindowListCopyWindowInfo([.optionOnScreenOnly, .excludeDesktopElements], kCGNullWindowID) as? [WindowInfo] ?? []
}

func bounds(_ w: WindowInfo) -> CGRect? {
    guard let d = w[kCGWindowBounds as String] as? NSDictionary else { return nil }
    return CGRect(dictionaryRepresentation: d)
}

func owner(_ w: WindowInfo) -> String { w[kCGWindowOwnerName as String] as? String ?? "?" }

// App-level windows: normal (0), floating (3), modal panels (8) and the like.
// Layer 20+ is the Dock, menu bar and system chrome.
func isAppWindow(_ w: WindowInfo) -> Bool {
    let layer = w[kCGWindowLayer as String] as? Int ?? 0
    return (0..<20).contains(layer)
        && ((w[kCGWindowAlpha as String] as? Double) ?? 1) > 0
        && (bounds(w).map { $0.width > 80 && $0.height > 80 } ?? false)
}

// The list is front-to-back, so the first match is the frontmost.
func frontWindow(of app: String) -> CGRect? {
    onScreenWindows().first { owner($0) == app && isAppWindow($0) }.flatMap(bounds)
}

// The topmost app-level window under `p`, or nil over bare desktop.
func topWindow(at p: CGPoint) -> WindowInfo? {
    onScreenWindows().first { isAppWindow($0) && (bounds($0)?.contains(p) ?? false) }
}

func displayBounds() -> [CGRect] {
    var ids = [CGDirectDisplayID](repeating: 0, count: 16)
    var n: UInt32 = 0
    CGGetActiveDisplayList(16, &ids, &n)
    return ids.prefix(Int(n)).map { CGDisplayBounds($0) }
}

func requireOnDisplay(_ p: CGPoint, _ what: String) {
    guard displayBounds().contains(where: { $0.contains(p) }) else {
        die(1, "\(what) \(Int(p.x)),\(Int(p.y)) is on no display. Run `macdrag displays` for valid bounds.")
    }
}

// MARK: events

func post(_ type: CGEventType, _ p: CGPoint) {
    CGEvent(mouseEventSource: nil, mouseType: type, mouseCursorPosition: p, mouseButton: .left)?
        .post(tap: .cghidEventTap)
}

func cursor() -> CGPoint { CGEvent(source: nil)?.location ?? .zero }

let accessibilityHelp = """
    Accessibility is not granted, so macOS drops the posted mouse events.
    Ask the human at the desk to open System Settings > Privacy & Security > Accessibility
    and switch on the app this command runs under (Terminal, iTerm, Ghostty, Claude, Code...),
    then quit and reopen that app and rerun `macdrag check`.
    """

func checkAccess() {
    guard AXIsProcessTrusted() else { die(3, accessibilityHelp) }
    // Trusted but still filtered (e.g. a sandboxed parent): prove a post moves the cursor.
    let before = cursor()
    let probe = CGPoint(x: hypot(before.x - 300, before.y - 300) > 150 ? 300 : 700, y: 300)
    post(.mouseMoved, probe); usleep(100_000)
    let moved = cursor()
    post(.mouseMoved, before); usleep(50_000)
    // Loose tolerance: a hand on the mouse nudges the reading by a few points.
    guard hypot(moved.x - probe.x, moved.y - probe.y) < 40 else {
        die(3, "Posted a mouse move to \(probe) but the cursor stayed at \(moved).\n" + accessibilityHelp)
    }
}

// One drag per machine: two drivers fighting over the cursor corrupt both runs.
func takeLock() -> Int32 {
    let dir = (ProcessInfo.processInfo.environment["MACDRAG_CACHE"]
        ?? NSHomeDirectory() + "/Library/Caches/coduo-mac-drag")
    try? FileManager.default.createDirectory(atPath: dir, withIntermediateDirectories: true)
    let fd = open(dir + "/drag.lock", O_CREAT | O_RDWR, 0o644)
    guard fd >= 0, flock(fd, LOCK_EX | LOCK_NB) == 0 else {
        die(4, "Another macdrag drag is running on this machine. Wait for it to finish.")
    }
    return fd
}

// MARK: commands

var args = Array(CommandLine.arguments.dropFirst())
guard let cmd = args.first else { die(1, "usage: macdrag check | displays | window <App> | drag ...") }
args.removeFirst()

switch cmd {
case "check":
    print("AXIsProcessTrusted:", AXIsProcessTrusted())
    checkAccess()
    print("ok: posted events move the cursor")
    exit(0)

case "displays":
    for (i, b) in displayBounds().enumerated() {
        print("display \(i): x=\(Int(b.minX)) y=\(Int(b.minY)) w=\(Int(b.width)) h=\(Int(b.height))\(i == 0 ? " (main)" : "")")
    }
    exit(0)

case "window":
    guard let app = args.first else { die(1, "usage: macdrag window <App>") }
    guard let b = frontWindow(of: app) else { die(1, "no on-screen window owned by '\(app)'") }
    print("window \(app): x=\(Int(b.minX)) y=\(Int(b.minY)) w=\(Int(b.width)) h=\(Int(b.height)) center=\(Int(b.midX)),\(Int(b.midY))")
    exit(0)

case "drag":
    break

default:
    die(1, "unknown command '\(cmd)'")
}

// MARK: drag options

var fromApp: String?, expectApp: String?, from: CGPoint?, to: CGPoint?
var grip = CGPoint(x: 0.5, y: 0.6)
var via: [CGPoint] = []
var hold = 1.0, glideMs = 650.0
var shot: String?, shotRegion: String?
var i = 0
func value() -> String {
    i += 1
    guard i < args.count else { die(1, "\(args[i - 1]) needs a value") }
    return args[i]
}
while i < args.count {
    switch args[i] {
    case "--from-app": fromApp = value()
    case "--grip": grip = point(value())
    case "--from": from = point(value())
    case "--expect-app": expectApp = value()
    case "--to": to = point(value())
    case "--via": via.append(point(value()))
    case "--hold": hold = Double(value()) ?? hold
    case "--glide-ms": glideMs = Double(value()) ?? glideMs
    case "--shot": shot = value()
    case "--shot-region": shotRegion = value()
    default: die(1, "unknown option \(args[i])")
    }
    i += 1
}
guard let target = to else { die(1, "drag needs --to x,y") }
guard (fromApp == nil) != (from == nil) else { die(1, "drag needs exactly one of --from-app <App> or --from x,y") }

let lock = takeLock()
checkAccess()

// Resolve the start point.
var start: CGPoint
if let app = fromApp {
    guard let b = frontWindow(of: app) else { die(1, "no on-screen window owned by '\(app)'") }
    start = CGPoint(x: b.minX + b.width * grip.x, y: b.minY + b.height * grip.y)
    expectApp = app
} else {
    start = from!
}
requireOnDisplay(start, "start")
requireOnDisplay(target, "target")
for v in via { requireOnDisplay(v, "via point") }

// Safety: never press on a window the caller did not mean to press on.
let top = topWindow(at: start)
let topOwner = top.map(owner) ?? "desktop"
if let want = expectApp, topOwner != want {
    die(2, "abort: topmost window at start \(Int(start.x)),\(Int(start.y)) belongs to \(topOwner), not \(want). Nothing was pressed.")
}
print("start \(Int(start.x)),\(Int(start.y)) on \(topOwner)")

let restore = cursor()
var pressed = false

// If killed mid-drag, release the button and give the cursor back.
func release(_ p: CGPoint) {
    if pressed { post(.leftMouseUp, p); pressed = false }
}
for sig in [SIGINT, SIGTERM, SIGHUP] {
    signal(sig) { _ in
        let p = CGEvent(source: nil)?.location ?? .zero
        CGEvent(mouseEventSource: nil, mouseType: .leftMouseUp, mouseCursorPosition: p, mouseButton: .left)?.post(tap: .cghidEventTap)
        _exit(130)
    }
}

// Hand-off guard: if the cursor is not where we last put it, a human is moving
// the real mouse. Release where it is, give the cursor back and stop.
// Checked before each post: right after a post the cursor always matches.
var lastPosted = CGPoint.zero
func drag(to p: CGPoint) {
    let at = cursor()
    if hypot(at.x - lastPosted.x, at.y - lastPosted.y) > 25 {
        release(at)
        post(.mouseMoved, restore)
        die(2, "abort: the real mouse moved during the drag (cursor at \(Int(at.x)),\(Int(at.y)), expected \(Int(lastPosted.x)),\(Int(lastPosted.y))). Button released; rerun when the desk is idle.")
    }
    post(.leftMouseDragged, p)
    lastPosted = p
}

func glide(_ a: CGPoint, _ b: CGPoint) {
    let steps = max(8, Int(glideMs / 16))
    for s in 1...steps {
        let t = Double(s) / Double(steps)
        drag(to: CGPoint(x: a.x + (b.x - a.x) * t, y: a.y + (b.y - a.y) * t))
        usleep(16_000)
    }
}

post(.mouseMoved, start); usleep(200_000)
post(.leftMouseDown, start); pressed = true; lastPosted = start; usleep(400_000)

// The wiggle: a few small dragged steps before travelling. Safari (WebKit) only
// starts an NSDraggingSession once it sees short movement after the press; a
// jump straight to the target reads as a click-and-release instead.
let dir: Double = start.y > 40 ? -1 : 1
for s in 1...12 {
    drag(to: CGPoint(x: start.x, y: start.y + dir * Double(s) * 2)); usleep(30_000)
}
usleep(300_000)

var last = CGPoint(x: start.x, y: start.y + dir * 24)
for p in via + [target] { glide(last, p); last = p }

// Hover: keep posting dragged events so the target sees a live session
// (draggingUpdated) for the whole hold, e.g. to reveal hover-only UI.
let ticks = max(1, Int(hold * 20))
for t in 0..<ticks {
    drag(to: target); usleep(50_000)
    if t == ticks / 2, let path = shot {
        let region = shotRegion ?? "\(Int(target.x) - 150),\(Int(target.y) - 80),300,160"
        let p = Process()
        p.executableURL = URL(fileURLWithPath: "/usr/sbin/screencapture")
        p.arguments = ["-x", "-R", region, path]
        try? p.run(); p.waitUntilExit()
        print(p.terminationStatus == 0 ? "shot \(path) region \(region)" : "shot failed (Screen Recording not granted?)")
    }
}

release(target)
print("released at \(Int(target.x)),\(Int(target.y))")
usleep(300_000)
post(.mouseMoved, restore)
flock(lock, LOCK_UN)
