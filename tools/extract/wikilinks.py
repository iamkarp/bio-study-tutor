"""Find [[wikilinks]] in markdown and resolve them to KG node ids."""
from __future__ import annotations

import re
from pathlib import Path

WIKILINK_RE = re.compile(r"\[\[([^\]|]+?)(?:\|([^\]]+))?\]\]")


def find_wikilinks(text: str) -> list[tuple[str, str | None, int]]:
    out = []
    for m in WIKILINK_RE.finditer(text):
        target = m.group(1).strip()
        display = m.group(2).strip() if m.group(2) else None
        out.append((target, display, m.start()))
    return out


def path_to_slug(path: str) -> str:
    s = path.rsplit("/", 1)[-1]
    s = re.sub(r"\.md$", "", s)
    s = re.sub(r"#.*$", "", s)
    s = re.sub(r"[^a-z0-9-]+", "-", s.lower()).strip("-")
    return s


def resolve_target(target: str, page_path: Path, slug_to_id: dict[str, str]) -> str | None:
    """Resolve a wikilink target string to a canonical node id."""
    norm = target.strip().lstrip("./")
    norm = re.sub(r"#.*$", "", norm)
    norm = re.sub(r"\.md$", "", norm)
    while norm.startswith("../"):
        norm = norm[3:]

    if norm.startswith("raw/"):
        slug = path_to_slug(norm[len("raw/"):])
        return f"source:{slug}"

    parts = norm.split("/")
    candidate_slug = path_to_slug(parts[-1])
    if candidate_slug in slug_to_id:
        return slug_to_id[candidate_slug]
    full_slug = path_to_slug(norm)
    if full_slug in slug_to_id:
        return slug_to_id[full_slug]
    return None
