#!/usr/bin/env python3
"""Render a folder of notes into one self-contained flow HTML.

    python3 scripts/build_flow.py <flow-dir>

The notes are the source of truth. Every label, colour, edge and section in the
output is read from their frontmatter and body — the HTML holds no data of its
own, so an edit made there disappears at the next build.

Stdlib only, by design: this runs in any repo, whatever its toolchain.
"""

import datetime
import html
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import flowio
import flowmd
import frontmatter

HERE = os.path.dirname(os.path.abspath(__file__))
SHELL = os.path.join(HERE, "..", "assets", "flow-shell.html")

# Palette slots. A `kind` maps to a tone; the tone decides the colour. Keeping
# the palette closed is what makes twenty notes read as one system.
TONES = {
    "plain":  ("var(--n-screen)", "var(--s-screen)"),
    "warn":   ("var(--n-dec)",    "var(--s-dec)"),
    "danger": ("var(--n-rec)",    "var(--s-rec)"),
    "ok":     ("var(--n-end)",    "var(--s-end)"),
    "muted":  ("var(--n-state)",  "var(--s-state)"),
    "sheet":  ("var(--n-sheet)",  "var(--s-sheet)"),
    "gate":   ("var(--n-gate)",   "var(--s-gate)"),
}
DEFAULT_KINDS = {
    "finding":   {"tone": "plain",  "label": "Finding"},
    "decision":  {"tone": "warn",   "label": "Decision"},
    "blocker":   {"tone": "danger", "label": "Blocked"},
    "action":    {"tone": "ok",     "label": "Action"},
    "reference": {"tone": "none",   "label": "Reference"},
}

# A risk and an open question are each one line of frontmatter, split on the
# first colon exactly like `facts` — one convention to learn, not three. The
# prefix is only read as a prefix when every token in it is one we know, so a
# risk that simply happens to contain a colon keeps its whole sentence.
SEVERITIES = {"high": "danger", "medium": "warn", "low": "muted"}

#: WHO ANSWERS IT. Not what the work touches — on a software project everything
#: touches code, and a category matching two thirds of the list is not a filter.
#: The useful split is ownership: each person filters to their own department and
#: sees only what is waiting on them. Tag both when both must agree; the filter
#: ORs, so a shared question shows up for either.
#:
#: Override per project in flow.json with a "categories" object.
QUESTION_CATS = {
    "code": "Code",
    "product": "Design & product",
}

RISK_TOKENS = set(SEVERITIES) | set(QUESTION_CATS) | {"mitigated", "unmitigated"}
WHEN_MAX = 28


def parse_risk(raw):
    """`"high, code, devops: ..."` — severity, an optional `mitigated`, and any
    number of categories, in any order."""
    text, sev, mitigated, cats = str(raw).strip(), "medium", False, []
    if ":" in text:
        head, rest = text.split(":", 1)
        toks = [t.strip().lower() for t in head.replace("/", ",").split(",") if t.strip()]
        if toks and all(t in RISK_TOKENS for t in toks) and rest.strip():
            for t in toks:
                if t in SEVERITIES:
                    sev = t
                elif t in QUESTION_CATS and t not in cats:
                    cats.append(t)
                mitigated = mitigated or t == "mitigated"
            text = rest.strip()
    return {"sev": sev, "tone": SEVERITIES[sev], "mitigated": mitigated,
            "cats": cats, "text": text}


#: Base URL for a bare `#123` reference. Set by `issueUrl` in flow.json; without
#: it a `#123` stays plain text, because guessing a tracker would be worse.
ISSUE_URL = [""]


def linkify(escaped):
    """Turn `#123` into a link to the tracker, in text that is ALREADY escaped.

    Takes escaped input on purpose: every caller has a value it must escape
    anyway, and running the two in the other order would let a note inject
    markup through an issue number."""
    if not ISSUE_URL[0]:
        return escaped
    return re.sub(r"(?<![\w&#])#(\d+)\b",
                  lambda m: '<a class="iss" href="%s%s" target="_blank" rel="noopener">#%s</a>'
                            % (ISSUE_URL[0], m.group(1), m.group(1)),
                  escaped)


def set_categories(cfg):
    """A project's departments are its own. `"categories": {"code": "Backend"}`
    in flow.json replaces the vocabulary wholesale."""
    ISSUE_URL[0] = (cfg.get("issueUrl") or "").strip()
    custom = cfg.get("categories")
    if custom:
        QUESTION_CATS.clear()
        QUESTION_CATS.update(custom)
        RISK_TOKENS.clear()
        RISK_TOKENS.update(set(SEVERITIES) | set(QUESTION_CATS) | {"mitigated", "unmitigated"})


def parse_question(raw):
    """`"code, product: ...?"` — the head is a comma-separated list of
    categories, optionally including `answered`.

    The older form, a short free-text deadline head (`"week 1: ...?"`), still
    parses so existing flows keep working; it lands in `when` and renders as a
    plain chip. New flows should use categories: a deadline written as prose
    ("before the epic") told a reader nothing they could act on."""
    text, when, answered, cats = str(raw).strip(), "", False, []
    if ":" in text:
        head, rest = text.split(":", 1)
        toks = [t.strip().lower() for t in head.replace("/", ",").split(",") if t.strip()]
        known = QUESTION_CATS.keys()
        if rest.strip() and toks and all(t in known or t == "answered" for t in toks):
            text = rest.strip()
            for t in toks:
                if t == "answered":
                    answered = True
                elif t not in cats:
                    cats.append(t)
        elif rest.strip() and "?" not in head and len(head.strip()) <= WHEN_MAX:
            when, text = head.strip(), rest.strip()
            if when.lower() == "answered":
                answered, when = True, ""
    return {"when": when, "answered": answered, "cats": cats, "text": text}


W_NODE, H_NODE, PITCH_X, PITCH_Y = 252, 58, 320, 104
X0, BAND_TOP = 60, 118


def die(msg):
    sys.stderr.write("build_flow: %s\n" % msg)
    sys.exit(1)


def esc(s):
    return html.escape(str(s), quote=False)


def _int(v):
    try:
        return int(str(v).strip())
    except (TypeError, ValueError):
        return None


def epics_of(name, fm):
    """The epics attached to a card, as a list of ints.

    A card is a durable thing — a screen, a system, a rule — and the work that
    lands against it over its life is a list of epics, not one. `epics: [68, 91]`
    is the canonical form; `epic: 68` still parses as a one-element list, so
    older maps keep working. Both at once is ambiguous and dies."""
    plural, singular = fm.get("epics"), fm.get("epic")
    if plural not in (None, "") and singular not in (None, ""):
        die("%s: has both `epic:` and `epics:` — use `epics:` alone" % name)
    raw = plural if plural not in (None, "") else singular
    if raw in (None, ""):
        return []
    items = raw if isinstance(raw, (list, tuple)) else [raw]
    out = []
    for item in items:
        n = _int(str(item).lstrip("#"))
        if n is None:
            die('%s: epic "%s" is not an issue number' % (name, item))
        if n not in out:
            out.append(n)
    return out


def load(flow_dir):
    cfg_path = os.path.join(flow_dir, "flow.json")
    cfg = flowio.read_json(cfg_path) if os.path.exists(cfg_path) else {}
    set_categories(cfg)
    # Written by sync_epics.py, which is the only thing here that touches the
    # network. Absent, every bar simply reads as "no epic written yet", which
    # is the honest default for a flow whose work is not on a tracker at all.
    epics_path = os.path.join(flow_dir, "epics.json")
    epics_doc = flowio.read_json(epics_path) if os.path.exists(epics_path) else {}
    epics = epics_doc.get("epics") or {}
    cfg["_epicsGenerated"] = epics_doc.get("generated", "")
    kinds = dict(DEFAULT_KINDS)
    kinds.update(cfg.get("kinds", {}))
    index = cfg.get("index", "README.md")

    notes = []
    for name in flowio.note_files(flow_dir, index):
        try:
            fm, body = flowio.read_note(flow_dir, name)
        except ValueError:
            die("%s has no frontmatter block" % name)
        except UnicodeDecodeError as e:
            die("%s is not valid UTF-8 (%s)" % (name, e))
        for req in ("id", "title", "node", "kind", "status", "summary"):
            if not fm.get(req):
                die("%s is missing `%s`" % (name, req))
        if fm["kind"] not in kinds:
            die('%s has kind "%s"; flow.json defines %s'
                % (name, fm["kind"], ", ".join(sorted(kinds))))
        body_html, sections = flowmd.render(body, "note-%s-" % fm["id"])
        notes.append({
            "file": name, "id": fm["id"], "title": fm["title"], "node": fm["node"],
            "caption": fm.get("caption", ""), "kind": fm["kind"], "status": fm["status"],
            "confidence": fm.get("confidence", ""), "summary": fm["summary"],
            "updated": str(fm.get("updated", "")),
            "facts": fm.get("facts", []) or [],
            "dep": fm.get("depends_on", []) or [],
            "risks": [parse_risk(r) for r in fm.get("risks", []) or []],
            "questions": [parse_question(q) for q in fm.get("questions", []) or []],
            "loops": fm.get("loops_to", []) or [],
            "executor": (fm.get("executor") or "").strip().lower(),
            "epics": epics_of(name, fm),
            "epic_infos": [epics.get(str(e)) or {} for e in epics_of(name, fm)],
            "start": _int(fm.get("start")),
            # A start with no length is one unit — the checker allows it, so the
            # builder must draw it rather than drop the row in silence.
            "length": _int(fm.get("length")) or (1 if _int(fm.get("start")) else None),
            "html": body_html,
            "sections": sections, "text": re.sub(r"<[^>]+>", " ", body_html),
            "tone": kinds[fm["kind"]]["tone"],
            "kind_label": kinds[fm["kind"]].get("label", fm["kind"]),
        })
    return cfg, kinds, notes


def layer(drawn, by_id):
    """Longest-path layering by Kahn's algorithm, so a dependency cycle is a
    named error instead of an infinite loop."""
    for n in drawn:
        unknown = [d for d in n["dep"] if d not in by_id]
        if unknown:
            die("%s: depends_on %s - not a drawable note. Run check_flow.py."
                % (n["file"], ", ".join('"%s"' % u for u in unknown)))
    indeg = {n["id"]: len(n["dep"]) for n in drawn}
    adj = {n["id"]: [] for n in drawn}
    for n in drawn:
        for d in n["dep"]:
            adj[d].append(n["id"])
    for n in drawn:
        n["layer"] = 0
    ready, settled = [n for n in drawn if not n["dep"]], 0
    while ready:
        n = ready.pop(0)
        settled += 1
        for nxt in adj[n["id"]]:
            t = by_id[nxt]
            t["layer"] = max(t["layer"], n["layer"] + 1)
            indeg[nxt] -= 1
            if indeg[nxt] == 0:
                ready.append(t)
    if settled != len(drawn):
        die("dependency cycle involving: %s"
            % ", ".join(n["id"] for n in drawn if indeg[n["id"]] > 0))


def order(layers, edges, by_id):
    """Barycentre sweeps to cut edge crossings."""
    for lay in layers:
        for i, n in enumerate(lay):
            n["row"] = i
    for sweep in range(4):
        seq = list(reversed(layers)) if sweep % 2 else layers
        for lay in seq:
            def bary(n):
                near = ([by_id[e[0]] for e in edges if e[1] == n["id"]] if sweep % 2 == 0
                        else [by_id[e[1]] for e in edges if e[0] == n["id"]])
                return sum(m["row"] for m in near) / len(near) if near else n["row"]
            lay.sort(key=bary)
            for i, n in enumerate(lay):
                n["row"] = i


def build(flow_dir):
    cfg, kinds, notes = load(flow_dir)
    by_id = {n["id"]: n for n in notes}
    if len(by_id) != len(notes):
        die("duplicate id across notes")
    # A node's categories are the union of its questions' and risks'. Nothing is
    # tagged twice: if a note's open work is all DevOps, the node is DevOps.
    done_statuses = set(cfg.get("doneStatuses") or ["validated"])
    for n in notes:
        cats = []
        for item in list(n["questions"]) + list(n["risks"]):
            for c in item.get("cats") or []:
                if c not in cats:
                    cats.append(c)
        n["cats"] = [c for c in QUESTION_CATS if c in cats]
        # A shipped epic outranks the note's own status: the note says what we
        # decided, the tracker says what shipped, and shipped is the stronger
        # claim. A card whose epic closed is built even if its status never got
        # updated. And once ANY attached epic has shipped the card stays built —
        # a new open epic (a field added to a screen already live) is work in
        # flight against a thing that exists, not a thing become unbuilt again.
        n["shipped_epic"] = any(epic_shipped(i) for i in n["epic_infos"])
        n["open_epic"] = any((i.get("state") == "open") for i in n["epic_infos"])
        n["epic_done"] = n["shipped_epic"]
        n["done"] = n["status"] in done_statuses or n["shipped_epic"]

    # "Nobody has filed any work for this yet" is a fact about the tracker, so
    # the map reads it off the tracker rather than asking an author to declare
    # it as a kind. A kind that means "not built" stops being true the day the
    # work lands, and then contradicts the tick beside it.
    #
    # `start` is the test for "this is work still to come": a note on the
    # timeline is scheduled work, where a note without one may be a finding, a
    # decision, or a screen that shipped long before this map existed. An open
    # epic already attached is work in progress, not unfiled, so it is NOT
    # unbuilt — only a timeline card with no epics at all is. The whole thing
    # switches on for a flow that uses the join at all, so a decision map with
    # no epics anywhere is untouched.
    uses_epics = any(n["epics"] for n in notes)
    for n in notes:
        n["unbuilt"] = bool(uses_epics and n["start"] and not n["done"]
                            and not n["epics"])
        n["has_q"] = any(not q["answered"] for q in n["questions"])
        n["has_risk"] = any(not r["mitigated"] for r in n["risks"])

    drawn = [n for n in notes if n["tone"] != "none"]
    drawn_ids = {n["id"] for n in drawn}
    edges = [(d, n["id"]) for n in drawn for d in n["dep"] if d in drawn_ids]

    # A loop edge is a real path the reader can take back — a free tier that
    # offers an upgrade, a retry after a failure. It is drawn, but it is kept
    # out of the layering graph, so a flow that legitimately cycles does not
    # have to leave its return path undrawn.
    loops = []
    for n in drawn:
        for t in n["loops"]:
            if t not in drawn_ids:
                die('%s: loops_to "%s" is not a drawable note' % (n["file"], t))
            loops.append((n["id"], t))

    spine_ids = cfg.get("spine", [])
    spine = set(zip(spine_ids, spine_ids[1:]))
    for pair in spine:
        if pair not in edges:
            die('spine names %s -> %s, which is not a dependency edge' % pair)

    layer(drawn, {n["id"]: n for n in drawn})
    layers = []
    for n in drawn:
        while len(layers) <= n["layer"]:
            layers.append([])
        layers[n["layer"]].append(n)
    order(layers, edges, {n["id"]: n for n in drawn})

    rows = max(len(l) for l in layers)
    band_h = rows * H_NODE + (rows - 1) * (PITCH_Y - H_NODE)
    cy = BAND_TOP + band_h / 2
    for lay in layers:
        h = len(lay) * H_NODE + (len(lay) - 1) * (PITCH_Y - H_NODE)
        for i, n in enumerate(lay):
            n["x"] = X0 + n["layer"] * PITCH_X
            n["y"] = int(cy - h / 2 + i * PITCH_Y)
    width = X0 * 2 + (len(layers) - 1) * PITCH_X + W_NODE
    # The legend used to be drawn into the SVG, which meant it scrolled away
    # the moment a reader panned right — exactly when they needed it. It is HTML
    # now, pinned above the map.
    legend_y = 0
    height = BAND_TOP + band_h + 88

    svg = render_svg(cfg, kinds, layers, edges, loops, spine, by_id, width, height, legend_y)
    map_bars, map_key = render_map_controls(cfg, kinds, drawn, spine, loops)
    return cfg, notes, drawn, edges, layers, svg, map_bars, map_key


def render_svg(cfg, kinds, layers, edges, loops, spine, by_id, width, height, legend_y):
    p = []
    lanes = cfg.get("lanes") or ["LAYER %d" % (i + 1) for i in range(len(layers))]
    for i, lane in enumerate(lanes[:len(layers)]):
        p.append('<text class="lane" x="%d" y="82" text-anchor="middle">%s</text>'
                 % (X0 + i * PITCH_X + W_NODE // 2, esc(lane)))

    band_bottom = max(n["y"] + H_NODE for lay in layers for n in lay)
    for a_id, b_id in edges:
        a, b = by_id[a_id], by_id[b_id]
        x1, y1 = a["x"] + W_NODE, a["y"] + H_NODE / 2
        x2, y2 = b["x"], b["y"] + H_NODE / 2
        dx = max(46, (x2 - x1) * 0.44)
        crit = (a_id, b_id) in spine
        # A spine edge spanning more than one layer would pass behind the cards
        # between, reading as if it ended there. Bow it clear of the band.
        bow = (band_bottom + 26 - (y1 + y2) / 2) if crit and b["layer"] - a["layer"] > 1 else 0
        p.append('<path d="M%g %g C%g %g %g %g %g %g" fill="none" stroke="%s" '
                 'stroke-width="%s" %smarker-end="url(#%s)"/>'
                 % (x1, y1, x1 + dx, y1 + bow, x2 - dx, y2 + bow, x2 - 3, y2,
                    "var(--s-end)" if crit else "var(--edge)",
                    "2.2" if crit else "1.2",
                    "" if crit else 'opacity=".65" ', "ahc" if crit else "ah"))

    # Loop edges last among the paths, bowed under the band so they read as a
    # return rather than another forward dependency.
    for a_id, b_id in loops:
        a, b = by_id[a_id], by_id[b_id]
        x1, y1 = a["x"], a["y"] + H_NODE / 2
        x2, y2 = b["x"] + W_NODE, b["y"] + H_NODE / 2
        under = band_bottom + 44
        p.append('<path class="loop" d="M%g %g C%g %g %g %g %g %g" fill="none" '
                 'stroke="var(--s-state)" stroke-width="1.4" stroke-dasharray="6 4" '
                 'marker-end="url(#ahl)"/>'
                 % (x1, y1, x1 - 40, under, x2 + 40, under, x2 + 3, y2))

    for lay in layers:
        for n in lay:
            fill, stroke = TONES[n["tone"]]
            rx = 22 if n["layer"] == len(layers) - 1 and len(lay) == 1 else 13
            # Up to three dots, right-aligned in the card's top corner. Red for
            # an unheld risk, amber for an unanswered question, green for
            # settled — read right to left, "done, but still owes answers".
            # There is no dot for "not settled": the card's own colour and the
            # absence of green already say that, and a fourth state on a 252px
            # card is noise.
            marks = []
            if n.get("has_risk"):
                marks.append(("dot", "var(--s-rec)"))
            if n.get("has_q"):
                marks.append(("dot", "var(--tag-new)"))
            if n.get("epic_done"):
                marks.append(("tick", "var(--tag-live)"))
            elif n["status"] in ("validated", "decided"):
                marks.append(("dot", "var(--tag-live)"))
            dots = "".join(
                node_mark(kind, colour,
                          n["x"] + W_NODE - 13 - (len(marks) - 1 - i) * 11, n["y"] + 12)
                for i, (kind, colour) in enumerate(marks))
            diamond = ('<path d="M%d %d l7 7-7 7-7-7z" fill="%s"/>'
                       % (n["x"] + 17, n["y"] + H_NODE // 2 - 7, stroke)) if n["tone"] == "warn" else ""
            shift = 9 if diamond else 0
            cx = n["x"] + W_NODE // 2 + shift
            # The kind says what it is; the dashed red edge says nobody has
            # written an epic for it. Two claims, two channels, neither
            # overwriting the other.
            edge = 'stroke="var(--s-rec)" stroke-width="1.5" stroke-dasharray="6 4"' \
                if n.get("unbuilt") else 'stroke="%s" stroke-width="1.5"' % stroke
            p.append(
                '<g id="node-%s" class="node%s" data-note="%s" data-cats="%s" data-done="%s" '
                'tabindex="0" role="button" aria-label="Open %s">'
                '<rect x="%d" y="%d" width="%d" height="%d" rx="%d" fill="%s" %s/>'
                '%s%s'
                '<text class="nl" x="%d" y="%d" text-anchor="middle">%s</text>'
                '<text class="ns" x="%d" y="%d" text-anchor="middle">%s</text></g>'
                % (n["id"], " unbuilt" if n.get("unbuilt") else "",
                   n["id"], " ".join(n.get("cats") or ["none"]), "1" if n.get("done") else "0",
                   esc(n["title"]), n["x"], n["y"], W_NODE, H_NODE, rx, fill, edge,
                   diamond, dots,
                   cx, n["y"] + 25, esc(n["node"]),
                   cx, n["y"] + 42, esc(n["caption"])))

    return ('<svg viewBox="0 0 %d %d" width="%d" height="%d" role="img" aria-label="%s">\n'
            '  <defs>\n'
            '    <marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto">'
            '<path d="M0 0l10 5-10 5z" fill="var(--edge)"/></marker>\n'
            '    <marker id="ahc" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto">'
            '<path d="M0 0l10 5-10 5z" fill="var(--s-end)"/></marker>\n'
            '    <marker id="ahl" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto">'
            '<path d="M0 0l10 5-10 5z" fill="var(--s-state)"/></marker>\n  </defs>\n  %s\n</svg>'
            % (width, height, width, height,
               esc(cfg.get("title", "Flow map")) + " dependency map",
               "\n  ".join(p)))


def synced_stamp(iso):
    """The "last updated" line in the eyebrow.

    Rendered here in absolute terms so the page still says something with
    scripting off, and upgraded in the browser to "3 days ago" — because the
    relative half has to be computed when the page is *read*, not when it is
    built. A "just now" baked in at build time is the exact lie this line
    exists to prevent."""
    if not iso:
        return ""
    try:
        when = datetime.datetime.fromisoformat(iso)
    except ValueError:
        return ""
    # %-I is not portable, and a leading zero on the hour reads as a timestamp
    # rather than as a time someone would say out loud.
    text = "%d:%02d %s %d %s" % (
        (when.hour % 12) or 12, when.minute, "AM" if when.hour < 12 else "PM",
        when.day, when.strftime("%b"))
    return ('<span class="synced" data-iso="%s">Last updated: <b>%s</b></span>'
            % (esc(iso), esc(text)))


def epic_shipped(ep):
    """GitHub reports an epic closed as *not planned* with the same `state` as
    one that shipped, so reading `state` alone paints abandoned work green.
    Anything not explicitly abandoned counts as shipped, which keeps an older
    `epics.json` with no `stateReason` behaving as it did."""
    return (ep or {}).get("state") == "closed" and \
        (ep.get("stateReason") or "").lower() not in ("not_planned", "not planned")


def node_mark(kind, colour, cx, cy):
    """A card's top-right marks. Everything is a dot except "its epic closed",
    which is a tick: on a wall of coloured dots a *shape* reads from across the
    room, and a fourth hue does not."""
    if kind != "tick":
        return '<circle cx="%d" cy="%d" r="3.5" fill="%s"/>' % (cx, cy, colour)
    return ('<circle cx="%d" cy="%d" r="5.5" fill="%s"/>'
            '<path d="M%.1f %.1f l1.7 1.8 3.4-3.8" fill="none" stroke="var(--card)" '
            'stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"/>'
            % (cx, cy, colour, cx - 2.6, cy - 0.2))


def epic_url(num, info):
    """One epic's tracker URL. Prefers what `sync_epics.py` read back from
    GitHub; falls back to `issueUrl` so an epic named before the first sync
    still links somewhere."""
    if (info or {}).get("url"):
        return info["url"]
    return (ISSUE_URL[0] + str(num)) if (num and ISSUE_URL[0]) else ""


#: Who can actually do a piece of work. Drives the Gantt bar's fill, because on
#: a plan executed by agents this is a more useful sort key than dependency
#: depth: the graph says what is possible, this says what can start tonight.
EXECUTORS = {
    "unattended": "Unattended — an agent can run it",
    "human": "Human — credentials, hardware or a decision",
    "mixed": "Mixed — an unattended half and a human half",
}
EXECUTOR_ORDER = ("unattended", "mixed", "human")


def render_map_controls(cfg, kinds, drawn, spine, loops):
    """Everything that used to be baked into the SVG or missing from it: the
    category filter, the shipped-work switch, and the legend — all outside the
    horizontal scroller so panning the map never scrolls them away."""
    bars = ""
    opts = cat_options(drawn)
    if opts:
        bars += filterbar("cats", opts, "Filter")
    if any(n.get("done") for n in drawn):
        bars += ('<div class="filterbar" data-group="done" data-multi="1">'
                 '<span class="flabel">Shipped</span>'
                 '<button type="button" class="chip" data-filter="done" data-value="done" '
                 'aria-pressed="false">Dim what is built</button></div>')
    # One row: two filter bars stacked cost a whole line of vertical space above
    # a map that is already the tallest thing on the page.
    bars = '<div class="map-bars">%s</div>' % bars if bars else ""

    keys = []
    for kind, spec in kinds.items():
        if spec["tone"] == "none" or not any(n["kind"] == kind for n in drawn):
            continue
        fill, stroke = TONES[spec["tone"]]
        keys.append('<span><i class="sw" style="background:%s;border-color:%s"></i>%s</span>'
                    % (fill, stroke, esc(spec.get("label", kind))))
    if any(n.get("unbuilt") for n in drawn):
        keys.append('<span><i class="sw unbuilt"></i>No epic written yet</span>')
    if any(n.get("has_risk") for n in drawn):
        keys.append('<span><i class="dot" style="background:var(--s-rec)"></i>Unheld risk</span>')
    if any(n.get("has_q") for n in drawn):
        keys.append('<span><i class="dot" style="background:var(--tag-new)"></i>Open question</span>')
    if any(n.get("done") or n["status"] in ("validated", "decided") for n in drawn):
        keys.append('<span><i class="dot" style="background:var(--tag-live)"></i>Settled</span>')
    # The tick is a different claim from the dot beside it — settled is what we
    # decided, shipped is what the tracker says landed — so it has to be named.
    if any(n.get("epic_done") for n in drawn):
        keys.append('<span><i class="dot tick" style="background:var(--tag-live)"></i>'
                    'Shipped &mdash; its epic is closed</span>')
    if spine:
        keys.append('<span><i class="ln crit"></i>%s</span>'
                    % esc(cfg.get("spineLabel", "Critical path")))
    if loops:
        keys.append('<span><i class="ln loop"></i>Loops back</span>')
    # Filters above the map, legend below it: the filters are a control and
    # belong under the reader's hand, the legend is a reference and belongs
    # where a reader looks after seeing something they cannot name.
    return bars, '<div class="map-key">%s</div>' % "".join(keys)


def render_gantt(cfg, notes, spine_ids):
    """Epic-level order, drawn only when the flow declares a timeline and at
    least one note is placed on it. The map shows what blocks what; this shows
    when — the one thing a dependency graph cannot say."""
    tl = cfg.get("timeline") or {}
    units = _int(tl.get("units"))
    placed = [n for n in notes if n["start"] and n["length"]]
    if not units or not placed:
        return ""
    label = tl.get("unitLabel", "Unit")
    bands = tl.get("bands", []) or []

    def in_band(i):
        """Which band a unit falls in, as a CSS suffix — bands are distinct
        stretches and must not read as one continuous wash."""
        for bi, b in enumerate(bands):
            if _int(b.get("from")) <= i <= _int(b.get("to")):
                return " band band-%d" % (bi % 4)
        return ""

    cols = "grid-template-columns:15rem repeat(%d,1fr)" % units
    rows = ['<div class="gantt-row ruler" style="%s"><div class="corner">%s</div>%s</div>'
            % (cols, esc(tl.get("rowLabel", "Workstream")),
               "".join('<div class="tick%s">%d</div>' % (in_band(i), i)
                       for i in range(1, units + 1)))]
    for n in sorted(placed, key=lambda n: (n["start"], n["length"])):
        cells = "".join('<div class="cell%s"></div>' % in_band(i)
                        for i in range(1, units + 1))
        crit = " crit" if n["id"] in spine_ids else ""
        # Executor beats the spine for the bar's fill: on a plan run by agents,
        # "who can do this" is the thing a reader needs from across the room,
        # and the critical path is already drawn on the map itself.
        if n["executor"] in EXECUTORS:
            crit = " x-" + n["executor"]
        # Three tracker states, and only one changes the fill toward green. A
        # shipped epic makes the bar green and is the last word — a card with a
        # shipped epic and a newer open one is still built. A card with epics
        # but none shipped is in progress (ordinary fill). Only a card with no
        # epics at all reads as hatched: the plan says it, nobody has filed it.
        if n.get("shipped_epic"):
            crit += " e-done"
        elif not n.get("epics"):
            crit += " e-none"
        chips = []
        for num, info in zip(n["epics"], n["epic_infos"]):
            url = epic_url(num, info)
            if not url:
                continue
            chips.append('<a class="ep%s" href="%s" target="_blank" '
                         'rel="noopener" title="%s">#%d</a>'
                         % (" done" if epic_shipped(info) else "", esc(url),
                            esc(info.get("title") or "Epic on the tracker"), num))
        chip = "".join(chips)
        span = "grid-column:%d/%d" % (n["start"], min(n["start"] + n["length"], units + 1))
        rows.append(
            '<div class="gantt-row" style="%s">'
            '<div class="gantt-name"><span class="t" data-note="%s">%s</span>%s</div>'
            '<div class="track" style="grid-column:2/-1;%s">%s</div>'
            '<div class="bars" style="grid-column:2/-1;%s">'
            '<div class="bar%s" data-note="%s" style="%s"><span class="bl">%d %s%s</span>'
            '</div></div></div>'
            % (cols, n["id"], esc(n["node"]), chip,
               "grid-template-columns:repeat(%d,1fr)" % units, cells,
               "grid-template-columns:repeat(%d,1fr)" % units,
               crit, n["id"], span, n["length"], esc(label.lower()),
               "s" if n["length"] != 1 else ""))

    used = [x for x in EXECUTOR_ORDER if any(n["executor"] == x for n in placed)]
    if used:
        keys = ['<span><i class="x-%s"></i>%s</span>' % (x, EXECUTORS[x]) for x in used]
        if any(not n["executor"] for n in placed):
            keys.insert(0, '<span><i></i>Scheduled</span>')
    else:
        keys = ['<span><i></i>Scheduled</span>']
        if any(n["id"] in spine_ids for n in placed):
            keys.append('<span><i class="crit"></i>%s</span>'
                        % esc(cfg.get("spineLabel", "Critical path")))
    if any(n.get("shipped_epic") for n in placed):
        keys.append('<span><i class="e-done"></i>Shipped &mdash; an epic is closed</span>')
    if any(not n.get("epics") for n in placed):
        keys.append('<span><i class="e-none"></i>No epic on the tracker yet</span>')
    # The two halves of the legend say different things — a solid swatch is a
    # bar's fill, a bordered one is a shaded stretch of the chart behind them.
    # A rule between them stops the second group reading as more bar types.
    if bands:
        keys.append('<span class="key-sep" aria-hidden="true"></span>')
    for bi, b in enumerate(bands):
        keys.append('<span class="key-band"><i class="band band-%d"></i>%s</span>'
                    % (bi % 4, esc(b.get("label", ""))))

    return (section("schedule",
            '  <div class="full"><div class="scroller" tabindex="0" role="region" '
            'aria-label="Timeline, scrollable"><div class="gantt">%s</div>'
            '<div class="gantt-key">%s</div></div></div>'
            % ("".join(rows), "".join(keys)),
            esc(tl.get("title", "When each piece runs")),
            esc(tl.get("lede", "Order and overlap. The roadmap says what blocks what; "
                               "this says when. Click a row to open its note."))))


def section(key, inner, title, lede):
    """Every tab is one of these: a heading, a standfirst, then the thing."""
    return ('  <section class="tabpanel" id="tab-%s" role="tabpanel" aria-labelledby="tb-%s" hidden>\n'
            '  <h2 class="sec-head">%s</h2>\n  <p>%s</p>\n%s</section>'
            % (key, key, title, lede, inner))


def row(chip_tone, chip, text, note, ref="", data="", cats=(), show_src=True, id_ns=""):
    """One risk or one question, carrying the note it came from. The link back
    is the point: a risk with no note behind it is a mood, not a finding.

    `ref` is the stable handle (Q-7, R-12) a reader quotes when answering in
    another thread — the reason it is rendered first and in mono.

    `id_ns` prefixes the row's id so the copy rendered inside a note panel does
    not collide with the canonical tab-level `id="q-7"`. The tab copy keeps the
    bare handle; the in-note copy becomes `note-<id>-q-7`. Without this, a
    returned lavish-axi selector `li#q-7` could resolve to any of three live
    copies of the same row."""
    tags = ""
    if cats:
        tags = "".join('<span class="cat">%s</span>' % esc(QUESTION_CATS.get(c, c)) for c in cats)
    src = ('%sfrom <button type="button" data-note="%s">%s</button>'
           % (tags, note["id"], esc(note["node"]))) if show_src else tags
    return ('<li%s%s><span>%s%s</span><div><p class="txt">%s</p>%s</div></li>'
            % (' id="%s%s"' % (id_ns, ref.lower()) if ref else "", data,
               '<span class="ref">%s</span>' % esc(ref) if ref else "",
               '<span class="tag %s">%s</span>' % (chip_tone, esc(chip)) if chip else "",
               linkify(esc(text)), '<p class="src">%s</p>' % src if src else ""))


def number_items(notes):
    """Q-1..Q-n and R-1..R-n, assigned in note order so a handle a reader quoted
    yesterday still points at the same line today. Notes load in filename order,
    so this is stable across builds as long as no file is renumbered."""
    qi = ri = 0
    for n in notes:
        for q in n["questions"]:
            qi += 1
            q["ref"] = "Q-%d" % qi
        for r in n["risks"]:
            ri += 1
            r["ref"] = "R-%d" % ri


def cat_options(items):
    """The category chips a list actually needs — never the full vocabulary, so
    a flow that never mentions design does not carry a dead Design chip."""
    used = [k for k in QUESTION_CATS if any(k in (i.get("cats") or []) for i in items)]
    if not used:
        return []
    opts = [("", "All")] + [(k, QUESTION_CATS[k]) for k in used]
    if any(not (i.get("cats") or []) for i in items):
        opts.append(("none", "Uncategorised"))
    return opts


def filterbar(name, options, lead, multi=True):
    """A row of toggles above a list. Multi-select ORs; single-select is a
    plain radio group with an All. Filtering is done in the page rather than by
    rebuilding, so a chosen filter survives switching tabs and back."""
    chips = "".join(
        '<button type="button" class="chip%s" data-filter="%s" data-value="%s"%s>%s</button>'
        % (" on" if v == "" else "", name, v,
           ' aria-pressed="%s"' % ("true" if v == "" else "false"), esc(label))
        for v, label in options)
    return ('<div class="filterbar" data-group="%s" data-multi="%s">'
            '<span class="flabel">%s</span>%s</div>\n' % (name, "1" if multi else "", esc(lead), chips))


def render_questions(cfg, notes):
    """What the plan is assuming an answer to. Unanswered first, because the
    answered ones are history and the open ones are this week's work."""
    cq = cfg.get("questions") or {}
    items = [(q, n) for n in notes for q in n["questions"]]
    if not items:
        return "", 0
    live = [(q, n) for q, n in items if not q["answered"]]
    done = [(q, n) for q, n in items if q["answered"]]

    def qrow(tone, chip, q, n):
        cats = q.get("cats") or []
        data = ' data-cats="%s"' % " ".join(cats or ["none"])
        return row(tone, chip, q["text"], n, ref=q.get("ref", ""), data=data, cats=cats)

    inner = ""
    opts = cat_options([q for q, _ in items])
    if opts:
        inner += filterbar("cats", opts, "Filter")
    if live:
        inner += '  <ul class="rows" data-filterable>%s</ul>\n' % "".join(
            qrow("warn", q["when"], q, n) for q, n in live)
        inner += '  <p class="no-rows" hidden>No open question matches that filter.</p>\n'
    else:
        inner += '  <p class="grp">Nothing is waiting on an answer.</p>\n'
    if done:
        inner += ('  <p class="grp">Answered</p>\n'
                  '  <ul class="rows settled" data-filterable>%s</ul>\n'
                  % "".join(qrow("ok", "answered", q, n) for q, n in done))
    return section("questions", inner,
                   esc(cq.get("title", "Open questions")),
                   esc(cq.get("lede", "Answer these in week 1. Each one changes what the plan "
                                      "says, and the roadmap already assumes an answer."))), len(live)


def render_risks(cfg, notes):
    """Unmitigated first and worst first — the order someone reads this in when
    they are deciding what to do about it today."""
    cr = cfg.get("risks") or {}
    items = [(r, n) for n in notes for r in n["risks"]]
    if not items:
        return "", 0
    rank = {"high": 0, "medium": 1, "low": 2}
    live = sorted([(r, n) for r, n in items if not r["mitigated"]], key=lambda i: rank[i[0]["sev"]])
    held = sorted([(r, n) for r, n in items if r["mitigated"]], key=lambda i: rank[i[0]["sev"]])
    def rrow(tone, r, n):
        cats = r.get("cats") or []
        return row(tone, r["sev"], r["text"], n, ref=r.get("ref", ""),
                   data=' data-sev="%s" data-cats="%s"' % (r["sev"], " ".join(cats or ["none"])),
                   cats=cats)

    present = [k for k in ("high", "medium", "low") if any(r["sev"] == k for r, _ in items)]
    inner = filterbar("sev", [("", "All")] + [(k, k.title()) for k in present],
                      "Severity", multi=False)
    copts = cat_options([r for r, _ in items])
    if copts:
        inner += filterbar("cats", copts, "Filter")
    if live:
        inner += '  <ul class="rows" data-filterable>%s</ul>\n' % "".join(
            rrow(r["tone"], r, n) for r, n in live)
        inner += '  <p class="no-rows" hidden>No risk matches those filters.</p>\n'
    else:
        inner += '  <p class="grp">Every risk here has a mitigation.</p>\n'
    if held:
        inner += ('  <p class="grp">Mitigated</p>\n'
                  '  <ul class="rows settled" data-filterable>%s</ul>\n'
                  % "".join(rrow("muted", r, n) for r, n in held))
    return section("risks", inner,
                   esc(cr.get("title", "Risk")),
                   esc(cr.get("lede", "Where the plan actually breaks. Unmitigated first, "
                                      "worst first — not in the order they were found."))), len(live)


def render_quick(notes, open_q, unmit):
    """Top right, above everything: what is still unanswered and what is still
    unheld. A reader who looks at nothing else should see these two numbers."""
    total_q = sum(len(n["questions"]) for n in notes)
    total_r = sum(len(n["risks"]) for n in notes)
    if not total_q and not total_r:
        return ""
    lines = []
    if total_q:
        lines.append(('questions', open_q, "open question" + ("" if open_q == 1 else "s"),
                      "%d answered" % (total_q - open_q) if total_q - open_q else "none answered yet"))
    if total_r:
        lines.append(('risks', unmit, "unmitigated risk" + ("" if unmit == 1 else "s"),
                      "of %d tracked" % total_r))
    return ('<aside class="quick"><p>Still open</p>%s</aside>' % "".join(
        '<button type="button" data-tab="%s"><b class="%s">%d</b>'
        '<span class="lbl">%s<i>%s</i></span></button>'
        % (key, "clear" if not n else "hot" if key == "risks" else "", n, esc(label), esc(sub))
        for key, n, label, sub in lines))


def render_tabnav(panels):
    """One tab is not a tab bar — a flow with no timeline, no risks and no open
    questions is still just a map, and should look like one."""
    live = [t for t in panels if t[2]]
    if len(live) < 2:
        return ""
    return ('  <nav class="tabs" role="tablist" aria-label="Sections">%s</nav>' % "".join(
        '<button type="button" role="tab" id="tb-%s" aria-controls="tab-%s" data-tab="%s" '
        'aria-selected="%s" tabindex="%d">%s%s</button>'
        % (key, key, key, "true" if i == 0 else "false", 0 if i == 0 else -1, esc(label),
           '<em>%d</em>' % count if count else "")
        for i, (key, label, _, count) in enumerate(live)))


def note_article(n):
    facts = "".join(
        '<span class="fact"><b>%s</b>%s</span>'
        % (esc(f.split(":", 1)[0]), linkify(esc(":" .join(f.split(":", 1)[1:]).strip())))
        if ":" in f else '<span class="fact">%s</span>' % linkify(esc(f))
        for f in n["facts"])
    rail = "".join('<a data-lavish-action data-goto="%s">%s</a>' % (sid, esc(txt))
                   for sid, txt in n["sections"])

    # Details / Open questions / Risks, using exactly the row markup the
    # top-level tabs use — one component, so the two places can never drift into
    # naming or ordering the same thing differently. The tab bar only appears
    # when there is a second tab to go to.
    def rows(kind, live, held, held_label):
        out = ""
        if live:
            out += '<ul class="rows">%s</ul>' % "".join(live)
        if held:
            out += ('<p class="grp">%s</p><ul class="rows settled">%s</ul>'
                    % (esc(held_label), "".join(held)))
        return out or '<p class="grp">Nothing here.</p>'

    ns = "note-%s-" % n["id"]
    q_html = rows("q",
        [row("warn", q["when"], q["text"], n, ref=q["ref"], cats=q.get("cats"), show_src=False, id_ns=ns)
         for q in n["questions"] if not q["answered"]],
        [row("ok", "answered", q["text"], n, ref=q["ref"], cats=q.get("cats"), show_src=False, id_ns=ns)
         for q in n["questions"] if q["answered"]], "Answered")
    r_html = rows("r",
        [row(r["tone"], r["sev"], r["text"], n, ref=r["ref"], cats=r.get("cats"), show_src=False, id_ns=ns)
         for r in n["risks"] if not r["mitigated"]],
        [row("muted", r["sev"], r["text"], n, ref=r["ref"], cats=r.get("cats"), show_src=False, id_ns=ns)
         for r in n["risks"] if r["mitigated"]], "Mitigated")

    n_q = len([q for q in n["questions"] if not q["answered"]])
    n_r = len([r for r in n["risks"] if not r["mitigated"]])
    tabs = [("details", "Details", 0)]
    if n["questions"]:
        tabs.append(("questions", "Open questions", n_q))
    if n["risks"]:
        tabs.append(("risks", "Risks", n_r))

    # Facts are reference material — useful to an agent reading the note, mostly
    # noise to a human who wants the argument. Collapsed, with the count on the
    # summary so it is obvious there is something behind it.
    facts_html = ""
    if facts:
        facts_html = ('<details class="facts-wrap"><summary>At a glance'
                      '<em>%d</em></summary><div class="facts">%s</div></details>'
                      % (len(n["facts"]), facts))
    details = (epic_block(n) + facts_html
               + ('<nav class="rail"><p>Table of contents</p><div>%s</div></nav>' % rail if rail else "")
               + '<div class="prose">%s</div>' % n["html"])

    if len(tabs) == 1:
        inner = details
    else:
        inner = ('<nav class="ntabs" role="tablist">%s</nav>' % "".join(
            '<button type="button" role="tab" data-ntab="%s" aria-selected="%s">%s%s</button>'
            % (key, "true" if i == 0 else "false", esc(label),
               '<em>%d</em>' % count if count else "")
            for i, (key, label, count) in enumerate(tabs)))
        panes = {"details": details, "questions": q_html, "risks": r_html}
        inner += "".join(
            '<div class="npane" data-ntab="%s"%s>%s</div>'
            % (key, "" if i == 0 else " hidden", panes[key])
            for i, (key, _, _) in enumerate(tabs))

    return (
        '<article class="note" id="note-%s" hidden data-title="%s" data-summary="%s">\n'
        '<p class="note-meta"><span class="tag %s">%s</span><span>%s</span>%s'
        '<span class="note-file">%s</span></p>\n'
        '<h1 class="note-title">%s</h1>\n'
        '<p class="standfirst">%s</p>\n'
        '%s</article>'
        % (n["id"], esc(n["title"]), esc(n["summary"]),
           n["tone"], esc(n["kind_label"]), esc(n["status"]),
           '<span>confidence: %s</span>' % esc(n["confidence"]) if n["confidence"] else "",
           esc(n["file"]), esc(n["title"]), esc(n["summary"]), inner))


def _one_epic(num, info):
    """One epic and its children, as a labelled block in the note panel."""
    url, state = epic_url(num, info), (info.get("state") or "")
    shipped = epic_shipped(info)
    if state == "closed" and not shipped:
        state = "closed, not planned"
    head = ('<span class="lbl">Epic</span>'
            '<a class="iss" href="%s" target="_blank" rel="noopener">#%d%s</a>'
            % (esc(url), num, " " + esc(info["title"]) if info.get("title") else ""))
    head += ('<span class="est %s">%s</span>'
             % ("ok" if shipped else "open", esc(state)) if state
             else '<span class="est">not synced</span>')
    subs = "".join(
        '<li><span class="est %s">%s</span>'
        '<a class="iss" href="%s" target="_blank" rel="noopener">#%d</a> %s</li>'
        % ("ok" if sub_i.get("state") == "closed" else "open",
           esc(sub_i.get("state") or ""), esc(sub_i.get("url") or ""),
           sub_i["number"], esc(sub_i.get("title") or ""))
        for sub_i in info.get("subIssues") or [])
    return ('<div class="epic-box%s"><p class="epic-hd">%s</p>%s</div>'
            % (" done" if shipped else "", head,
               '<ul class="epic-subs">%s</ul>' % subs if subs else ""))


def epic_block(n):
    """The epics attached to a card, and their children, at the top of the
    Details tab.

    They sit above the facts because they are the one thing on the note whose
    truth lives somewhere else: everything below is what we decided, this is
    what the tracker currently says. A card accumulates epics over its life, so
    this is a list; a timeline card with none says so out loud, since an empty
    list is the reason its bar is hatched and a reader will come here to find
    out why."""
    if not n.get("epics"):
        if not n.get("start"):
            return ""
        return ('<div class="epic-box none"><p class="epic-hd">'
                '<span class="lbl">Epic</span>'
                '<span class="est">none filed yet</span></p></div>')
    return "".join(_one_epic(num, info)
                   for num, info in zip(n["epics"], n["epic_infos"]))


def main():
    if len(sys.argv) < 2:
        die("usage: build_flow.py <flow-dir>")
    flow_dir = sys.argv[1]
    cfg, notes, drawn, edges, layers, svg, map_bars, map_key = build(flow_dir)

    tally = [("%d" % len(drawn), cfg.get("nodeWord", "notes")),
             ("%d" % len(edges), "dependencies"),
             ("%d" % len(layers), "layers")]
    tally += [(str(t.get("value")), t.get("label", "")) for t in cfg.get("tally", [])]
    tally_html = "".join("<li><b>%s</b> %s</li>" % (esc(v), esc(l)) for v, l in tally)

    number_items(notes)
    # Questions and risks join the search index as first-class entries. A reader
    # searching "username" wants the open question about it, not only the note
    # that happens to mention it — and each hit carries its Q-/R- handle so it
    # can be quoted straight into another thread.
    index = [{"id": n["id"], "t": n["title"], "s": n["summary"],
              "x": re.sub(r"\s+", " ", n["text"])[:4000]} for n in notes]
    for n in notes:
        for q in n["questions"]:
            index.append({"id": n["id"], "k": "q",
                          "t": "%s · %s" % (q["ref"], n["node"]), "s": q["text"], "x": ""})
        for r in n["risks"]:
            index.append({"id": n["id"], "k": "r",
                          "t": "%s · %s" % (r["ref"], n["node"]), "s": r["text"], "x": ""})
    search = json.dumps(index, ensure_ascii=False)

    questions_html, open_q = render_questions(cfg, notes)
    risks_html, unmit = render_risks(cfg, notes)
    gantt_html = render_gantt(cfg, drawn, set(cfg.get("spine", [])))
    # Schedule sits second, directly after the map. "What blocks what" and "when"
    # are read together — a reader who has just seen the graph wants the dates
    # next, not the open questions. Questions and risks are the detail behind
    # both and follow them.
    panels = [
        ("roadmap", cfg.get("roadmapTab", "Roadmap"), True, 0),
        ("schedule", ((cfg.get("timeline") or {}).get("tab", "Schedule")), bool(gantt_html), 0),
        ("questions", (cfg.get("questions") or {}).get("tab", "Open questions"),
         bool(questions_html), open_q),
        ("risks", (cfg.get("risks") or {}).get("tab", "Risks"), bool(risks_html), unmit),
    ]
    tabnav = render_tabnav(panels)

    out = flowio.read_text(SHELL)
    for key, val in {
        "TITLE": esc(cfg.get("title", "Flow map")),
        "KICKER": esc(cfg.get("kicker", "")) + synced_stamp(cfg.get("_epicsGenerated")),
        "LEDE": esc(cfg.get("lede", "")),
        "TALLY": tally_html,
        "SVG": svg,
        "MAPCONTROLS": map_bars,
        "MAPLEGEND": map_key,
        "TABNAV": tabnav,
        "QUICKVIEW": render_quick(notes, open_q, unmit),
        "QUESTIONS": questions_html,
        "RISKS": risks_html,
        "NOTES": "\n".join(note_article(n) for n in notes),
        "SEARCH": search,
        "GANTT": gantt_html,
        "FONTS": ('<link rel="preconnect" href="https://fonts.googleapis.com">\n'
                  '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
                  '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?'
                  'family=Archivo:wght@500;600;700&family=IBM+Plex+Mono:wght@400;500;600'
                  '&family=Source+Serif+4:opsz,wght@8..60,400;8..60,600&display=swap">')
                 if cfg.get("webfonts") else "",
        # The footer is where provenance already lives, and the sync date is
        # provenance: it is the difference between "no epic yet" and "nobody
        # has asked GitHub since March".
        "FOOTER": esc(" ".join(x for x in [
            cfg.get("footer", ""),
            ("Epic state synced from GitHub on %s; re-run sync_epics.py to refresh."
             % cfg["_epicsGenerated"]) if cfg.get("_epicsGenerated") else "",
        ] if x)),
    }.items():
        out = out.replace("{{%s}}" % key, val)

    dest = os.path.join(flow_dir, cfg.get("out", "flow.html"))
    flowio.write_text(dest, out)
    print("%s | %d notes (%d drawn) | %d edges | %d layers | %d open q | %d unmitigated | %d KB"
          % (os.path.relpath(dest), len(notes), len(drawn), len(edges),
             len(layers), open_q, unmit, len(out) // 1024))


if __name__ == "__main__":
    main()
