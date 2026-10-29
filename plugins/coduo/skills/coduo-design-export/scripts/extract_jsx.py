#!/usr/bin/env python3
"""Pull the `jsx` string out of a saved Paper get_jsx tool result.

    extract_jsx.py <tool-result.txt> <out.jsx>

When a get_jsx result is bigger than the tool-result cap (~50 KB, i.e. any real
screen) the harness writes it to disk instead of the context and prints the path.
That file is the JSON the tool returned; this lifts d["jsx"] out of it verbatim, so
the markup never has to be re-emitted by the model.
"""
import json
import sys

src, out = sys.argv[1:3]
with open(src) as f:
    data = json.load(f)
jsx = data["jsx"]
if not jsx.strip():
    sys.exit(f"{src}: empty jsx — get_jsx on a page root returns nothing; call it per artboard")
with open(out, "w") as f:
    f.write(jsx)
print(f"{out} {len(jsx)} chars")
