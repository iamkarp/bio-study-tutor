"""Load wiki + KG into memory for the Shiny app."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[1]
WIKI = REPO / "wiki"
KG = REPO / "kg"

FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n(.*)$", re.DOTALL)


@dataclass
class Page:
    id: str
    type: str
    slug: str
    title: str
    chapters: list[int]
    exam_topics: list[str]
    tags: list[str]
    body: str
    path: str


def load_pages() -> dict[str, Page]:
    pages: dict[str, Page] = {}
    for f in sorted(WIKI.rglob("*.md")):
        name = f.name
        if name in {"CLAUDE.md", "index.md", "log.md", "overview.md"}:
            continue
        text = f.read_text(encoding="utf-8")
        m = FRONTMATTER_RE.match(text)
        if not m:
            continue
        fm = yaml.safe_load(m.group(1)) or {}
        body = m.group(2).strip()
        if not fm.get("id"):
            continue
        pages[fm["id"]] = Page(
            id=fm["id"],
            type=fm.get("type", ""),
            slug=fm.get("slug", ""),
            title=fm.get("title", fm["id"]),
            chapters=fm.get("chapters", []) or [],
            exam_topics=fm.get("exam_topics", []) or [],
            tags=fm.get("tags", []) or [],
            body=body,
            path=str(f.relative_to(REPO)),
        )
    return pages


def load_edges() -> list[dict]:
    p = KG / "edges.jsonl"
    if not p.exists():
        return []
    return [json.loads(line) for line in p.read_text().splitlines() if line.strip()]


def load_nodes_json() -> list[dict]:
    nodes_dir = KG / "nodes"
    if not nodes_dir.exists():
        return []
    return [json.loads(f.read_text()) for f in nodes_dir.rglob("*.json")]


def pages_by_chapter(pages: dict[str, Page]) -> dict[int, list[Page]]:
    out: dict[int, list[Page]] = {}
    for p in pages.values():
        for ch in p.chapters:
            try:
                ch_int = int(ch)
            except (ValueError, TypeError):
                continue
            out.setdefault(ch_int, []).append(p)
    for v in out.values():
        v.sort(key=lambda p: (p.type, p.title.lower()))
    return out


def pages_by_type(pages: dict[str, Page]) -> dict[str, list[Page]]:
    out: dict[str, list[Page]] = {}
    for p in pages.values():
        out.setdefault(p.type, []).append(p)
    for v in out.values():
        v.sort(key=lambda p: p.title.lower())
    return out


CHAPTER_TITLES = {
    9: "Chapter 9 — Meiosis",
    10: "Chapter 10 — Patterns of Inheritance",
    11: "Chapter 11 — DNA Structure & Replication",
    12: "Chapter 12 — How Genes Work",
    13: "Chapter 13 — New Biology",
}

TYPE_LABELS = {
    "exam_topic": "Exam Topics",
    "concept": "Concepts",
    "process": "Processes",
    "structure": "Structures",
    "molecule": "Molecules",
    "enzyme": "Enzymes",
    "term": "Vocabulary Terms",
    "inheritance_pattern": "Inheritance Patterns",
    "experiment": "Experiments",
    "person": "People",
    "disease": "Diseases / Disorders",
    "technique": "Techniques",
    "principle": "Principles",
    "comparison": "Comparisons",
    "chapter": "Chapters",
    "source": "Sources",
}


def corpus_text(pages: dict[str, Page], chapter: int | None = None,
                node_type: str | None = None, max_chars: int = 60000) -> str:
    """Concatenated wiki text — used as RAG context for the LLM."""
    chunks: list[str] = []
    total = 0
    for p in pages.values():
        if chapter and chapter not in p.chapters:
            continue
        if node_type and p.type != node_type:
            continue
        snippet = f"### {p.title} ({p.type})\n{p.body}\n"
        if total + len(snippet) > max_chars:
            break
        chunks.append(snippet)
        total += len(snippet)
    return "\n".join(chunks)
