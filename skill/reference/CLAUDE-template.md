# Project CLAUDE.md template

When scaffolding a new project, write a project-specific `CLAUDE.md` at the project root using this template. Replace `<PLACEHOLDERS>` with subject-specific values.

```markdown
# <Subject> Study Tutor — Schema Contract

This is an LLM-maintained study wiki for **<Subject + scope>**. It follows the
[llm-wiki](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) pattern:
the LLM incrementally builds and maintains a structured collection of markdown files
with a derived JSON knowledge graph.

## Four-Layer Architecture

1. **raw/** — Immutable source material. Original .pptx/.docx/.pdf files plus extracted/*.md text dumps.
2. **wiki/** — LLM-maintained markdown pages. **Source of truth.** YAML frontmatter + [[wikilinks]].
3. **kg/** — Derived JSON knowledge graph. Built from wiki/. Never hand-edit.
4. **This file (CLAUDE.md)** — The schema. Documents structure, conventions, operations.

## Wiki Organization

Pages organized into directories by node type:

- **chapters/** — Source chapter pages (one per source unit)
- **exam-topics/** — Study-guide bullets, learning objectives (the spine)
- **concepts/** — Broad ideas
- **terms/** — Vocabulary
- **principles/** — Laws, rules, theorems
- **people/** — Named individuals
- **comparisons/** — X vs Y discussions
<INSERT DOMAIN-SPECIFIC TYPES HERE — e.g. for biology:>
- **processes/** — Multi-step processes
- **structures/** — Physical/anatomical structures
- **molecules/** — DNA, RNA, etc.
- **enzymes/** — Catalytic proteins
<...>

## Page Format

Every wiki page uses this template:

\```markdown
---
id: <type>:<slug>
type: <one of the schema types above>
title: Page Title
slug: page-slug
aliases: []
tags: [chapter-N, ...]
status: active
created: YYYY-MM-DD
updated: YYYY-MM-DD
chapters: [N]
exam_topics: [topic-slug, ...]
---

# Page Title

## Summary
1-3 sentence summary.

## <Type-specific sections>
...

## See Also
- [[other-page]]

## Sources
- [[../raw/extracted/source-N.md#anchor]]
\```

## Knowledge Graph Build

\```bash
python3 tools/build_kg.py     # wiki/ → kg/
python3 tools/validate.py     # JSON Schema + referential integrity
python3 tools/render_index.py # regenerates wiki/index.md
\```

## Edge Relations

Edges inferred from section headings. See `tools/build_kg.py:SECTION_TO_RELATION`.

## Conventions

- File names: lowercase, hyphens, no spaces
- One concept per page
- Always include `chapters: [N]` in frontmatter
- Update `updated:` field when editing
- 5-15 wikilinks per concept page
- Spot-check coverage with `kg/indexes/coverage.json`

## Subject-specific notes

<INSERT SUBJECT-SPECIFIC NOTES HERE — e.g.:>

- Chapter mapping: <Chapter 1: ...>
- Naming conventions for type X: <e.g. processes use noun-form like "transcription" not "transcribing">
- Out-of-scope: <topics that belong to other courses, e.g. "cellular respiration is in chapters 6-8, not this exam">
```
