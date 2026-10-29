"""Frontmatter parsing shared by build_flow.py and check_flow.py.

Handles the three shapes the note schema uses and nothing else:

    key: scalar                     (may wrap onto following lines)
    key: [a, b]                     (may wrap onto following lines)
    key:
      - item                        (block list)

A note needing richer YAML is a note doing too much. Formatters wrap long
arrays across lines, so continuation lines are folded back into their key
before anything is parsed — without that, a prettier-formatted `depends_on`
silently reads as empty and the whole graph loses its edges.
"""

import re

_KEY = re.compile(r"^([a-z_]+):(.*)$")
_ITEM = re.compile(r"^\s*-\s+(.*)$")


def split(text):
    """-> (frontmatter dict, markdown body). Raises if the block is missing."""
    m = re.match(r"^---\n(.*?)\n---\n?", text, re.S)
    if not m:
        raise ValueError("no frontmatter block")
    return parse(m.group(1)), text[m.end():]


def _fold(block):
    """Join continuation lines onto the key they belong to."""
    logical = []
    for line in block.split("\n"):
        if _KEY.match(line) or _ITEM.match(line) or not logical:
            logical.append(line)
        else:
            if line.strip():
                logical[-1] = logical[-1].rstrip() + " " + line.strip()
    return logical


def parse(block):
    data, key, items = {}, None, None

    def close():
        if key is not None and items is not None:
            data[key] = items

    for line in _fold(block):
        kv = _KEY.match(line)
        if kv:
            close()
            key, rest, items = kv.group(1), kv.group(2).strip(), None
            if rest.startswith("["):
                data[key] = _inline(rest)
            elif rest:
                data[key] = _scalar(rest)
            else:
                items = []          # either a block list, or an array that wrapped
            continue
        item = _ITEM.match(line)
        if item is not None and items is not None:
            items.append(_scalar(item.group(1)))
    close()
    # A key whose value wrapped entirely onto the next line arrives here as an
    # empty list with the array text folded in; re-read those.
    for k, v in list(data.items()):
        if isinstance(v, list) and len(v) == 1 and str(v[0]).startswith("["):
            data[k] = _inline(v[0])
    return data


def _inline(text):
    inner = text.strip().lstrip("[").rstrip("]").strip().rstrip(",")
    return [_scalar(p) for p in inner.split(",") if p.strip()]


def _scalar(v):
    v = v.strip()
    if len(v) > 1 and v[0] == v[-1] and v[0] in "\"'":
        return v[1:-1]
    return v
