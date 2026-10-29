#!/usr/bin/env python3
"""Render a flow-map JSON model into the standalone HTML explorer.

Usage: render.py <model.json> [output.html]

The template carries all layout, interaction, and QA-dashboard code; this
only injects the model. Re-run it after every edit to the JSON — the HTML
is a build artifact and hand-edits to it are lost on the next render.
"""
import json
import pathlib
import sys

TEMPLATE = pathlib.Path(__file__).resolve().parent.parent / "assets" / "flow-map-template.html"
PLACEHOLDER = "/*__FLOW_MAP_DATA__*/ null"


def main(argv):
    if not 2 <= len(argv) <= 3:
        sys.exit(__doc__)

    model_path = pathlib.Path(argv[1])
    out_path = pathlib.Path(argv[2]) if len(argv) == 3 else model_path.with_suffix(".html")

    model = json.loads(model_path.read_text())
    template = TEMPLATE.read_text()
    if PLACEHOLDER not in template:
        sys.exit(f"template placeholder missing in {TEMPLATE}")

    # "</script>" inside a string would close the host <script> element.
    payload = json.dumps(model, ensure_ascii=False).replace("</", "<\\/")
    out_path.write_text(template.replace(PLACEHOLDER, payload))

    print(
        f"rendered {out_path} "
        f"({len(model['nodes'])} nodes, {len(model['edges'])} edges, {len(model['flows'])} flows)"
    )


if __name__ == "__main__":
    main(sys.argv)
