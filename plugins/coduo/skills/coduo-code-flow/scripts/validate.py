#!/usr/bin/env python3
"""Check a flow-map JSON model before rendering.

Usage: validate.py <model.json>

Errors (exit 1) are things that break the rendered page: dangling ids,
duplicates, missing positions. Warnings are things that make the page
misleading but still render: overlapping cards, flows whose edges do not
cover their own steps, orphan nodes.
"""
import json
import pathlib
import sys

NODE_W, NODE_H = 184, 58
GUTTER = 8

errors: list[str] = []
warnings: list[str] = []


def require_unique(items, kind):
    seen, ids = set(), []
    for item in items:
        item_id = item.get("id")
        if item_id is None:
            errors.append(f"{kind}: entry without an id")
            continue
        if item_id in seen:
            errors.append(f"{kind}: duplicate id {item_id!r}")
        seen.add(item_id)
        ids.append(item_id)
    return set(ids)


def main(argv):
    if len(argv) != 2:
        sys.exit(__doc__)

    model = json.loads(pathlib.Path(argv[1]).read_text())

    for key in ("repository", "description", "nodes", "edges", "flows"):
        if key not in model:
            errors.append(f"top level: missing {key!r}")
    if errors:
        report()

    nodes = model["nodes"]
    edges = model["edges"]
    flows = model["flows"]

    node_ids = require_unique(nodes, "nodes")
    edge_ids = require_unique(edges, "edges")
    require_unique(flows, "flows")

    for node in nodes:
        for key in ("label", "layer", "description"):
            if not node.get(key):
                errors.append(f"node {node.get('id')!r}: missing {key!r}")
        position = node.get("position") or {}
        if "x" not in position or "y" not in position:
            errors.append(f"node {node.get('id')!r}: missing position.x/position.y")

    for edge in edges:
        for end in ("source", "target"):
            if edge.get(end) not in node_ids:
                errors.append(f"edge {edge.get('id')!r}: {end} {edge.get(end)!r} is not a node")
        if not edge.get("relation"):
            errors.append(f"edge {edge.get('id')!r}: missing 'relation' verb")

    edge_by_id = {edge.get("id"): edge for edge in edges}
    used_edges: set[str] = set()

    for flow in flows:
        flow_id = flow.get("id")
        if flow.get("category") not in ("user", "system"):
            errors.append(f"flow {flow_id!r}: category must be 'user' or 'system'")
        for key in ("label", "summary"):
            if not flow.get(key):
                errors.append(f"flow {flow_id!r}: missing {key!r}")

        steps = flow.get("steps") or []
        if len(steps) < 2:
            errors.append(f"flow {flow_id!r}: needs at least two steps")
        for step in steps:
            if step not in node_ids:
                errors.append(f"flow {flow_id!r}: step {step!r} is not a node")

        touched: set[str] = set()
        for edge_id in flow.get("edgeIds") or []:
            if edge_id not in edge_ids:
                errors.append(f"flow {flow_id!r}: edgeId {edge_id!r} is not an edge")
                continue
            used_edges.add(edge_id)
            edge = edge_by_id[edge_id]
            touched.update((edge["source"], edge["target"]))
        uncovered = [step for step in steps if step in node_ids and step not in touched]
        if uncovered:
            warnings.append(
                f"flow {flow_id!r}: steps not covered by its edgeIds: {', '.join(uncovered)}"
            )

        qa = flow.get("qa") or {}
        manual_ids = set()
        for check in qa.get("manual") or []:
            if not check.get("id"):
                errors.append(f"flow {flow_id!r}: manual check without an id")
            elif check["id"] in manual_ids:
                errors.append(f"flow {flow_id!r}: duplicate manual check id {check['id']!r}")
            else:
                manual_ids.add(check["id"])
            if not check.get("expected"):
                errors.append(
                    f"flow {flow_id!r}: manual check {check.get('id')!r} has no 'expected' result"
                )
        for check in qa.get("automated") or []:
            if not check.get("command"):
                errors.append(f"flow {flow_id!r}: automated check without a 'command'")
        if flow.get("category") == "user" and not (qa.get("manual") or []):
            warnings.append(f"flow {flow_id!r}: user flow with no manual QA checks")

    connected = {end for edge in edges for end in (edge.get("source"), edge.get("target"))}
    for node_id in sorted(node_ids - connected):
        warnings.append(f"node {node_id!r}: no edges touch it")
    for edge_id in sorted(edge_ids - used_edges):
        warnings.append(f"edge {edge_id!r}: not used by any flow")

    boxes = [
        (node["id"], node["position"]["x"], node["position"]["y"])
        for node in nodes
        if isinstance(node.get("position"), dict)
        and "x" in node["position"]
        and "y" in node["position"]
    ]
    for index, (a_id, ax, ay) in enumerate(boxes):
        for b_id, bx, by in boxes[index + 1 :]:
            if abs(ax - bx) < NODE_W + GUTTER and abs(ay - by) < NODE_H + GUTTER:
                warnings.append(f"cards overlap: {a_id!r} and {b_id!r}")

    layout = model.get("layout") or {}
    width, height = layout.get("width", 1480), layout.get("height", 980)
    for node_id, x, y in boxes:
        if x < 0 or y < 0 or x + NODE_W > width or y + NODE_H > height:
            warnings.append(f"node {node_id!r}: sits outside the {width}x{height} canvas")

    report(len(nodes), len(edges), len(flows))


def report(node_count=0, edge_count=0, flow_count=0):
    for warning in warnings:
        print(f"warn  {warning}")
    for error in errors:
        print(f"ERROR {error}")
    if errors:
        sys.exit(f"\n{len(errors)} error(s); fix the JSON before rendering.")
    print(f"\nok: {node_count} nodes, {edge_count} edges, {flow_count} flows, {len(warnings)} warning(s)")


if __name__ == "__main__":
    main(sys.argv)
