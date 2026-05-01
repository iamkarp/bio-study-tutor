#!/usr/bin/env python3
"""Validate KG against schemas + referential integrity."""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

try:
    from jsonschema import Draft202012Validator
    HAVE_JSONSCHEMA = True
except ImportError:
    HAVE_JSONSCHEMA = False

KG = REPO / "kg"
SCHEMA = KG / "schema"


def load_schemas() -> dict[str, dict]:
    schemas = {}
    if not SCHEMA.exists():
        return schemas
    for f in SCHEMA.glob("*.schema.json"):
        s = json.loads(f.read_text())
        # match against $id type field
        name = f.stem.replace(".schema", "")
        schemas[name] = s
    return schemas


def main() -> int:
    errors: list[str] = []

    nodes_dir = KG / "nodes"
    edges_path = KG / "edges.jsonl"

    if not nodes_dir.exists():
        print("error: kg/nodes/ does not exist — run build_kg.py first", file=sys.stderr)
        return 1

    nodes: dict[str, dict] = {}
    for f in nodes_dir.rglob("*.json"):
        node = json.loads(f.read_text())
        nid = node.get("id")
        if not nid:
            errors.append(f"{f}: missing id")
            continue
        if nid in nodes:
            errors.append(f"{f}: duplicate id {nid}")
        nodes[nid] = node

    schemas = load_schemas()
    base_schema = schemas.get("node.base") or schemas.get("base")
    if HAVE_JSONSCHEMA and base_schema:
        v = Draft202012Validator(base_schema)
        for nid, node in nodes.items():
            for err in v.iter_errors(node):
                errors.append(f"{nid}: {err.message}")
    elif not HAVE_JSONSCHEMA:
        print("note: jsonschema not installed — skipping schema validation (pip3 install jsonschema)", file=sys.stderr)

    # Edges: every endpoint must resolve
    if edges_path.exists():
        for ln, line in enumerate(edges_path.read_text().splitlines(), 1):
            if not line.strip():
                continue
            e = json.loads(line)
            if e["source"] not in nodes:
                errors.append(f"edges.jsonl:{ln}: source not found: {e['source']}")
            if e["target"] not in nodes:
                errors.append(f"edges.jsonl:{ln}: target not found: {e['target']}")

    # Coverage report (informational, not error)
    cov_file = KG / "indexes" / "coverage.json"
    if cov_file.exists():
        cov = json.loads(cov_file.read_text())
        print(f"coverage: {cov['uncovered_term_count']} raw terms not yet in KG, "
              f"{len(cov['exam_topics_without_covers_edge'])} exam topics with no covers edges")
        if cov['exam_topics_without_covers_edge']:
            print("  exam topics needing covers edges:")
            for t in cov['exam_topics_without_covers_edge'][:10]:
                print(f"    - {t}")

    if errors:
        print(f"\n{len(errors)} validation errors:", file=sys.stderr)
        for e in errors[:50]:
            print(f"  {e}", file=sys.stderr)
        return 1

    print(f"\nvalidation OK — {len(nodes)} nodes, edges file present: {edges_path.exists()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
