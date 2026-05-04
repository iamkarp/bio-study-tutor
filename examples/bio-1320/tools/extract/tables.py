"""Parse markdown tables into list[dict[str,str]]."""
from __future__ import annotations

import re

ROW_RE = re.compile(r"^\s*\|(.+)\|\s*$")
SEP_RE = re.compile(r"^\s*\|?\s*:?-{2,}.*$")


def parse_tables(text: str) -> list[list[dict[str, str]]]:
    lines = text.splitlines()
    tables: list[list[dict[str, str]]] = []
    i = 0
    while i < len(lines):
        m = ROW_RE.match(lines[i])
        if m and i + 1 < len(lines) and SEP_RE.match(lines[i + 1]):
            headers = [c.strip() for c in m.group(1).split("|")]
            rows: list[dict[str, str]] = []
            j = i + 2
            while j < len(lines):
                rm = ROW_RE.match(lines[j])
                if not rm:
                    break
                cells = [c.strip() for c in rm.group(1).split("|")]
                cells = (cells + [""] * len(headers))[: len(headers)]
                rows.append(dict(zip(headers, cells)))
                j += 1
            if rows:
                tables.append(rows)
            i = j
        else:
            i += 1
    return tables


def strip_md(s: str) -> str:
    s = re.sub(r"\*\*(.+?)\*\*", r"\1", s)
    s = re.sub(r"\*(.+?)\*", r"\1", s)
    s = re.sub(r"`(.+?)`", r"\1", s)
    s = re.sub(r"\[\[(.+?)\]\]", r"\1", s)
    s = re.sub(r"\[(.+?)\]\(.+?\)", r"\1", s)
    return s.strip()
