"""Resolve [[wikilink]] syntax in markdown bodies into clickable HTML anchors."""
from __future__ import annotations

import re

WIKILINK_RE = re.compile(r"\[\[([^\]|]+?)(?:\|([^\]]+))?\]\]")


def _slugify(s: str) -> str:
    s = re.sub(r"#.*$", "", s)  # drop fragment
    s = re.sub(r"\.md$", "", s, flags=re.IGNORECASE)
    parts = re.split(r"[/:]", s.strip())
    last = parts[-1] if parts else ""
    return re.sub(r"[^a-z0-9-]+", "-", last.lower()).strip("-")


def build_resolver_maps(pages: dict) -> tuple[dict[str, str], dict[str, str]]:
    """Return (slug_or_alias -> id, id -> title)."""
    slug_to_id: dict[str, str] = {}
    id_to_title: dict[str, str] = {}
    for p in pages.values():
        id_to_title[p.id] = p.title
        slug_to_id[p.slug] = p.id
        # also id without prefix is acceptable
        slug_to_id[p.id] = p.id
        slug_to_id[_slugify(p.id)] = p.id
        # aliases (if loaded — Page dataclass doesn't have aliases attribute, so skip safely)
    return slug_to_id, id_to_title


def render_wikilinks(body: str, slug_to_id: dict[str, str],
                     id_to_title: dict[str, str]) -> str:
    """Convert [[target]] / [[target|display]] to <a class='wikilink' data-page-id='id'>..</a>.

    Resolution: try the raw target slug, then its last path segment, then a slug-normalized
    form. Unresolved links render as a muted span.
    """
    def sub(m: re.Match) -> str:
        target = m.group(1).strip()
        custom_display = m.group(2)
        # Skip raw/extracted source links (they're file refs, not concept links)
        if target.startswith("../raw/") or "raw/extracted" in target:
            return f'<span class="wikilink-source">{custom_display or target.rsplit("/", 1)[-1]}</span>'

        # Try several resolution strategies
        candidates = [target, _slugify(target)]
        # also try "type/slug" → take last
        if "/" in target:
            candidates.append(target.rsplit("/", 1)[-1])
            candidates.append(_slugify(target.rsplit("/", 1)[-1]))
        page_id = None
        for c in candidates:
            if c in slug_to_id:
                page_id = slug_to_id[c]
                break

        if not page_id:
            display = custom_display or target
            return f'<span class="wikilink-broken" title="not found">{display}</span>'

        display = custom_display or id_to_title.get(page_id, target)
        return (f'<a class="wikilink" data-page-id="{page_id}" '
                f'href="#" title="{id_to_title.get(page_id, "")}">{display}</a>')

    return WIKILINK_RE.sub(sub, body)
