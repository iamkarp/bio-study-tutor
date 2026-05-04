# Bio 1320 Exam 3 Hybrid Wiki + Knowledge Graph — Schema

This is an LLM-maintained study wiki for Biology 1320 Exam 3 (Chapters 9–13). It follows the
[llm-wiki](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) pattern: the LLM
incrementally builds and maintains a structured collection of markdown files with a derived JSON
knowledge graph.

## Four-Layer Architecture

1. **raw/** — Immutable source material. Original `.pptx` and `.docx` files plus `extracted/*.md`
   text dumps. The LLM reads but never modifies these.

2. **wiki/** — LLM-maintained markdown pages organized by node type. **Source of truth.**
   Every page has YAML frontmatter. Cross-references use `[[wiki-links]]`.

3. **kg/** — Typed JSON knowledge graph **derived from wiki/** by `tools/build_kg.py`.
   `kg/nodes/<type>/<slug>.json` is one file per node; `kg/edges.jsonl` is one typed edge per line;
   `kg/indexes/*.json` are derived lookups. **Never hand-edit kg/** — re-run the builder.

4. **This file (CLAUDE.md)** — The schema. Documents structure, conventions, and operations.

## Wiki Organization

- **chapters/** — One page per source chapter (9–13) plus the study guide.
- **exam-topics/** — One page per study-guide bullet. **The spine.**
- **processes/** — Biological processes (meiosis, DNA replication, transcription, translation, …).
- **structures/** — Physical/anatomical structures (chromosome, ribosome, double helix, …).
- **molecules/** — DNA, RNA, mRNA/tRNA/rRNA, codon, amino acids, …
- **enzymes/** — DNA polymerase, RNA polymerase, helicase, ligase, …
- **terms/** — Vocabulary (allele, homozygous, phenotype, …).
- **inheritance/** — Inheritance patterns (incomplete dominance, codominance, sex-linked, …).
- **experiments/** — Mendel pea, Griffith.
- **people/** — Mendel, Mullis.
- **diseases/** — Sickle cell, cystic fibrosis, Down syndrome, …
- **techniques/** — Punnett square, PCR, gel electrophoresis, DNA sequencing, STR analysis.
- **principles/** — Mendel's laws, base pairing, central dogma, genetic code.
- **comparisons/** — Mitosis vs. meiosis, DNA vs. RNA, transcription vs. translation, …
- **concepts/** — Catch-all for ideas that don't fit other types.

## Page Format

```markdown
---
id: <type>:<slug>
type: chapter|exam_topic|concept|process|structure|molecule|enzyme|term|
      inheritance_pattern|experiment|person|disease|technique|principle|
      comparison|source
title: Page Title
slug: page-slug
aliases: []
tags: [tag1, tag2]
status: active
created: YYYY-MM-DD
updated: YYYY-MM-DD
chapters: [9, 10]              # which source chapter(s) it came from
exam_topics: [topic-slug, ...] # which exam-topic pages this is covered by
---

# Page Title

## Summary
1–3 sentence plain-English summary.

## Key Facts / Details / Steps / Components / Catalyzes / ...
Section headings drive edge inference (see SECTION_TO_RELATION in tools/build_kg.py).
Use `[[wiki-links]]` liberally.

## Sources
- [[../raw/extracted/chapter-XX-...]] slide N
```

## Section → Edge Relation

The builder infers edge relations from the section a [[wikilink]] appears in. Examples:
- `## Steps` / `## Components` → `part_of`
- `## Produces` → `produces`
- `## Catalyzes` → `catalyzes`
- `## Causes` / `## Caused By` → `causes` / `caused_by`
- `## Demonstrates` → `demonstrates`
- `## Compared To` → `compared_to`
- `## Related` → `related_to`
- `## Sources` → `cites`
- `## Covers` (on exam_topic pages) → `covers`

See `SECTION_TO_RELATION` in `tools/build_kg.py` for the full mapping.

## Operations

### Build KG
```bash
python3 tools/build_kg.py
python3 tools/validate.py
python3 tools/render_index.py
```

### Add a New Source
1. Drop the `.pptx` or `.docx` into `raw/` (not into `raw/extracted/`).
2. Run `python3 tools/extract_pptx.py` (or `extract_docx.py`).
3. Update or create relevant wiki pages.
4. Run the build pipeline above.
5. Append a line to `wiki/log.md`.

### Conventions
- File names: lowercase, hyphenated, no spaces.
- One concept per page. Prefer atomic granularity.
- Always include `chapters: [N]` so coverage is auditable.
- Update `updated:` whenever you edit a page.

## Audit / Coverage

- `kg/indexes/coverage.json` — terms in `raw/extracted/` not yet in the KG, and exam topics with no `covers` edges.
- `kg/indexes/orphans.json` — wiki pages with no inbound links.
- `kg/indexes/by-chapter.json` — confirm every chapter has node entries.
