// Throwaway drop target for checking macdrag end to end.
// Opens a window that accepts URLs, file URLs and strings, and logs every
// drag callback with os.Logger (subsystem co.coduo.mac-drag.droptarget).
// Prints "droptarget center X,Y" in top-left global display points on start.
// usage: droptarget [x y]   (window top-left, global top-left points; default 200 200)
import AppKit
import os

let log = Logger(subsystem: "co.coduo.mac-drag.droptarget", category: "drop")
let size = CGSize(width: 360, height: 240)

final class DropView: NSView {
    override init(frame: NSRect) {
        super.init(frame: frame)
        registerForDraggedTypes([.URL, .fileURL, .string])
        wantsLayer = true
        layer?.backgroundColor = NSColor.systemTeal.withAlphaComponent(0.35).cgColor
    }
    required init?(coder: NSCoder) { fatalError() }
    override func draggingEntered(_ sender: NSDraggingInfo) -> NSDragOperation {
        log.info("draggingEntered")
        return .copy
    }
    override func draggingExited(_ sender: NSDraggingInfo?) { log.info("draggingExited") }
    override func prepareForDragOperation(_ sender: NSDraggingInfo) -> Bool { true }
    override func performDragOperation(_ sender: NSDraggingInfo) -> Bool {
        let pb = sender.draggingPasteboard
        let urls = pb.readObjects(forClasses: [NSURL.self]) as? [URL] ?? []
        let text = urls.first?.absoluteString ?? pb.string(forType: .string) ?? "<nothing readable>"
        log.info("performDragOperation dropped=\(text, privacy: .public)")
        print("dropped", text); fflush(stdout)
        return true
    }
}

let app = NSApplication.shared
app.setActivationPolicy(.regular)
let args = CommandLine.arguments
let topLeft = CGPoint(x: args.count > 2 ? Double(args[1])! : 200, y: args.count > 2 ? Double(args[2])! : 200)
// AppKit frames are bottom-left origin relative to the primary display.
let primaryHeight = NSScreen.screens[0].frame.height
let frame = NSRect(x: topLeft.x, y: primaryHeight - topLeft.y - size.height, width: size.width, height: size.height)
let window = NSWindow(contentRect: frame, styleMask: [.titled], backing: .buffered, defer: false)
window.title = "macdrag drop target"
window.contentView = DropView(frame: NSRect(origin: .zero, size: size))
window.level = .floating
window.orderFrontRegardless()
let cx = topLeft.x + size.width / 2, cy = topLeft.y + size.height / 2
log.info("ready center=\(cx),\(cy)")
print("droptarget center \(Int(cx)),\(Int(cy))"); fflush(stdout)
app.run()
