"""Split a markdown body into H2/H3 sections keyed by heading text."""
from __future__ import annotations

import re
from typing import OrderedDict

HEADING_RE = re.compile(r"^(#{2,3})\s+(.+?)\s*$", re.MULTILINE)


def split_sections(body: str) -> "OrderedDict[str, str]":
    sections: "OrderedDict[str, str]" = OrderedDict()
    sections[""] = ""

    matches = list(HEADING_RE.finditer(body))
    if not matches:
        sections[""] = body
        return sections

    sections[""] = body[: matches[0].start()].strip()

    current_key = ""
    for i, m in enumerate(matches):
        level, heading = m.group(1), m.group(2).strip()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(body)
        content = body[m.end() : end].strip()
        if level == "##":
            current_key = heading
            sections[current_key] = content
        else:
            existing = sections.get(current_key, "")
            sections[current_key] = (existing + f"\n\n### {heading}\n\n{content}").strip()
    return sections


# Section heading → canonical key. Drives edge inference (see SECTION_TO_RELATION in build_kg).
SECTION_ALIASES: dict[str, str] = {
    "summary": "summary",
    "what it is": "summary",
    "key facts": "key_facts",
    "key facts / details": "key_facts",
    "details": "key_facts",
    "steps": "steps",
    "steps / phases": "steps",
    "phases": "steps",
    "stages": "steps",
    "process": "steps",
    "components": "components",
    "structure": "components",
    "consists of": "components",
    "made of": "components",
    "produces": "produces",
    "products": "produces",
    "output": "produces",
    "produced by": "produced_by",
    "catalyzes": "catalyzes",
    "catalyzed by": "catalyzed_by",
    "causes": "causes",
    "caused by": "caused_by",
    "regulates": "regulates",
    "regulated by": "regulated_by",
    "located in": "located_in",
    "occurs in": "located_in",
    "found in": "located_in",
    "demonstrates": "demonstrates",
    "demonstrated by": "demonstrated_by",
    "discovered by": "discovered_by",
    "proposed by": "discovered_by",
    "compared to": "compared_to",
    "comparison": "compared_to",
    "examples": "example_of",
    "example": "example_of",
    "covers": "covers",
    "exam relevance": "covers",
    "why it matters": "covers",
    "why it matters / exam relevance": "covers",
    "see also": "related",
    "related": "related",
    "sources": "sources",
    "gotchas": "gotchas",
    "mistakes": "gotchas",
    "common confusions": "gotchas",
    "requires": "requires",
    "prerequisites": "requires",
    "contradicts": "contradicts",
    "supersedes": "supersedes",
    "instance of": "instance_of",
    "type of": "instance_of",
    "is a": "instance_of",
}


def section_aliases(name: str) -> str:
    n = name.lower().strip()
    if n in SECTION_ALIASES:
        return SECTION_ALIASES[n]
    return n.replace(" ", "_").replace("'", "").replace("/", "_")
