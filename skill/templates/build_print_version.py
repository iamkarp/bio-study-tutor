#!/usr/bin/env python3
"""Build a single-file print-ready HTML of the wiki with numbered sections.

Each page gets a sequential section number (§1, §2, ...). [[wikilinks]] in
bodies are converted into "display [§N]" references that point to the section
number containing the linked page.

Usage:
    python3 tools/build_print_version.py
    open print/study-guide.html  # then File → Print → Save as PDF
"""
from __future__ import annotations

import re
import sys
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
APP_DIR = REPO / "app"
sys.path.insert(0, str(APP_DIR))

import markdown as md  # noqa: E402

from kg_loader import (  # noqa: E402
    CHAPTER_TITLES,
    Page,
    TYPE_LABELS,
    load_pages,
)
from wikilink import WIKILINK_RE, _slugify  # noqa: E402

OUT = REPO / "print" / "study-guide.html"

# Order of types within each chapter — top-of-chapter first, vocab last.
TYPE_ORDER = [
    "chapter",
    "exam_topic",
    "principle",
    "experiment",
    "process",
    "structure",
    "molecule",
    "enzyme",
    "technique",
    "inheritance_pattern",
    "disease",
    "person",
    "comparison",
    "concept",
    "term",
    "source",
]


def _primary_chapter(p: Page) -> int:
    """Each page is printed under its lowest-numbered chapter."""
    if not p.chapters:
        return 99
    nums = []
    for c in p.chapters:
        try:
            nums.append(int(c))
        except (ValueError, TypeError):
            continue
    return min(nums) if nums else 99


def order_pages(pages: dict[str, Page]) -> list[Page]:
    """Sort pages: chapter (asc), type (TYPE_ORDER), then title (asc)."""
    type_rank = {t: i for i, t in enumerate(TYPE_ORDER)}
    items = list(pages.values())
    items.sort(key=lambda p: (
        _primary_chapter(p),
        type_rank.get(p.type, 99),
        p.title.lower(),
    ))
    return items


def assign_numbers(ordered: list[Page]) -> tuple[dict[str, int], dict[int, str]]:
    """Map page id → section number (1-based) and section number → id."""
    id_to_num: dict[str, int] = {}
    num_to_id: dict[int, str] = {}
    for i, p in enumerate(ordered, start=1):
        id_to_num[p.id] = i
        num_to_id[i] = p.id
    return id_to_num, num_to_id


def build_resolver(pages: dict[str, Page]) -> dict[str, str]:
    """slug + id + slugified id → canonical id."""
    out: dict[str, str] = {}
    for p in pages.values():
        out[p.slug] = p.id
        out[p.id] = p.id
        out[_slugify(p.id)] = p.id
    return out


def replace_wikilinks(body: str, resolver: dict[str, str],
                      id_to_num: dict[str, int],
                      id_to_title: dict[str, str]) -> str:
    def sub(m: re.Match) -> str:
        target = m.group(1).strip()
        custom = m.group(2)
        # Skip raw source links — render as italic notation
        if target.startswith("../raw/") or "raw/extracted" in target:
            label = custom or target.rsplit("/", 1)[-1]
            return f'<span class="src-ref">{label}</span>'
        candidates = [target, _slugify(target)]
        if "/" in target:
            candidates.append(target.rsplit("/", 1)[-1])
            candidates.append(_slugify(target.rsplit("/", 1)[-1]))
        page_id = next((resolver[c] for c in candidates if c in resolver), None)
        if not page_id:
            display = custom or target
            return f'<span class="ref-broken">{display}</span>'
        num = id_to_num.get(page_id)
        title = id_to_title.get(page_id, target)
        display = custom or title
        if num is None:
            return display
        return f'<a class="xref" href="#sec-{num}">{display}<span class="ref">[§{num}]</span></a>'
    return WIKILINK_RE.sub(sub, body)


CHAPTER_LABELS = {
    9: "Chapter 9 — Meiosis",
    10: "Chapter 10 — Patterns of Inheritance",
    11: "Chapter 11 — DNA Structure & Replication",
    12: "Chapter 12 — How Genes Work",
    13: "Chapter 13 — The New Biology",
}


PRINT_CSS = """
@page {
    size: letter;
    margin: 0.8in 0.75in 0.9in 0.75in;
    @bottom-center { content: counter(page); font-family: serif; font-size: 9pt; color: #666; }
    @top-center { content: "Bio 1320 Exam 3 Study Guide"; font-family: serif; font-size: 8.5pt; color: #999; }
}
@media screen {
    body { background: #f8f8f8; }
    .pages { max-width: 7.5in; margin: 24px auto; padding: 0.8in 0.75in;
             background: white; box-shadow: 0 2px 12px rgba(0,0,0,0.08); }
    .toolbar { position: sticky; top: 0; background: white; padding: 12px 16px;
               border-bottom: 1px solid #e5e5e5; z-index: 10;
               box-shadow: 0 1px 3px rgba(0,0,0,0.04); }
}
@media print {
    body { background: white; }
    .pages { max-width: none; margin: 0; padding: 0; box-shadow: none; }
    .toolbar { display: none; }
    .page-break { page-break-before: always; }
    h2.chapter-heading { page-break-before: always; }
    h3.section-heading { page-break-after: avoid; }
    a { color: #000; text-decoration: none; }
    a.xref .ref { color: #555; }
}
body {
    font-family: 'Charter', 'Georgia', 'Cambria', 'Times New Roman', serif;
    font-size: 11pt; line-height: 1.55; color: #111;
}
.toolbar h1 { font-size: 16pt; margin: 0 0 4px 0; }
.toolbar p { margin: 0; color: #666; font-size: 11pt; }
.toolbar button {
    margin-right: 8px; padding: 6px 14px; font-size: 13px; cursor: pointer;
    border: 1px solid #ccc; border-radius: 6px; background: white;
}
.toolbar button:hover { background: #f0f0f0; }
.toolbar button.primary { background: #4f46e5; color: white; border-color: #4f46e5; }
.toolbar button.primary:hover { background: #4338ca; }

h1.title { font-size: 28pt; margin: 0 0 8pt 0; letter-spacing: -0.01em; }
.subtitle { font-size: 13pt; color: #555; margin: 0 0 24pt 0; font-style: italic; }
.builddate { font-size: 9.5pt; color: #888; margin-bottom: 24pt; }

h2.chapter-heading {
    font-size: 22pt; margin: 0 0 14pt 0;
    border-bottom: 1.5pt solid #333; padding-bottom: 6pt;
    letter-spacing: -0.005em;
}
h3.section-heading {
    font-size: 13pt; font-weight: 600; margin: 18pt 0 4pt 0;
    color: #111; letter-spacing: -0.005em;
}
.sec-num {
    color: #888; font-weight: 400; font-size: 11.5pt;
    margin-right: 6pt; font-variant-numeric: lining-nums;
}
.type-tag {
    display: inline-block; font-size: 8.5pt; color: #777;
    text-transform: uppercase; letter-spacing: 0.04em;
    margin-left: 8pt; vertical-align: 2pt; font-weight: 400;
}

.section-body { margin: 4pt 0 0 0; }
.section-body p { margin: 4pt 0; }
.section-body ul, .section-body ol { margin: 6pt 0; padding-left: 20pt; }
.section-body li { margin: 2pt 0; }
.section-body table { border-collapse: collapse; margin: 8pt 0; font-size: 10pt; }
.section-body th, .section-body td {
    border: 0.5pt solid #999; padding: 3pt 8pt; text-align: left;
}
.section-body th { background: #f5f5f5; font-weight: 600; }
.section-body code {
    font-family: 'Consolas', 'Menlo', monospace; font-size: 9.5pt;
    background: #f5f5f5; padding: 1pt 3pt; border-radius: 2pt;
}

a.xref { color: #2c3e8a; text-decoration: none; }
a.xref:hover { text-decoration: underline; }
.ref { font-size: 8.5pt; color: #888; vertical-align: 2pt; margin-left: 1pt; }
.src-ref { color: #888; font-size: 9.5pt; font-style: italic; }
.ref-broken { color: #aaa; font-style: italic; }

.toc { columns: 2; column-gap: 24pt; column-rule: 0.5pt solid #ddd;
       margin-top: 12pt; }
.toc-entry { display: block; break-inside: avoid; padding: 1pt 0;
             font-size: 10pt; line-height: 1.4; color: #111;
             text-decoration: none; }
.toc-entry:hover { background: #f5f5f5; }
.toc-num { display: inline-block; width: 38px; color: #888;
           font-variant-numeric: lining-nums; }
.toc-title { color: #111; }
.toc-chapter-heading {
    font-size: 11pt; font-weight: 600; margin: 10pt 0 3pt 0;
    color: #333; break-inside: avoid; break-after: avoid;
}

.index { columns: 2; column-gap: 24pt; column-rule: 0.5pt solid #ddd;
         font-size: 10pt; line-height: 1.5; }
.index-entry { break-inside: avoid; padding: 1pt 0; }
.index-letter { font-weight: 700; font-size: 13pt; margin: 12pt 0 4pt 0;
                column-span: all; break-after: avoid; }
"""


def md_to_html(text: str) -> str:
    return md.markdown(text, extensions=["tables", "fenced_code", "sane_lists"])


def render_section(p: Page, num: int, resolver: dict[str, str],
                   id_to_num: dict[str, int],
                   id_to_title: dict[str, str]) -> str:
    body = replace_wikilinks(p.body, resolver, id_to_num, id_to_title)
    body_html = md_to_html(body)
    type_label = TYPE_LABELS.get(p.type, p.type).rstrip("s") if p.type != "exam_topic" else "Exam topic"
    return (
        f'<section id="sec-{num}">'
        f'<h3 class="section-heading">'
        f'<span class="sec-num">§{num}</span>{p.title}'
        f'<span class="type-tag">{type_label}</span>'
        f'</h3>'
        f'<div class="section-body">{body_html}</div>'
        f'</section>'
    )


def render_toc(ordered: list[Page]) -> str:
    """Produce a chapter-grouped TOC with section numbers."""
    by_chapter: dict[int, list[tuple[int, Page]]] = {}
    for i, p in enumerate(ordered, start=1):
        by_chapter.setdefault(_primary_chapter(p), []).append((i, p))
    parts = ['<div class="toc">']
    for ch in sorted(by_chapter.keys()):
        parts.append(f'<div class="toc-chapter-heading">{CHAPTER_LABELS.get(ch, f"Chapter {ch}")}</div>')
        for num, p in by_chapter[ch]:
            parts.append(
                f'<a class="toc-entry" href="#sec-{num}">'
                f'<span class="toc-num">§{num}</span>'
                f'<span class="toc-title">{p.title}</span>'
                f'</a>'
            )
    parts.append("</div>")
    return "".join(parts)


def render_index(ordered: list[Page]) -> str:
    """Alphabetical index of all sections."""
    by_letter: dict[str, list[tuple[int, Page]]] = {}
    for i, p in enumerate(ordered, start=1):
        letter = (p.title[0] if p.title else "?").upper()
        if not letter.isalpha():
            letter = "#"
        by_letter.setdefault(letter, []).append((i, p))
    parts = ['<div class="index">']
    for letter in sorted(by_letter.keys()):
        parts.append(f'<div class="index-letter">{letter}</div>')
        for num, p in sorted(by_letter[letter], key=lambda x: x[1].title.lower()):
            type_label = TYPE_LABELS.get(p.type, p.type).rstrip("s")
            parts.append(
                f'<div class="index-entry">'
                f'<a class="xref" href="#sec-{num}">{p.title}</a> '
                f'<span style="color:#888; font-size:9pt;">— {type_label}, §{num}</span>'
                f'</div>'
            )
    parts.append("</div>")
    return "".join(parts)


def render_chapter_intro(ch: int) -> str:
    return (
        f'<div class="page-break"></div>'
        f'<h2 class="chapter-heading" id="ch-{ch}">{CHAPTER_LABELS.get(ch, f"Chapter {ch}")}</h2>'
    )


def main() -> None:
    pages = load_pages()
    ordered = order_pages(pages)
    id_to_num, _ = assign_numbers(ordered)
    id_to_title = {pid: p.title for pid, p in pages.items()}
    resolver = build_resolver(pages)

    # Build sections, inserting a chapter heading before the first page of each chapter.
    sections_html: list[str] = []
    last_ch = None
    for i, p in enumerate(ordered, start=1):
        ch = _primary_chapter(p)
        if ch != last_ch:
            sections_html.append(render_chapter_intro(ch))
            last_ch = ch
        sections_html.append(render_section(p, i, resolver, id_to_num, id_to_title))

    body = "\n".join(sections_html)
    toc = render_toc(ordered)
    index = render_index(ordered)

    today = date.today().isoformat()

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Bio 1320 Exam 3 Study Guide — Print Edition</title>
<style>{PRINT_CSS}</style>
</head>
<body>
<div class="toolbar">
  <h1>Bio 1320 Exam 3 Study Guide — Print Edition</h1>
  <p style="margin: 4px 0 10px 0;"><b>{len(ordered)}</b> numbered sections · cross-references resolved · ready to print</p>
  <button class="primary" onclick="window.print()">Print → Save as PDF</button>
  <button onclick="window.scrollTo(0, 0)">Back to top</button>
</div>

<div class="pages">

<h1 class="title">Bio 1320 Exam 3</h1>
<p class="subtitle">Study Guide · Chapters 9–13</p>
<p class="builddate">Generated {today} · {len(ordered)} numbered sections</p>

<div class="page-break"></div>
<h2 class="chapter-heading">Table of Contents</h2>
{toc}

{body}

<div class="page-break"></div>
<h2 class="chapter-heading">Index</h2>
{index}

</div>
</body>
</html>
"""

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(html, encoding="utf-8")
    print(f"Wrote {OUT.relative_to(REPO)} ({len(ordered)} sections, {len(html):,} bytes)")


if __name__ == "__main__":
    main()
