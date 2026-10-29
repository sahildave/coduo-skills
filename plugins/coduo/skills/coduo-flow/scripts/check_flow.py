#!/usr/bin/env python3
"""Gate a flow folder before building it.

    python3 scripts/check_flow.py <flow-dir>

The graph lives in the notes' frontmatter, where a mistake is invisible: a
dangling id, a one-way edge, or a wrong `kind` shows up only as a missing arrow
or a wrongly-coloured card. This names each one and exits non-zero.

Stdlib only, like the builder.
"""

import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import flowio
from build_flow import DEFAULT_KINDS, RISK_TOKENS, TONES, parse_question, set_categories

STATUSES = ["open", "proposed", "validated", "decided"]
EXECUTORS = ("unattended", "human", "mixed")
REQUIRED = ["id", "title", "node", "kind", "status", "summary", "updated"]
NODE_MAX = 24

problems, warnings = [], []


def fail(m):
    problems.append(m)


def warn(m):
    warnings.append(m)


def _timing(name, fm, cfg):
    """`start`/`length` place a note on the timeline. A bar running past the
    end of the timeline is silently clipped when drawn, so catch it here."""
    tl = cfg.get("timeline") or {}
    start, length = fm.get("start"), fm.get("length")
    if start is None and length is None:
        return
    if not tl:
        fail("%s: has start/length but flow.json declares no `timeline`" % name)
        return
    try:
        units = int(tl.get("units"))
    except (TypeError, ValueError):
        fail("flow.json timeline needs an integer `units`")
        return
    if length is not None and start is None:
        fail("%s: `length` needs a `start` to place it on the timeline" % name)
        return
    try:
        start_i, length_i = int(start), int(length or 1)
    except (TypeError, ValueError):
        fail("%s: start/length must be whole numbers" % name)
        return
    if start_i < 1 or start_i + length_i - 1 > units:
        fail("%s: runs %d-%d, past the end of a %d-unit timeline"
             % (name, start_i, start_i + length_i - 1, units))


def _open_items(name, fm):
    """`risks` and `questions` are block lists of one line each. A scalar there
    is the mistake that costs a whole section silently, so it is an error."""
    for key in ("risks", "questions"):
        val = fm.get(key)
        if val is None:
            continue
        if not isinstance(val, list):
            fail("%s: `%s` must be a list, one line per entry" % (name, key))
            continue
        for raw in val:
            if not str(raw).strip():
                fail("%s: an empty entry in `%s`" % (name, key))
            elif key == "risks":
                head = str(raw).split(":", 1)[0].strip().lower()
                if not all(t.strip() in RISK_TOKENS
                           for t in head.replace("/", ",").split(",") if t.strip()):
                    warn('%s: risk "%s…" names no severity, so it reads as medium and '
                         "unmitigated" % (name, str(raw).strip()[:44]))
            elif "?" not in parse_question(raw)["text"]:
                warn('%s: open question "%s…" is not phrased as a question'
                     % (name, parse_question(raw)["text"][:44]))


def _words(text):
    return set(re.findall(r"[a-z]{4,}", text.lower()))


def _duplicate_items(notes):
    """Two notes asking the same question is worse than either asking it alone:
    it is answered in neither, and it double-counts on the quick view."""
    seen = []
    for n in notes.values():
        for raw in n.get("items", []):
            # Drop the prefix (severity, categories, `answered`) before comparing:
            # two questions differing only in who owns them are still one question.
            text = raw.split(":", 1)[-1].strip() if ":" in raw[:48] else raw
            words = _words(text)
            if len(words) < 5:
                continue
            for other_file, other_words in seen:
                if other_file == n["file"]:
                    continue
                overlap = len(words & other_words) / max(len(words | other_words), 1)
                if overlap >= 0.6:
                    warn('%s and %s ask nearly the same thing — "%s"'
                         % (n["file"], other_file, text[:56]))
                    break
            seen.append((n["file"], words))


def note_epics(name, fm):
    """The epic numbers a note names, as strings, the way the builder reads
    them: `epics:` (list) is canonical, `epic:` (scalar) is a legacy alias, and
    both at once is ambiguous. Returns (list_of_str, error_or_None)."""
    plural, singular = fm.get("epics"), fm.get("epic")
    if plural not in (None, "") and singular not in (None, ""):
        return [], "%s: has both `epic:` and `epics:` — use `epics:` alone" % name
    raw = plural if plural not in (None, "") else singular
    if raw in (None, ""):
        return [], None
    items = raw if isinstance(raw, (list, tuple)) else [raw]
    out = []
    for item in items:
        tok = str(item).strip().lstrip("#")
        if not tok.isdigit():
            return [], '%s: epic "%s" is not an issue number' % (name, item)
        if tok not in out:
            out.append(tok)
    return out, None


def main(flow_dir):
    cfg_path = os.path.join(flow_dir, "flow.json")
    cfg = {}
    if os.path.exists(cfg_path):
        try:
            cfg = flowio.read_json(cfg_path)
        except ValueError as e:
            fail("flow.json is not valid JSON: %s" % e)
    else:
        warn("no flow.json - falling back to defaults for title, lanes and kinds")
    # The builder honors flow.json's `categories` override; checking against the
    # defaults instead makes every correctly-prefixed risk warn "names no
    # severity". Same mutable sets, so this must run before any note is checked.
    set_categories(cfg)
    kinds = dict(DEFAULT_KINDS)
    kinds.update(cfg.get("kinds", {}))
    index = cfg.get("index", "README.md")

    # This gates the build, so a tone the builder cannot draw has to fail here
    # rather than as a KeyError three steps later.
    for kind, spec in sorted(kinds.items()):
        tone = (spec or {}).get("tone")
        if tone != "none" and tone not in TONES:
            fail('flow.json kind "%s" has tone "%s"; the palette is %s or "none"'
                 % (kind, tone, ", ".join('"%s"' % t for t in sorted(TONES))))

    # epics.json is optional: a flow whose work is not on a tracker never runs
    # sync_epics.py and is not broken for it.
    epics_path = os.path.join(flow_dir, "epics.json")
    epics, epics_used, no_epic = {}, set(), []
    done_statuses = set(cfg.get("doneStatuses") or ["validated"])
    if os.path.exists(epics_path):
        try:
            epics = flowio.read_json(epics_path).get("epics") or {}
        except ValueError as e:
            fail("epics.json is not valid JSON: %s" % e)

    notes = {}
    for name in flowio.note_files(flow_dir, index):
        try:
            fm, body = flowio.read_note(flow_dir, name)
        except UnicodeDecodeError as e:
            fail("%s: not valid UTF-8 (%s)" % (name, e))
            continue
        except ValueError:
            fail("%s: no frontmatter block" % name)
            continue
        for key in REQUIRED:
            if not fm.get(key):
                fail("%s: missing `%s`" % (name, key))
        if fm.get("kind") and fm["kind"] not in kinds:
            fail('%s: kind "%s" is not in flow.json kinds (%s)'
                 % (name, fm["kind"], ", ".join(sorted(kinds))))
        # "Dim what is built" keys on `done`, and a danger-toned kind - `gap`,
        # `blocker` - is a card that says *not* built. A note that is both dims
        # itself out of the map while its colour insists it is missing, and the
        # reader is left with two contradictory claims on one card. It is a
        # data problem every time: the kind was never updated when the work
        # settled. Nothing else in the toolchain can see it.
        note_eps, ep_err = note_epics(name, fm)
        if ep_err:
            fail(ep_err)
        # "Dim what is built" keys on `done`, and a danger-toned kind - `gap`,
        # `blocker` - is a card that says *not* built. A card that is both dims
        # itself out of the map while its colour insists it is missing, leaving
        # the reader two contradictory claims. Always a data problem: the kind
        # was never updated when the work settled. Nothing else can see it.
        tone = (kinds.get(fm.get("kind")) or {}).get("tone")
        shipped = any(
            (epics.get(e) or {}).get("state") == "closed"
            and ((epics.get(e) or {}).get("stateReason") or "") != "not_planned"
            for e in note_eps)
        if tone == "danger" and (fm.get("status") in done_statuses or shipped):
            warn('%s: kind "%s" says not built, and %s says it is built - so it '
                 "dims under 'Dim what is built' while still drawn red. "
                 "Update the kind."
                 % (name, fm.get("kind"),
                    "a closed epic" if shipped else 'its status "%s"' % fm.get("status")))
        for e in note_eps:
            if e not in epics:
                # Not an error: an epic can be named before the sync runs. But
                # the bar draws plain until then, so say why.
                warn("%s: epic #%s is not in epics.json - run sync_epics.py"
                     % (name, e))
            else:
                epics_used.add(e)
        if not note_eps and fm.get("start"):
            # Collected, not warned per file: on a live plan most of the
            # timeline has no epic yet, and one line per note is how a checker
            # teaches people to stop reading it.
            no_epic.append(name)
        if fm.get("executor") and fm["executor"] not in EXECUTORS:
            fail('%s: executor "%s" not in %s'
                 % (name, fm["executor"], "|".join(EXECUTORS)))
        if fm.get("status") and fm["status"] not in STATUSES:
            fail('%s: status "%s" not in %s' % (name, fm["status"], "|".join(STATUSES)))
        if fm.get("node") and len(fm["node"]) > NODE_MAX:
            fail('%s: node "%s" is %d chars; the card fits %d'
                 % (name, fm["node"], len(fm["node"]), NODE_MAX))
        if fm.get("summary") and len(fm["summary"]) > 300:
            warn("%s: summary is %d chars - the standfirst reads best under ~200"
                 % (name, len(fm["summary"])))
        if fm.get("summary") and not re.search(r"[.!?]$", fm["summary"].strip()):
            warn("%s: summary does not end in a full stop - it should be a sentence" % name)
        _open_items(name, fm)
        if not re.search(r"^#\s", body.lstrip(), re.M):
            warn("%s: body has no `# ` heading" % name)
        nid = fm.get("id")
        if nid in notes:
            fail('duplicate id "%s" in %s and %s' % (nid, name, notes[nid]["file"]))
        if nid:
            _timing(name, fm, cfg)
            notes[nid] = {"file": name, "dep": fm.get("depends_on", []) or [],
                          "unl": fm.get("unlocks", []) or [],
                          "loops": fm.get("loops_to", []) or [],
                          "kind": fm.get("kind"), "tone": kinds.get(fm.get("kind"), {}).get("tone"),
                          "items": [str(x) for x in (fm.get("questions") or [])]
                                   + [str(x) for x in (fm.get("risks") or [])]}

    if not notes:
        fail("no notes found in %s" % flow_dir)
        return report()

    # depends_on and unlocks must be exact inverses, with nothing dangling
    for nid, n in notes.items():
        for d in n["dep"]:
            if d not in notes:
                fail('%s: depends_on "%s" does not exist' % (n["file"], d))
            elif nid not in notes[d]["unl"]:
                fail('%s: unlocks is missing "%s"' % (notes[d]["file"], nid))
        for u in n["unl"]:
            if u not in notes:
                fail('%s: unlocks "%s" does not exist' % (n["file"], u))
            elif nid not in notes[u]["dep"]:
                fail('%s: depends_on is missing "%s"' % (notes[u]["file"], nid))

    # loops_to names a return path. It is drawn but never layered, so it is
    # checked for existence only — a loop is not a cycle error.
    for nid, n in notes.items():
        for t in n["loops"]:
            if t not in notes:
                fail('%s: loops_to "%s" does not exist' % (n["file"], t))
            elif notes[t]["tone"] == "none":
                fail('%s: loops_to "%s", which is never drawn' % (n["file"], t))

    drawn = {i: n for i, n in notes.items() if n["tone"] != "none"}
    for nid, n in drawn.items():
        for d in n["dep"]:
            if d in notes and notes[d]["tone"] == "none":
                fail('%s: depends_on "%s", which is kind %s and is never drawn'
                     % (n["file"], d, notes[d]["kind"]))

    # cycles — the builder cannot lay these out
    indeg = {i: len([d for d in n["dep"] if d in drawn]) for i, n in drawn.items()}
    adj = {i: [] for i in drawn}
    for i, n in drawn.items():
        for d in n["dep"]:
            if d in adj:
                adj[d].append(i)
    ready = [i for i, v in indeg.items() if v == 0]
    settled = 0
    while ready:
        i = ready.pop(0)
        settled += 1
        for nxt in adj[i]:
            indeg[nxt] -= 1
            if indeg[nxt] == 0:
                ready.append(nxt)
    if settled != len(drawn):
        fail("dependency cycle involving: %s"
             % ", ".join(i for i in drawn if indeg[i] > 0))

    spine = cfg.get("spine", [])
    for a, b in zip(spine, spine[1:]):
        if a not in notes or b not in notes:
            fail('spine names "%s" -> "%s"; one of them is not a note' % (a, b))
        elif a not in notes[b]["dep"]:
            fail('spine names "%s" -> "%s", which is not a dependency edge' % (a, b))

    for nid, n in drawn.items():
        if not n["dep"] and not n["unl"]:
            warn("%s is an island - nothing depends on it and it depends on nothing"
                 % n["file"])

    lint_vocabulary(kinds, {n["kind"] for n in notes.values() if n.get("kind")})

    _duplicate_items(notes)

    if no_epic:
        warn("%d note%s on the timeline name no epic and draw hatched: %s"
             % (len(no_epic), "" if len(no_epic) == 1 else "s", ", ".join(no_epic)))
    for stale in sorted(set(epics) - epics_used, key=lambda x: int(x)):
        warn("epics.json carries #%s but no note names it - the sync is ahead "
             "of the notes, or the note lost its `epic:`" % stale)

    lanes = cfg.get("lanes")
    if lanes:
        depth = longest_path(drawn)
        if len(lanes) < depth:
            warn("flow.json names %d lanes but the graph is %d layers deep; "
                 "the last %d will be unlabelled" % (len(lanes), depth, depth - len(lanes)))

    return report(len(notes), len(drawn))


#: Words that describe where work has got to rather than what it is. A kind
#: built from one of these is a status in disguise; see references/presets.md.
LIFECYCLE_WORDS = {
    "done", "shipped", "built", "unbuilt", "complete", "completed", "gap",
    "todo", "missing", "pending", "wip", "started", "finished", "delivered",
}


#: Words that describe where work has got to rather than what it is. A kind
#: built from one of these is a status in disguise; see references/presets.md.
LIFECYCLE_WORDS = {
    "done", "shipped", "built", "unbuilt", "complete", "completed", "gap",
    "todo", "missing", "pending", "wip", "started", "finished", "delivered",
}


def lint_vocabulary(kinds, used):
    """The two vocabulary mistakes that only show up on screen, weeks later.

    Only over kinds a note actually carries: `kinds` is the defaults merged
    with the flow's own, and an unused default draws no card and appears in no
    legend, so linting it reports a clash that cannot happen."""
    seen = {}
    for kind in sorted(used):
        spec = kinds.get(kind) or {}
        label = spec.get("label", kind)
        # A kind is a noun. Anything that stops being true once the work lands
        # is lifecycle, and lifecycle already has three axes of its own -
        # `status`, `epic`, and the dim-what-is-built switch. Put it in `kind`
        # and the card ends up contradicting the tick beside it.
        if LIFECYCLE_WORDS & (set(kind.lower().split("-"))
                              | set(label.lower().split())):
            warn('flow.json kind "%s" (%s) names a lifecycle state, not a '
                 "thing. Use `status` and `epic:` for that - a card whose kind "
                 "says built or unbuilt will eventually contradict its own "
                 "tick. See references/presets.md." % (kind, label))
        # The legend is a colour key. Two swatches of one colour with different
        # labels stops it keying anything, and reads as a rendering fault.
        tone = spec.get("tone")
        if not tone or tone == "none":
            continue
        if tone in seen:
            warn('flow.json kinds "%s" and "%s" both use tone "%s"; the legend '
                 "will show two identical swatches with different labels."
                 % (seen[tone], kind, tone))
        else:
            seen[tone] = kind


def longest_path(drawn):
    layer = {i: 0 for i in drawn}
    for _ in range(len(drawn)):
        for i, n in drawn.items():
            for d in n["dep"]:
                if d in layer:
                    layer[i] = max(layer[i], layer[d] + 1)
    return max(layer.values()) + 1 if layer else 0


def report(total=0, drawn=0):
    for w in warnings:
        sys.stderr.write("  ! %s\n" % w)
    if problems:
        for p in problems:
            sys.stderr.write("  x %s\n" % p)
        sys.stderr.write("\n%d problem%s\n" % (len(problems), "" if len(problems) == 1 else "s"))
        return 1
    print("ok - %d notes (%d drawn), frontmatter consistent%s"
          % (total, drawn, ", %d warning(s)" % len(warnings) if warnings else ""))
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.stderr.write("usage: check_flow.py <flow-dir>\n")
        sys.exit(2)
    sys.exit(main(sys.argv[1]))
