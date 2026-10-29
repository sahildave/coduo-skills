#!/usr/bin/env python3
"""Stage a Claude Design bundle: the boards directory plus one gallery page that
shows every board side by side in iframes, which is what the canvas renders.

    gallery_page.py <boards-dir> <stage-dir> --title "Futari v2 — App Screens" [--blurb "..."]

Copies <boards-dir> to <stage-dir>/boards (dropping INDEX.md and licence .txt
files) and writes "<stage-dir>/<title>.html". Push <stage-dir> with DesignSync
write_files using localPath, so no board passes through the model's context.
"""
import argparse
import pathlib
import re
import shutil

ap = argparse.ArgumentParser()
ap.add_argument("boards")
ap.add_argument("stage")
ap.add_argument("--title", required=True)
ap.add_argument("--blurb", default="")
ap.add_argument("--width", type=int, default=393)
ap.add_argument("--height", type=int, default=852)
a = ap.parse_args()

stage = pathlib.Path(a.stage)
if stage.exists():
    shutil.rmtree(stage)
shutil.copytree(a.boards, stage / "boards", ignore=shutil.ignore_patterns("INDEX.md", "*.txt"))

cards = []
for b in sorted((stage / "boards").glob("*.html")):
    m = re.match(r"(.*?)-(\d\d)-(.*)", b.stem)
    nn, slug = (m.group(2), m.group(3)) if m else ("", b.stem)
    cards.append(f'''  <figure>
    <iframe src="boards/{b.name}" width="{a.width}" height="{a.height}" scrolling="no" loading="lazy"></iframe>
    <figcaption><b>{nn}</b> {slug.replace("-", "_").upper()}</figcaption>
  </figure>''')

html = f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>{a.title}</title>
<style>
  body {{ margin:0; background:#111; color:#eee; font: 14px/1.4 -apple-system, system-ui, sans-serif; padding: 32px; }}
  h1 {{ font-size: 20px; font-weight: 600; margin: 0 0 4px; }}
  p {{ color:#999; margin:0 0 24px; }}
  .grid {{ display:flex; flex-wrap:wrap; gap: 32px; }}
  figure {{ margin:0; }}
  iframe {{ border:0; border-radius: 24px; background:#000; display:block; }}
  figcaption {{ margin-top: 8px; color:#bbb; font-family: ui-monospace, monospace; font-size: 12px; }}
  figcaption b {{ color:#FFC84A; }}
</style></head><body>
<h1>{a.title}</h1>
<p>{a.blurb}</p>
<div class="grid">
{chr(10).join(cards)}
</div>
</body></html>'''
(stage / f"{a.title}.html").write_text(html)
print(f"{len(cards)} boards staged in {stage}")
