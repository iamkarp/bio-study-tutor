"""Parse and write YAML frontmatter on markdown wiki pages."""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n(.*)$", re.DOTALL)
KG_BLOCK_RE = re.compile(r"<!--\s*kg:begin\s*-->.*?<!--\s*kg:end\s*-->\s*", re.DOTALL)


def strip_kg_block(body: str) -> str:
    return KG_BLOCK_RE.sub("", body)


@dataclass
class Page:
    path: Path
    frontmatter: dict[str, Any]
    body: str

    @property
    def relpath(self) -> str:
        return str(self.path)


def read_page(path: Path, wiki_root: Path) -> Page:
    text = path.read_text(encoding="utf-8")
    m = FRONTMATTER_RE.match(text)
    if not m:
        return Page(path=path.relative_to(wiki_root.parent), frontmatter={}, body=strip_kg_block(text))
    fm_text, body = m.group(1), m.group(2)
    fm = yaml.safe_load(fm_text) or {}
    return Page(path=path.relative_to(wiki_root.parent), frontmatter=fm, body=strip_kg_block(body))


def write_page(page: Page, wiki_root: Path) -> None:
    fm_text = yaml.safe_dump(page.frontmatter, sort_keys=False, allow_unicode=True).strip()
    out = f"---\n{fm_text}\n---\n{page.body}"
    abs_path = wiki_root.parent / page.path
    abs_path.write_text(out, encoding="utf-8")


def iter_pages(wiki_root: Path):
    skip = {"CLAUDE.md"}
    for p in sorted(wiki_root.rglob("*.md")):
        if p.name in skip:
            continue
        yield read_page(p, wiki_root)
