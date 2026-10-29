"""A small Markdown -> HTML renderer, stdlib only.

`coduo-flow` runs in any repo — Python, Rust, Go, a repo with no toolchain at
all — so the build cannot assume npm or pip. This covers the subset the notes
actually use: headings, paragraphs, GFM tables, fenced code, blockquotes,
lists, thematic breaks, and inline code/bold/italic/links.

It is deliberately not a CommonMark implementation. If a note needs something
this does not cover, the note is doing too much: split it.
"""

import html
import re

_CODE_SPAN = re.compile(r"`([^`]+)`")
_LINK = re.compile(r"\[([^\]]+)\]\(([^)\s]+)\)")
_BOLD = re.compile(r"\*\*(?=\S)(.+?)(?<=\S)\*\*", re.S)
_EM = re.compile(r"(?<![\w*])[*_](?=\S)(.+?)(?<=\S)[*_](?![\w*])", re.S)
_FENCE = re.compile(r"^```(\w*)\s*$")
_HEADING = re.compile(r"^(#{1,4})\s+(.*)$")
_HR = re.compile(r"^\s{0,3}(?:-{3,}|\*{3,}|_{3,})\s*$")
_UL = re.compile(r"^(\s*)[-*+]\s+(.*)$")
_OL = re.compile(r"^(\s*)\d+[.)]\s+(.*)$")
_QUOTE = re.compile(r"^>\s?(.*)$")
_TABLE_RULE = re.compile(r"^\s*\|?[\s:|-]+\|[\s:|-]*$")


def _slug(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def inline(text):
    """Inline spans. Code is extracted first so its contents stay literal."""
    spans = []

    def stash(m):
        spans.append(html.escape(m.group(1), quote=False))
        return "\x00%d\x00" % (len(spans) - 1)

    text = _CODE_SPAN.sub(stash, text)
    text = html.escape(text, quote=False)
    # An in-page `#id` link is a cross-note jump — navigation, not content — so
    # suppress lavish-axi annotation on it (the surrounding prose stays
    # annotatable). An external link is a reference and stays annotatable.
    text = _LINK.sub(
        lambda m: '<a %shref="%s">%s</a>'
        % ("data-lavish-action " if m.group(2).startswith("#") else "",
           html.escape(m.group(2)), m.group(1)),
        text,
    )
    text = _BOLD.sub(r"<strong>\1</strong>", text)
    text = _EM.sub(r"<em>\1</em>", text)
    return re.sub(r"\x00(\d+)\x00", lambda m: "<code>%s</code>" % spans[int(m.group(1))], text)


def _split_row(line):
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|"):
        line = line[:-1]
    # A pipe inside a code span is content, not a cell boundary.
    cells, buf, in_code = [], "", False
    for ch in line:
        if ch == "`":
            in_code = not in_code
        if ch == "|" and not in_code:
            cells.append(buf.strip())
            buf = ""
        else:
            buf += ch
    cells.append(buf.strip())
    return cells


def render(md, id_prefix=""):
    """Render markdown to HTML. Returns (html, sections) where sections are the
    ## headings, in order, as (id, text) — the panel builds its rail from them.

    `id_prefix` namespaces heading ids per note. Notes share a template, so the
    same heading text ("The claim") slugs to the same id in every note; left
    bare, a lavish-axi selector for an annotated heading (`h1#the-claim`) is
    ambiguous across the whole document, and the walk stops at that id before it
    reaches the `#open-<id>` wrapper. Prefixing with `note-<id>-` makes each
    heading id unique; the rail's `data-goto` reads the same prefixed id, so the
    two stay in step."""
    lines = md.replace("\r\n", "\n").split("\n")
    out, sections, i = [], [], 0
    para = []

    def flush():
        if para:
            out.append("<p>%s</p>" % inline(" ".join(para).strip()))
            para.clear()

    while i < len(lines):
        line = lines[i]

        fence = _FENCE.match(line)
        if fence:
            flush()
            lang, body, i = fence.group(1), [], i + 1
            while i < len(lines) and not _FENCE.match(lines[i]):
                body.append(lines[i])
                i += 1
            cls = ' class="language-%s"' % lang if lang else ""
            out.append(
                "<pre><code%s>%s</code></pre>"
                % (cls, html.escape("\n".join(body), quote=False))
            )
            i += 1
            continue

        if not line.strip():
            flush()
            i += 1
            continue

        if _HR.match(line) and not para:
            flush()
            out.append("<hr>")
            i += 1
            continue

        head = _HEADING.match(line)
        if head:
            flush()
            level, text = len(head.group(1)), head.group(2).strip()
            hid = id_prefix + _slug(text)
            if level == 2:
                sections.append((hid, text))
            out.append('<h%d id="%s">%s</h%d>' % (level, hid, inline(text), level))
            i += 1
            continue

        # GFM table: a header row followed by a delimiter row.
        if "|" in line and i + 1 < len(lines) and _TABLE_RULE.match(lines[i + 1]):
            flush()
            head_cells = _split_row(line)
            i += 2
            rows = []
            while i < len(lines) and "|" in lines[i] and lines[i].strip():
                rows.append(_split_row(lines[i]))
                i += 1
            thead = "".join("<th>%s</th>" % inline(c) for c in head_cells)
            tbody = "".join(
                "<tr>%s</tr>" % "".join("<td>%s</td>" % inline(c) for c in r) for r in rows
            )
            out.append(
                "<div class=\"scroll-x\"><table><thead><tr>%s</tr></thead><tbody>%s</tbody></table></div>"
                % (thead, tbody)
            )
            continue

        if _QUOTE.match(line):
            flush()
            buf = []
            while i < len(lines) and _QUOTE.match(lines[i]):
                buf.append(_QUOTE.match(lines[i]).group(1))
                i += 1
            inner, _ = render("\n".join(buf))
            out.append("<blockquote>%s</blockquote>" % inner)
            continue

        if _UL.match(line) or _OL.match(line):
            flush()
            block, i = _list(lines, i)
            out.append(block)
            continue

        para.append(line.strip())
        i += 1

    flush()
    return "\n".join(out), sections


def _list(lines, i):
    """One list, including nested lists and lazy continuation lines."""
    first = _UL.match(lines[i]) or _OL.match(lines[i])
    ordered = _OL.match(lines[i]) is not None
    base = len(first.group(1))
    items, i = [], i
    while i < len(lines):
        m = _OL.match(lines[i]) if ordered else _UL.match(lines[i])
        other = _UL.match(lines[i]) if ordered else _OL.match(lines[i])
        if m and len(m.group(1)) == base:
            items.append([m.group(2)])
            i += 1
            continue
        if (m and len(m.group(1)) > base) or (other and len(other.group(1)) > base):
            nested, i = _list(lines, i)
            items[-1].append("\x01" + nested)
            continue
        if lines[i].strip() and not other and items and not _HEADING.match(lines[i]):
            # lazy continuation of the current item
            items[-1].append(lines[i].strip())
            i += 1
            continue
        break
    body = []
    for parts in items:
        text = " ".join(p for p in parts if not p.startswith("\x01"))
        nested = "".join(p[1:] for p in parts if p.startswith("\x01"))
        body.append("<li>%s%s</li>" % (inline(text.strip()), nested))
    return "<%s>%s</%s>" % (
        "ol" if ordered else "ul",
        "".join(body),
        "ol" if ordered else "ul",
    ), i
