#!/usr/bin/env python3
"""Reuse SVG path data across boards written by hand.

    splice_glyphs.py harvest <board.jsx> "<aria-label>" <GLYPH_NAME>
    splice_glyphs.py splice  <board.jsx>

`harvest` stores the `d=` of the first <path> under an <svg aria-label="..."> in
glyphs/<GLYPH_NAME>.txt (beside the jsx dir). `splice` replaces every
@@GLYPH_NAME@@ in a file with the stored path. Only needed for get_jsx results
small enough to arrive inline, where the model has to write the markup itself:
write @@ARROW_RIGHT@@ once, never a 6 KB path twice.
"""
import pathlib
import re
import sys

cmd, path = sys.argv[1], pathlib.Path(sys.argv[2])
lib = path.parent.parent / "glyphs"
lib.mkdir(exist_ok=True)
text = path.read_text()
if cmd == "harvest":
    label, name = sys.argv[3], sys.argv[4]
    m = re.search(r'aria-label="%s".*?<path[^>]*?\bd="([^"]+)"' % re.escape(label), text, re.S)
    if not m:
        sys.exit(f"no <svg aria-label={label!r}> with a <path> in {path}")
    (lib / f"{name}.txt").write_text(m.group(1))
    print(f"{name}: {len(m.group(1))} chars")
else:
    for g in lib.glob("*.txt"):
        text = text.replace(f"@@{g.stem}@@", g.read_text())
    left = re.findall(r"@@\w+@@", text)
    if left:
        sys.exit(f"unresolved placeholders in {path}: {left}")
    path.write_text(text)
    print(f"{path}: spliced")
