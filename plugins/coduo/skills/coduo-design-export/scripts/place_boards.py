#!/usr/bin/env python3
"""Number, name and place one export into the repo, then run the checks.

    place_boards.py <manifest.tsv> --jsx <dir> --png <dir> --boards <dir> --baselines <dir>
                    [--prefix futari] [--assets-url-prefix URL] [--family stem=Name]...
                    [--fonts <dir-with-ttfs>] [--width 393] [--height 852]

manifest.tsv, one board per line, tab-separated, in flow order:
    <paper-artboard-name>  <slug>  [gallery-id-or-none]  [note]
The slug is what downstream globs expect (`futari-*-perms-partial.png`), so take it
from the tasks, not from Paper. The Paper name must match `<jsx>/<name>.jsx` and
`<png>/<name>.png` as you stashed them.

Produces:
    <boards>/<prefix>-NN-<slug>.html   converted, self-contained
    <boards>/jsx/<prefix>-NN-<slug>.jsx  Paper's raw export
    <boards>/fonts/*.ttf                 copied from --fonts
    <baselines>/<prefix>-NN-<slug>.png   Paper's 2x export, unchanged
    <boards>/INDEX.md                    one row per board, from the manifest
and then checks: HTML/PNG counts match, every PNG is width*2 wide and
height*2 tall, blank-check.py (if the repo has one) passes on every PNG.
"""
import argparse
import pathlib
import shutil
import subprocess
import sys

HERE = pathlib.Path(__file__).parent


def sips_dims(p):
    out = subprocess.run(["sips", "-g", "pixelWidth", "-g", "pixelHeight", str(p)],
                         capture_output=True, text=True).stdout
    dims = [int(l.split(":")[1]) for l in out.splitlines() if "pixel" in l]
    return tuple(dims)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("manifest")
    ap.add_argument("--jsx", required=True)
    ap.add_argument("--png", required=True)
    ap.add_argument("--boards", required=True)
    ap.add_argument("--baselines", required=True)
    ap.add_argument("--prefix", default="board")
    ap.add_argument("--assets-url-prefix", default="")
    ap.add_argument("--family", action="append", default=[])
    ap.add_argument("--fonts")
    ap.add_argument("--width", type=int, default=393)
    ap.add_argument("--height", type=int, default=852)
    a = ap.parse_args()

    boards, baselines = pathlib.Path(a.boards), pathlib.Path(a.baselines)
    (boards / "jsx").mkdir(parents=True, exist_ok=True)
    baselines.mkdir(parents=True, exist_ok=True)
    if a.fonts:
        (boards / "fonts").mkdir(exist_ok=True)
        for ttf in pathlib.Path(a.fonts).glob("*.ttf"):
            shutil.copy(ttf, boards / "fonts" / ttf.name)

    rows = []
    for i, line in enumerate(l for l in pathlib.Path(a.manifest).read_text().splitlines()
                             if l.strip() and not l.startswith("#")):
        parts = line.split("\t")
        paper, slug = parts[0].strip(), parts[1].strip()
        gallery = parts[2].strip() if len(parts) > 2 and parts[2].strip() else "none"
        note = parts[3].strip() if len(parts) > 3 else ""
        stem = f"{a.prefix}-{i + 1:02d}-{slug}"
        jsx_src = pathlib.Path(a.jsx) / f"{paper}.jsx"
        png_src = pathlib.Path(a.png) / f"{paper}.png"
        for src in (jsx_src, png_src):
            if not src.exists():
                sys.exit(f"missing {src}")
        shutil.copy(jsx_src, boards / "jsx" / f"{stem}.jsx")
        shutil.copy(png_src, baselines / f"{stem}.png")
        cmd = [sys.executable, str(HERE / "jsx2html.py"), str(jsx_src), str(boards / f"{stem}.html"),
               "--title", paper, "--width", str(a.width), "--height", str(a.height),
               "--assets-url-prefix", a.assets_url_prefix]
        for f in a.family:
            cmd += ["--family", f]
        subprocess.run(cmd, check=True, capture_output=True)
        rows.append((stem, gallery, paper, note))

    index = ["# Boards — index", "",
             "| Stem | Gallery ID | Paper artboard | Note |", "|---|---|---|---|"]
    for stem, gallery, paper, note in rows:
        g = f"`{gallery}`" if gallery != "none" else "none"
        index.append(f"| `{stem}` | {g} | `{paper}` | {note} |")
    (boards / "INDEX.md").write_text("\n".join(index) + "\n")

    # checks
    htmls = sorted(p.stem for p in boards.glob(f"{a.prefix}-*.html"))
    pngs = sorted(p.stem for p in baselines.glob(f"{a.prefix}-*.png"))
    ok = True
    if htmls != pngs:
        print("STEM MISMATCH", set(htmls) ^ set(pngs)); ok = False
    want = (a.width * 2, a.height * 2)
    for p in baselines.glob(f"{a.prefix}-*.png"):
        d = sips_dims(p)
        if d != want:
            print(f"SIZE {p.name}: {d} want {want}"); ok = False
    blank = pathlib.Path("scripts/design/blank-check.py")
    if blank.exists():
        for p in baselines.glob(f"{a.prefix}-*.png"):
            r = subprocess.run([sys.executable, str(blank), str(p)], capture_output=True)
            if r.returncode != 0:
                print(f"BLANK-CHECK exit {r.returncode}: {p.name}"); ok = False
    print(f"{len(rows)} boards placed; html={len(htmls)} png={len(pngs)}; "
          f"{'all checks pass' if ok else 'CHECKS FAILED'}")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
