#!/usr/bin/env python3
"""Join the notes to the tracker, once, into a file the build can read offline.

`build_flow.py` is stdlib-only and never touches the network — that is what
makes a rebuild deterministic and a diff readable. So the one fact it cannot
derive from the notes, whether a note's epic exists on GitHub and whether it is
closed, is fetched here and written beside them as `epics.json`.

Run it after `coduo-epic` or `coduo-tickets` has changed the tracker, then
rebuild. A note with no `epic:` is not an error: it is an epic nobody has
written yet, and the map draws it hatched to say so.

    python3 sync_epics.py <flow-dir> [--repo owner/name]
"""
import datetime
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import flowio  # noqa: E402


def die(msg):
    sys.stderr.write("sync_epics: %s\n" % msg)
    sys.exit(1)


def gh(args):
    """One `gh` call. A non-zero exit is fatal except where the caller says
    otherwise — a silent empty result would render as "this epic has no
    children", which is a different and wrong claim."""
    try:
        out = subprocess.run(["gh"] + args, capture_output=True, text=True)
    except FileNotFoundError:
        die("the `gh` CLI is not installed; it is how epic state is read")
    if out.returncode != 0:
        return None, (out.stderr or "").strip()
    return json.loads(out.stdout or "null"), None


def epic_numbers(flow_dir, index):
    """Every distinct epic across the notes, in note order.

    `epics:` (list) is canonical; `epic:` (scalar) is a legacy alias. A card
    accumulates epics over its life, so a note may name several."""
    seen = []
    for name in flowio.note_files(flow_dir, index):
        try:
            fm, _ = flowio.read_note(flow_dir, name)
        except (ValueError, UnicodeDecodeError):
            continue
        plural, singular = fm.get("epics"), fm.get("epic")
        if plural not in (None, "") and singular not in (None, ""):
            die("%s: has both `epic:` and `epics:` — use `epics:` alone" % name)
        raw = plural if plural not in (None, "") else singular
        if raw in (None, ""):
            continue
        for item in (raw if isinstance(raw, (list, tuple)) else [raw]):
            try:
                n = int(str(item).strip().lstrip("#"))
            except ValueError:
                die('%s: epic "%s" is not an issue number' % (name, item))
            if n not in seen:
                seen.append(n)
    return seen


def main():
    args = [a for a in sys.argv[1:]]
    repo = None
    if "--repo" in args:
        i = args.index("--repo")
        repo = args[i + 1]
        del args[i:i + 2]
    if not args:
        die("usage: sync_epics.py <flow-dir> [--repo owner/name]")
    flow_dir = args[0]
    if not os.path.isdir(flow_dir):
        die("%s is not a directory" % flow_dir)

    cfg_path = os.path.join(flow_dir, "flow.json")
    cfg = flowio.read_json(cfg_path) if os.path.exists(cfg_path) else {}
    if not repo:
        got, err = gh(["repo", "view", "--json", "nameWithOwner"])
        if not got:
            die("could not resolve the repo (%s); pass --repo owner/name" % err)
        repo = got["nameWithOwner"]

    # Stamped, and rendered in the page footer. A stale snapshot is this
    # design's worst failure mode precisely because it is invisible: a rebuild
    # reproduces yesterday's tracker exactly, and looks deliberate doing it.
    # A datetime, not a date: the page says how long ago in words, and "today"
    # is not an answer to "is this stale". Local time with its offset, so it
    # renders in the reader's own clock rather than in UTC.
    stamp = datetime.datetime.now().astimezone().replace(microsecond=0).isoformat()
    out = {"generated": stamp, "repo": repo, "epics": {}}
    numbers = epic_numbers(flow_dir, cfg.get("index", "README.md"))
    for n in numbers:
        issue, err = gh(["issue", "view", str(n), "--repo", repo,
                         "--json", "number,title,state,stateReason,url"])
        if not issue:
            die("#%d: %s" % (n, err or "not found"))
        # Sub-issues are a newer GitHub feature and the endpoint 404s on a repo
        # that has never used it. That is an epic with no children, not a
        # failure, so it degrades to an empty list rather than stopping.
        subs, _ = gh(["api", "repos/%s/issues/%d/sub_issues" % (repo, n)])
        out["epics"][str(n)] = {
            "number": issue["number"],
            "title": issue["title"],
            "state": issue["state"].lower(),
            # An epic closed as *not planned* has the same `state` as one that
            # shipped. Without this the map paints abandoned work green.
            "stateReason": (issue.get("stateReason") or "").lower(),
            "url": issue["url"],
            "subIssues": [
                {"number": s["number"], "title": s["title"],
                 "state": s["state"].lower(),
                 "url": s.get("html_url", "")}
                for s in (subs or [])
            ],
        }

    path = os.path.join(flow_dir, "epics.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
        f.write("\n")
    vals = out["epics"].values()
    shipped = sum(1 for e in vals
                  if e["state"] == "closed" and e["stateReason"] != "not_planned")
    dropped = sum(1 for e in vals if e["stateReason"] == "not_planned")
    print("epics.json: %d epic%s, %d shipped, %d closed as not planned, %d sub-issues"
          % (len(out["epics"]), "" if len(out["epics"]) == 1 else "s", shipped,
             dropped, sum(len(e["subIssues"]) for e in vals)))


if __name__ == "__main__":
    main()
