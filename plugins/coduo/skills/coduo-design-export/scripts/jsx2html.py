#!/usr/bin/env python3
"""Turn a Paper get_jsx (inline-styles) dump into a standalone HTML board.

    jsx2html.py <board.jsx> <out.html> [--title T] [--width 393] [--height 852]
                [--assets-url-prefix https://app.paper.design/file-assets/<fileId>/]
                [--family DMMono="DM Mono"]...

Paper's JSX is HTML plus `style={{ camelCase: value }}` objects, JSX comments and
self-closing non-void tags. Nothing else is React-specific, so the conversion is
mechanical: object -> CSS declaration list, camelCase -> kebab, bare numbers -> px
except on the unitless properties, `<div />` -> `<div></div>`.

Two things are rewritten so the file stands alone next to its siblings:
- `url(<assets-url-prefix>X.png)` becomes `url(assets/X.png)`; fetch those files
  with `fetch_assets.sh` into `assets/` beside the output.
- Every `fonts/*.ttf` beside the output gets an @font-face, weight read from the
  filename suffix (Regular 400 ... Black 900) and family from the stem before the
  dash; `--family` maps a stem to a display name when they differ.
"""
import argparse
import pathlib
import re

UNITLESS = {
    "font-weight", "flex", "flex-grow", "flex-shrink", "opacity", "z-index",
    "order", "line-height", "zoom", "tab-size", "column-count", "fill-opacity",
    "stroke-opacity", "stroke-width", "aspect-ratio",
}
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link",
        "meta", "param", "source", "track", "wbr", "path", "circle", "rect",
        "line", "polyline", "polygon", "ellipse", "stop", "use"}
WEIGHTS = {"thin": 100, "extralight": 200, "light": 300, "regular": 400, "medium": 500,
           "semibold": 600, "bold": 700, "extrabold": 800, "black": 900}


def kebab(key):
    key = key.strip().strip("'\"")
    if key.startswith("ms"):  # Webkit/Moz get their leading dash from the regex below
        key = "-" + key
    return re.sub(r"([A-Z])", lambda m: "-" + m.group(1).lower(), key)


def split_top(s):
    out, buf, depth, quote = [], [], 0, None
    for ch in s:
        if quote:
            buf.append(ch)
            if ch == quote:
                quote = None
            continue
        if ch in "'\"`":
            quote = ch
            buf.append(ch)
        elif ch in "([{":
            depth += 1
            buf.append(ch)
        elif ch in ")]}":
            depth -= 1
            buf.append(ch)
        elif ch == "," and depth == 0:
            out.append("".join(buf))
            buf = []
        else:
            buf.append(ch)
    if "".join(buf).strip():
        out.append("".join(buf))
    return out


def css_value(prop, raw):
    raw = raw.strip()
    if raw[:1] in "'\"`" and raw[-1:] == raw[:1]:
        inner = raw[1:-1]
        return inner.replace('"', "'") if "'" not in inner else inner.replace('"', "&quot;")
    if re.fullmatch(r"-?\d+(\.\d+)?", raw):
        return raw if prop in UNITLESS or raw == "0" else raw + "px"
    return raw


def obj_to_css(body):
    decls = []
    for pair in split_top(body):
        if ":" not in pair:
            continue
        k, v = pair.split(":", 1)
        prop = kebab(k)
        decls.append(f"{prop}: {css_value(prop, v)}")
    return "; ".join(decls)


def font_faces(out_path, families):
    faces = []
    for ttf in sorted((out_path.parent / "fonts").glob("*.ttf")):
        stem, _, weight = ttf.stem.partition("-")
        w = WEIGHTS.get(weight.lower(), 400)
        fam = families.get(stem, stem)
        faces.append(f'  @font-face {{ font-family: "{fam}"; font-weight: {w}; '
                     f'src: url(fonts/{ttf.name}) format("truetype"); }}')
    return "\n".join(faces)


def convert(jsx, title, width, height, assets_prefix, faces):
    s = jsx.strip()
    if s.startswith("(") and s.endswith(")"):
        s = s[1:-1]
    s = re.sub(r"\{/\*.*?\*/\}", "", s, flags=re.S)
    s = re.sub(r"\{'\s*'\}", " ", s)
    s = re.sub(r"style=\{\{(.*?)\}\}", lambda m: 'style="' + obj_to_css(m.group(1)) + '"', s, flags=re.S)
    s = re.sub(r"\bclassName=", "class=", s)

    def close(m):
        tag, attrs = m.group(1), m.group(2)
        return f"<{tag}{attrs}/>" if tag.lower() in VOID else f"<{tag}{attrs}></{tag}>"
    s = re.sub(r"<([A-Za-z][\w-]*)((?:\s[^<>]*?)?)\s*/>", close, s, flags=re.S)
    if assets_prefix:
        s = s.replace(assets_prefix, "assets/")
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{title}</title>
<meta name="viewport" content="width={width}">
<style>
{faces}
  html, body {{ margin: 0; background: #000; }}
  .board {{ width: {width}px; height: {height}px; overflow: hidden; }}
</style>
</head>
<body>
<div class="board">
{s.strip()}
</div>
</body>
</html>
"""


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("out")
    ap.add_argument("--title")
    ap.add_argument("--width", type=int, default=393)
    ap.add_argument("--height", type=int, default=852)
    ap.add_argument("--assets-url-prefix", default="")
    ap.add_argument("--family", action="append", default=[], help='stem=Display Name')
    a = ap.parse_args()
    out = pathlib.Path(a.out)
    families = dict(f.split("=", 1) for f in a.family)
    html = convert(pathlib.Path(a.src).read_text(), a.title or out.stem, a.width, a.height,
                   a.assets_url_prefix, font_faces(out, families))
    out.write_text(html)
    print(out, len(html), "bytes")
