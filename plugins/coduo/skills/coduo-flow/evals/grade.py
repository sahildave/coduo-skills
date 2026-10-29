#!/usr/bin/env python3
"""Grade coduo-flow eval runs against the assertions in evals.json.

Assertions 0-6 are mechanical and decided here. Assertion 7 -- do the
standfirsts state a conclusion a reader could repeat? -- needs human
judgement and is always recorded unmet, so a clean mechanical sweep
reads 7/8, not 8/8.

Expected layout, as produced by skill-creator's eval loop:

    <iteration-dir>/eval-*/eval_metadata.json
    <iteration-dir>/eval-*/{with_skill,without_skill}/outputs/

Writes grading.json beside each run's outputs/ and prints a summary.

Usage:  python3 evals/grade.py <iteration-dir>
"""
import glob
import json
import os
import re
import subprocess
import sys

SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(SKILL, "scripts"))
import flowio        # noqa: E402  (needs the path above)
import frontmatter   # noqa: E402


def load_notes(md_paths):
    """Parse every note that has frontmatter. Returns {id: fm}, [unparsed]."""
    notes, broken = {}, []
    for path in md_paths:
        try:
            fm, _ = frontmatter.split(flowio.read_text(path))
        except Exception as exc:
            broken.append((os.path.basename(path), str(exc)))
            continue
        if fm.get("id"):
            notes[fm["id"]] = fm
        else:
            broken.append((os.path.basename(path), "no id in frontmatter"))
    return notes, broken


def grade(run_dir, assertions):
    out = os.path.join(run_dir, "outputs")
    mds = [f for f in glob.glob(out + "/**/*.md", recursive=True)
           if os.path.basename(f).lower() != "readme.md"]
    htmls = glob.glob(out + "/**/*.html", recursive=True)
    cfgs = glob.glob(out + "/**/flow.json", recursive=True)
    notes, broken = load_notes(mds)

    cfg, cfg_err = None, "no flow.json"
    if cfgs:
        try:
            cfg = json.loads(flowio.read_text(cfgs[0]))
        except Exception as exc:
            cfg_err = f"flow.json invalid: {exc}"
    kinds = (cfg or {}).get("kinds") or {}
    # A kind whose tone is "none" is deliberately off-graph -- that is how the
    # skill carries a reference note the map should not draw. Judging those on
    # connectivity would punish the documented pattern.
    undrawn = {k for k, v in kinds.items()
               if isinstance(v, dict) and v.get("tone") == "none"}

    results = []

    def add(i, passed, evidence):
        results.append({"text": assertions[i], "passed": bool(passed),
                        "evidence": evidence})

    # 0 -- connected graph. Counting notes alone does not discriminate: a
    # baseline run may split into many files by instinct. Wiring them does.
    referenced = set()
    for nid, fm in notes.items():
        for key in ("depends_on", "unlocks"):
            for other in (fm.get(key) or []):
                referenced.add(nid)
                referenced.add(other)
    drawn = {nid for nid, fm in notes.items() if fm.get("kind") not in undrawn}
    isolated = sorted(drawn - referenced)
    add(0, len(notes) >= 4 and not isolated,
        f"{len(notes)} notes ({len(drawn)} drawn), "
        f"{len(referenced & drawn)} wired"
        + (f", isolated: {isolated[:5]}" if isolated else ", none isolated"))

    # 1 -- required frontmatter keys on every note.
    required = ["id", "title", "node", "kind", "status", "summary"]
    missing = {nid: [k for k in required if not fm.get(k)]
               for nid, fm in notes.items()}
    missing = {nid: keys for nid, keys in missing.items() if keys}
    add(1, notes and not missing and not broken,
        f"{len(notes)}/{len(mds)} notes carry all of {required}"
        + (f"; missing: {dict(list(missing.items())[:3])}" if missing else "")
        + (f"; unparsed: {broken[:3]}" if broken else ""))

    # 2 -- depends_on and unlocks are exact inverses, no dangling ids.
    errs = []
    for nid, fm in notes.items():
        for dep in (fm.get("depends_on") or []):
            if dep not in notes:
                errs.append(f"{nid} -> missing {dep}")
            elif nid not in (notes[dep].get("unlocks") or []):
                errs.append(f"{dep}.unlocks is missing {nid}")
    add(2, notes and not errs,
        "graph symmetric" if not errs else f"{len(errs)} problems: {errs[:4]}")

    # 3 -- a flow.json declaring a title.
    ok = bool(cfg and cfg.get("title"))
    evidence = (f"flow.json title={cfg.get('title', '')[:40]!r} "
                f"kinds={list(kinds)[:6]}") if cfg else cfg_err
    add(3, ok, evidence)

    # 4 -- self-contained: no external script/style/img references.
    external = []
    for h in htmls:
        external += re.findall(r'(?:src|href)="https?://[^"]+"',
                               flowio.read_text(h))
    add(4, bool(htmls) and not external,
        f"{len(htmls)} html file(s)"
        + (f", {len(external)} external refs: {external[:3]}" if external
           else ", no external refs"))

    # 5 -- every note's content embedded, so a click needs no network.
    embedded = 0
    if htmls and notes:
        blob = flowio.read_text(htmls[0])
        embedded = sum(1 for nid in notes
                       if f'note-{nid}"' in blob or f'"{nid}"' in blob)
    add(5, notes and embedded == len(notes),
        f"{embedded}/{len(notes)} note ids present in the html")

    # 6 -- the skill's own consistency gate passes.
    code, msg = 1, "no note folder to check"
    folders = sorted({os.path.dirname(m) for m in mds})
    if folders:
        proc = subprocess.run(
            [sys.executable, os.path.join(SKILL, "scripts", "check_flow.py"),
             folders[0]],
            capture_output=True, text=True)
        lines = (proc.stdout + proc.stderr).strip().splitlines()
        code, msg = proc.returncode, (lines[-1] if lines else "")
    add(6, code == 0, f"check_flow.py exit={code}: {msg[:120]}")

    # 7 -- reserved for the human reviewer.
    add(7, False, "human review: do the standfirsts state a conclusion?")
    return results


def main(root):
    for eval_dir in sorted(glob.glob(os.path.join(root, "eval-*"))):
        meta_path = os.path.join(eval_dir, "eval_metadata.json")
        if not os.path.exists(meta_path):
            print(f"{os.path.basename(eval_dir)}: no eval_metadata.json, skipped")
            continue
        assertions = json.loads(flowio.read_text(meta_path))["assertions"]
        for run in ("with_skill", "without_skill", "old_skill"):
            run_dir = os.path.join(eval_dir, run)
            if not os.path.isdir(run_dir):
                continue
            results = grade(run_dir, assertions)
            passed = sum(1 for r in results if r["passed"])
            doc = {
                "expectations": results,
                "summary": {"passed": passed, "failed": len(results) - passed,
                            "total": len(results),
                            "pass_rate": round(passed / len(results), 4)},
            }
            with open(os.path.join(run_dir, "grading.json"), "w",
                      encoding="utf-8") as fh:
                json.dump(doc, fh, indent=2)
            print(f"{os.path.basename(eval_dir):34} {run:15} "
                  f"{passed}/{len(results)}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
