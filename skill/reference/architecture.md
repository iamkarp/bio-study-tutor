# Architecture: the four layers

The study tutor is built on a strict separation of layers. Each layer is the single source of truth for one concern, and downstream layers are derived from upstream ones.

```
raw/        →  wiki/        →  kg/         →  app/
sources       human-readable   machine-      runtime UI
              source of truth  queryable     + features
```

## Layer 1 — `raw/`

Original course/training material. **Never modify this layer.** Files live at `raw/*.{pptx,docx,pdf,md}`. Per-source markdown text dumps live at `raw/extracted/*.md`, produced by `tools/extract_pptx.py`, `tools/extract_docx.py`, etc. Each extracted file preserves slide/section anchors (e.g. `## Slide 12 {#slide-12}`) so wiki pages can cite back to specific source locations.

**Why this matters**: when the wiki claims "DNA polymerase III adds nucleotides 5'→3' and proofreads," a reader can grep `raw/extracted/` to verify the slides actually said that. Auditability.

## Layer 2 — `wiki/`

Atomic Markdown pages, one per concept. **This is the single source of truth.** Every page has YAML frontmatter and uses `[[wikilink]]` syntax for cross-references:

```markdown
---
id: process:meiosis
type: process
title: Meiosis
slug: meiosis
chapters: [9]
exam_topics: [full-meiosis-process]
---

## Summary
Meiosis is the form of cell division that produces **haploid gametes**...

## Steps
1. [[processes/meiosis-i]] — separates homologous pairs
2. [[processes/meiosis-ii]] — separates sister chromatids
```

**Pages are organized into directories by node type**: `wiki/processes/`, `wiki/structures/`, `wiki/molecules/`, etc. Plus a few special locations:
- `wiki/index.md` — full catalog (auto-generated)
- `wiki/overview.md` — high-level map (hand-authored)
- `wiki/log.md` — change log (hand-authored)

**Why this matters**: humans can read, edit, and improve the wiki directly. An instructor reviewing the material sees a familiar text artifact, not a database. Every claim is reviewable in plain prose.

## Layer 3 — `kg/`

Typed JSON knowledge graph **derived from wiki/** by `tools/build_kg.py`. **Never hand-edit this layer.** Just rebuild.

- `kg/nodes/<type>/<slug>.json` — one file per node, per type
- `kg/edges.jsonl` — one typed edge per line, with provenance
- `kg/indexes/*.json` — derived lookups (by-type, by-tag, by-chapter, backlinks, alias-map, orphans, coverage)
- `kg/manifest.json` — build metadata (counts, hash)

Edge types are inferred from the section a wikilink appears in:
- Link inside `## Steps` or `## Components` → `part_of`
- Link inside `## Sources` → `cites`
- Link inside `## Compared To` → `compared_to`
- Link inside `## Causes` / `## Caused By` → `causes` / `caused_by`
- Link inside `## Related` → `related_to`

The full mapping lives in `tools/build_kg.py` as `SECTION_TO_RELATION`.

**Why this matters**: structured queries become trivial. "Which enzymes catalyze which processes?" "Show me every page in chapter 11." "What does this concept depend on?" All are simple JSON / jq queries — no LLM call required.

## Layer 4 — `app/`

The Python Shiny web app that serves all six tabs. **Reads from `wiki/` and `kg/` at startup; never writes back.** The split between the wiki+KG and the app is deliberate: the same wiki+KG could power a CLI tool, a static site, a Discord bot, etc.

Key modules:
- `app/app.py` — UI (6 tabs) + reactive logic
- `app/kg_loader.py` — loads wiki pages and KG into memory, builds slug-to-id maps
- `app/llm.py` — OpenRouter client (RAG with wiki as context)
- `app/games.py` — quiz/flashcard/match generators (LLM-driven JSON-mode calls)
- `app/graph_viz.py` — PyVis graph rendering with click-to-highlight 2-degree neighbors
- `app/wikilink.py` — `[[wikilink]]` → clickable HTML anchor resolution
- `app/starter_content/*.json` — pre-authored quiz/flashcard/match starters

## Why this layered approach matters

**For humans**: they edit and read prose, not JSON. The wiki stays useful even if you turn off the app and the LLM.

**For machines**: they query a typed graph, not free text. Coverage gaps, broken cross-references, and orphaned pages are detectable mechanically (`kg/indexes/orphans.json`, `kg/indexes/coverage.json`).

**For the build**: each layer can be regenerated cheaply from the previous one. Edit a wiki page, rerun `tools/build_kg.py`, and every downstream artifact (graph, indexes, print editions, app data) updates consistently.

**For trust**: when the LLM tutor answers a question, it cites the wiki page. When the wiki page makes a claim, it cites the source slide. Every output has a verifiable chain back to authored material.
