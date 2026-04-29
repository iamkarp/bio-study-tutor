# Bio 1320 Exam 3 — Hybrid Wiki + Knowledge Graph

A structured, queryable study guide for Biology 1320 Exam 3 (Chapters 9–13: Meiosis, Inheritance, DNA Structure & Replication, How Genes Work, New Biology). Built from the official PowerPoints and study guide using the [llm-wiki](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) pattern.

## What This Is

Two layers, one source of truth:

1. **`wiki/`** — Human-readable markdown. Each concept, term, process, person, etc. has its own atomic page, cross-linked with `[[wiki-links]]`. Read it like a study guide; navigate it like a wiki.
2. **`kg/`** — Auto-derived JSON knowledge graph. Every wiki page becomes a typed **node**; every wikilink becomes a typed **edge**. Use it for graph queries — "which enzymes catalyze which processes?", "every page that mentions Mendel", etc.

The wiki is the source of truth. The KG is built from the wiki by `python3 tools/build_kg.py` and is fully reproducible.

## Layout

```
Study/
├── CLAUDE.md         ← schema contract (read this first if editing)
├── README.md         ← this file
│
├── raw/              ← source material (not edited)
│   ├── *.pptx        ← chapter slide decks
│   ├── *.docx        ← study guide
│   └── extracted/    ← per-slide markdown dumps
│
├── wiki/             ← human-readable, single source of truth
│   ├── index.md      ← auto-rendered catalog
│   ├── overview.md   ← high-level map
│   ├── log.md        ← change history
│   ├── chapters/     ← chapter source pages
│   ├── exam-topics/  ← one page per study-guide bullet (the spine)
│   ├── processes/, structures/, molecules/, enzymes/, terms/,
│   ├── inheritance/, experiments/, people/, diseases/,
│   └── techniques/, principles/, comparisons/, concepts/
│
├── kg/               ← BUILD OUTPUT — never hand-edit
│   ├── schema/       ← JSON Schemas
│   ├── nodes/<type>/*.json
│   ├── edges.jsonl
│   ├── indexes/      ← by-type, by-tag, by-chapter, backlinks, orphans, coverage
│   ├── manifest.json
│   └── build.log
│
└── tools/
    ├── extract_pptx.py / extract_docx.py
    ├── build_kg.py
    ├── validate.py
    └── render_index.py
```

## Quick Start — How to Study

1. Open [`wiki/index.md`](wiki/index.md) to see the full catalog by chapter and by type.
2. Open [`wiki/overview.md`](wiki/overview.md) for a high-level map of the exam.
3. Walk the **exam-topic** pages in [`wiki/exam-topics/`](wiki/exam-topics/) — one per study-guide bullet. Each is a Q & A with links to the underlying concept pages.
4. Drill into any wikilink to read the supporting concept, term, process, or enzyme page.
5. Cross-reference with the chapter pages in `wiki/chapters/` for breadth.

## Quick Start — How to Query the Graph

```bash
# Rebuild the KG from the wiki (run after editing any wiki/*.md):
python3 tools/build_kg.py
python3 tools/validate.py
python3 tools/render_index.py

# Then ask questions of the JSON output:

# Every enzyme:
ls kg/nodes/enzyme/

# Every page in chapter 11:
cat kg/indexes/by-chapter.json | jq '.["11"]'

# Every "catalyzes" edge:
grep '"catalyzes"' kg/edges.jsonl

# Which exam topics cover crossing-over?
grep '"target": "process:crossing-over"' kg/edges.jsonl | grep '"covers"'

# What's mentioned in the sickle-cell page?
cat kg/indexes/backlinks.json | jq '.["disease:sickle-cell-anemia"]'
```

## Adding to the Wiki

1. Drop new source files into `raw/`.
2. Run the appropriate extractor (`tools/extract_pptx.py` or `tools/extract_docx.py`).
3. Read the extracted markdown; create/update wiki pages following the template in `CLAUDE.md`.
4. Run `python3 tools/build_kg.py && python3 tools/validate.py`.
5. Append an entry to `wiki/log.md`.

See [`CLAUDE.md`](CLAUDE.md) for the full schema and conventions.

## Stats

| Category | Count |
|---|---|
| Chapters | 5 (plus the study guide) |
| Exam topics (study-guide spine) | 38 |
| Atomic content pages | ~125 |
| Total wiki pages | ~170 |
| Node types | 16 |
| Edge relations | 31 |
