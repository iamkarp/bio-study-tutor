#!/usr/bin/env python3
"""Build knowledge graph from wiki/ markdown.

Usage:
  python3 tools/build_kg.py
  python3 tools/build_kg.py --wiki ./wiki --kg ./kg
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from tools.extract.frontmatter import iter_pages, Page  # noqa: E402
from tools.extract.sections import split_sections, section_aliases  # noqa: E402
from tools.extract.tables import parse_tables, strip_md  # noqa: E402
from tools.extract.wikilinks import find_wikilinks, resolve_target, path_to_slug  # noqa: E402

EXTRACTOR_VERSION = "0.1.0"

# Section canonical key → edge relation. Anything not listed defaults to related_to.
SECTION_TO_RELATION: dict[str, str] = {
    "summary": None,                # body of summary holds no link semantics by default
    "key_facts": "mentioned_in",    # links inside facts → mentioned_in
    "steps": "part_of",             # process steps → step part_of process (reversed below)
    "components": "part_of",
    "produces": "produces",
    "produced_by": "produced_by",
    "catalyzes": "catalyzes",
    "catalyzed_by": "catalyzed_by",
    "causes": "causes",
    "caused_by": "caused_by",
    "regulates": "regulates",
    "regulated_by": "regulated_by",
    "located_in": "located_in",
    "demonstrates": "demonstrates",
    "demonstrated_by": "demonstrated_by",
    "discovered_by": "discovered_by",
    "compared_to": "compared_to",
    "example_of": "example_of",
    "covers": "covers",
    "related": "related_to",
    "sources": "cites",
    "gotchas": "related_to",
    "requires": "requires",
    "contradicts": "contradicts",
    "supersedes": "supersedes",
    "instance_of": "instance_of",
}

# Sections where the wiki link target is the *parent* (steps part_of process), so the
# edge direction is reversed: edge from current page → target with relation r becomes
# edge from current page → target with relation r' = part_of (current is part of target).
# Default semantics: edge goes from current_page → linked_target with the listed relation.
# Override here when the natural direction is target → current.
SECTION_REVERSE: set[str] = set()  # currently none — semantics encoded directly above

NODE_TYPES = {
    "chapter", "exam_topic", "concept", "process", "structure", "molecule",
    "enzyme", "term", "inheritance_pattern", "experiment", "person", "disease",
    "technique", "principle", "comparison", "source",
}

EDGE_RELATIONS = {
    "part_of", "consists_of", "produces", "produced_by", "catalyzes", "catalyzed_by",
    "precedes", "follows", "pairs_with", "complement_of", "transcribes_to",
    "translates_to", "compared_to", "discovered_by", "demonstrates", "demonstrated_by",
    "causes", "caused_by", "regulates", "regulated_by", "located_in", "mentioned_in",
    "example_of", "instance_of", "inherits_as", "requires", "contradicts",
    "supersedes", "cites", "related_to", "covers",
}


def slugify(s: str) -> str:
    s = re.sub(r"[^a-z0-9-]+", "-", s.lower()).strip("-")
    return s


def first_paragraph(body: str) -> str:
    # Body without sections — first non-empty paragraph after frontmatter end.
    text = body.strip()
    # Drop leading "# Heading" lines
    text = re.sub(r"^#\s+.*$", "", text, count=1, flags=re.MULTILINE).strip()
    sections = split_sections(text)
    summary = sections.get("Summary") or sections.get("summary") or sections.get("")
    if not summary:
        return ""
    paras = [p.strip() for p in summary.split("\n\n") if p.strip()]
    if not paras:
        return ""
    return strip_md(paras[0])[:400]


def build_node(page: Page) -> dict[str, Any] | None:
    fm = page.frontmatter
    if not fm.get("id") or not fm.get("type"):
        return None
    if fm["type"] not in NODE_TYPES:
        print(f"warn: {page.path} has unknown type {fm['type']!r}", file=sys.stderr)
        return None
    node: dict[str, Any] = {
        "id": fm["id"],
        "type": fm["type"],
        "title": fm.get("title", fm.get("id")),
        "slug": fm.get("slug", path_to_slug(str(page.path))),
        "aliases": fm.get("aliases", []) or [],
        "tags": fm.get("tags", []) or [],
        "status": fm.get("status", "active"),
        "wiki_path": str(page.path),
        "summary": fm.get("summary") or first_paragraph(page.body),
        "source_refs": fm.get("source_refs", []) or [],
        "confidence": fm.get("confidence", 1.0),
        "provenance": {
            "ingested_from": [str(page.path)],
            "method": "parser",
            "extractor_version": EXTRACTOR_VERSION,
        },
        "version": int(fm.get("version", 1)),
    }
    if fm.get("created"):
        node["created"] = str(fm["created"])
    if fm.get("updated"):
        node["updated"] = str(fm["updated"])
    # Carry through type-specific fields verbatim
    for k in (
        "chapters", "exam_topics", "category", "step_index", "modality",
        "scientific_name", "formula", "abbreviation", "monomers", "polymer_of",
        "alleles", "trait", "year", "lifespan", "field",
    ):
        if k in fm:
            node[k] = fm[k]
    return node


def build_edges_from_page(page: Page, slug_to_id: dict[str, str], nodes_by_id: dict[str, dict]) -> list[dict[str, Any]]:
    edges: list[dict[str, Any]] = []
    fm = page.frontmatter
    src_id = fm.get("id")
    if not src_id:
        return edges

    # ── Frontmatter-driven edges ──────────────────────────────────────────
    # chapters: [9, 10] → src --mentioned_in--> chapter:09
    for ch in fm.get("chapters", []) or []:
        ch_slug = f"{int(ch):02d}" if isinstance(ch, int) else slugify(str(ch))
        target = f"chapter:{ch_slug}"
        if target in nodes_by_id:
            edges.append({
                "source": src_id, "target": target, "relation": "mentioned_in",
                "provenance": {"method": "frontmatter", "extractor_version": EXTRACTOR_VERSION,
                               "src_section": "chapters"},
                "confidence": 1.0,
            })

    # exam_topics: [meiosis-overview] → src --covers--> exam_topic:meiosis-overview
    # (For exam_topic pages, the reverse: exam_topic --covers--> concept)
    if fm.get("type") == "exam_topic":
        # exam_topic pages don't auto-emit covers from frontmatter (handled by ## Covers section)
        pass
    else:
        for et in fm.get("exam_topics", []) or []:
            target = f"exam_topic:{slugify(str(et))}"
            if target in nodes_by_id:
                # reversed: exam_topic --covers--> this node
                edges.append({
                    "source": target, "target": src_id, "relation": "covers",
                    "provenance": {"method": "frontmatter", "extractor_version": EXTRACTOR_VERSION,
                                   "src_section": "exam_topics"},
                    "confidence": 1.0,
                })

    # ── Section-driven wikilink edges ─────────────────────────────────────
    sections = split_sections(page.body)
    for heading, content in sections.items():
        canonical = section_aliases(heading) if heading else "summary"
        relation = SECTION_TO_RELATION.get(canonical, "related_to")
        if relation is None:
            # In summary section, links are mentions
            relation = "mentioned_in"
        for target_str, _display, _pos in find_wikilinks(content):
            target_id = resolve_target(target_str, Path(page.path), slug_to_id)
            if not target_id or target_id not in nodes_by_id:
                continue
            if target_id == src_id:
                continue
            # Special: in Sources section, we cite the source node (target should be source:*)
            edge = {
                "source": src_id, "target": target_id, "relation": relation,
                "provenance": {"method": "wikilink", "extractor_version": EXTRACTOR_VERSION,
                               "src_section": canonical},
                "confidence": 1.0,
            }
            edges.append(edge)

    return edges


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False, sort_keys=False) + "\n",
                    encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--wiki", default=str(REPO / "wiki"))
    ap.add_argument("--kg", default=str(REPO / "kg"))
    args = ap.parse_args()

    wiki_root = Path(args.wiki).resolve()
    kg_root = Path(args.kg).resolve()

    # Pass 1: read pages, build nodes + slug map
    pages: list[Page] = list(iter_pages(wiki_root))
    nodes: list[dict[str, Any]] = []
    slug_to_id: dict[str, str] = {}
    for p in pages:
        node = build_node(p)
        if not node:
            continue
        nodes.append(node)
        slug_to_id[node["slug"]] = node["id"]
        for alias in node.get("aliases", []) or []:
            slug_to_id.setdefault(slugify(alias), node["id"])

    nodes_by_id = {n["id"]: n for n in nodes}

    # Pass 2: edges
    edges: list[dict[str, Any]] = []
    for p in pages:
        edges.extend(build_edges_from_page(p, slug_to_id, nodes_by_id))

    # Merge any hand-authored overlay edges
    overlay_dir = kg_root / "overlays"
    if overlay_dir.exists():
        for of in sorted(overlay_dir.glob("*.json")):
            data = json.loads(of.read_text())
            edges.extend(data.get("edges", []))
            for n in data.get("nodes", []):
                if n["id"] not in nodes_by_id:
                    nodes.append(n)
                    nodes_by_id[n["id"]] = n
                    slug_to_id[n["slug"]] = n["id"]

    # Deduplicate edges (source, target, relation)
    seen = set()
    deduped = []
    for e in edges:
        key = (e["source"], e["target"], e["relation"])
        if key in seen:
            continue
        seen.add(key)
        deduped.append(e)
    edges = deduped

    # ── Write nodes/<type>/<slug>.json ────────────────────────────────────
    nodes_dir = kg_root / "nodes"
    if nodes_dir.exists():
        for f in nodes_dir.rglob("*.json"):
            f.unlink()
    for node in nodes:
        out = nodes_dir / node["type"] / f"{node['slug']}.json"
        write_json(out, node)

    # ── Write edges.jsonl ────────────────────────────────────────────────
    edges_path = kg_root / "edges.jsonl"
    edges_path.parent.mkdir(parents=True, exist_ok=True)
    with edges_path.open("w", encoding="utf-8") as f:
        for e in edges:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")

    # ── Indexes ──────────────────────────────────────────────────────────
    idx_dir = kg_root / "indexes"

    by_type: dict[str, list[str]] = defaultdict(list)
    by_tag: dict[str, list[str]] = defaultdict(list)
    by_chapter: dict[str, list[str]] = defaultdict(list)
    by_exam_topic: dict[str, list[str]] = defaultdict(list)
    alias_map: dict[str, str] = {}
    backlinks: dict[str, list[dict[str, str]]] = defaultdict(list)

    for n in nodes:
        by_type[n["type"]].append(n["id"])
        for t in n.get("tags", []) or []:
            by_tag[t].append(n["id"])
        for ch in n.get("chapters", []) or []:
            by_chapter[str(ch)].append(n["id"])
        for et in n.get("exam_topics", []) or []:
            by_exam_topic[str(et)].append(n["id"])
        for a in n.get("aliases", []) or []:
            alias_map[slugify(a)] = n["id"]

    for e in edges:
        backlinks[e["target"]].append({"source": e["source"], "relation": e["relation"]})

    # Orphans: pages with no inbound edges
    inbound = {e["target"] for e in edges}
    orphans = [n["id"] for n in nodes if n["id"] not in inbound]

    # Coverage: every term in raw/extracted/ that lacks a node, every exam_topic with zero outbound covers
    raw_terms = collect_raw_terms(REPO / "raw" / "extracted")
    known_titles = {n["title"].lower() for n in nodes} | set(alias_map.keys()) | set(slug_to_id.keys())
    uncovered_terms = sorted({t for t in raw_terms if slugify(t) not in alias_map and slugify(t) not in slug_to_id})

    exam_outbound: dict[str, int] = defaultdict(int)
    for e in edges:
        if e["relation"] == "covers" and e["source"].startswith("exam_topic:"):
            exam_outbound[e["source"]] += 1
    uncovered_topics = [n["id"] for n in nodes if n["type"] == "exam_topic" and exam_outbound.get(n["id"], 0) == 0]

    write_json(idx_dir / "by-type.json", {k: sorted(v) for k, v in by_type.items()})
    write_json(idx_dir / "by-tag.json", {k: sorted(v) for k, v in by_tag.items()})
    write_json(idx_dir / "by-chapter.json", {k: sorted(v) for k, v in by_chapter.items()})
    write_json(idx_dir / "by-exam-topic.json", {k: sorted(v) for k, v in by_exam_topic.items()})
    write_json(idx_dir / "alias-map.json", alias_map)
    write_json(idx_dir / "backlinks.json", backlinks)
    write_json(idx_dir / "orphans.json", sorted(orphans))
    write_json(idx_dir / "coverage.json", {
        "uncovered_terms_in_raw": uncovered_terms[:500],
        "uncovered_term_count": len(uncovered_terms),
        "exam_topics_without_covers_edge": uncovered_topics,
    })

    # ── Manifest ─────────────────────────────────────────────────────────
    h = hashlib.sha256()
    for n in sorted(nodes, key=lambda x: x["id"]):
        h.update(json.dumps(n, sort_keys=True).encode())
    for e in sorted(edges, key=lambda x: (x["source"], x["target"], x["relation"])):
        h.update(json.dumps(e, sort_keys=True).encode())
    write_json(kg_root / "manifest.json", {
        "schema_version": EXTRACTOR_VERSION,
        "built": str(date.today()),
        "node_count": len(nodes),
        "edge_count": len(edges),
        "by_type": {k: len(v) for k, v in by_type.items()},
        "edge_relations": dict(sorted(((r, sum(1 for e in edges if e["relation"] == r)) for r in EDGE_RELATIONS), key=lambda x: -x[1])),
        "hash": h.hexdigest()[:16],
    })

    # Build log
    (kg_root / "build.log").write_text(
        f"build {date.today()}\n"
        f"  nodes: {len(nodes)}\n"
        f"  edges: {len(edges)}\n"
        f"  orphans: {len(orphans)}\n"
        f"  uncovered_terms: {len(uncovered_terms)}\n"
        f"  uncovered_exam_topics: {len(uncovered_topics)}\n",
        encoding="utf-8",
    )

    print(f"built {len(nodes)} nodes and {len(edges)} edges")
    print(f"  orphans: {len(orphans)}")
    print(f"  uncovered exam topics: {len(uncovered_topics)}")
    print(f"  uncovered raw terms: {len(uncovered_terms)}")


# ── Heuristic raw-term collector ─────────────────────────────────────────
BOLD_RE = re.compile(r"\*\*([^*]+)\*\*")
NOTES_KEY_RE = re.compile(r"^\s*[-*]\s*\*\*([^*]+)\*\*", re.MULTILINE)


def collect_raw_terms(extracted_dir: Path) -> set[str]:
    terms: set[str] = set()
    if not extracted_dir.exists():
        return terms
    for f in extracted_dir.rglob("*.md"):
        text = f.read_text(encoding="utf-8")
        for m in BOLD_RE.finditer(text):
            t = m.group(1).strip()
            if 2 < len(t) < 60 and not t.startswith("Slide"):
                terms.add(t)
    return terms


if __name__ == "__main__":
    main()
