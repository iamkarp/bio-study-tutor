# Wiki authoring — page template, sections, wikilink discipline

This is the labor-intensive step. Quality of the wiki determines quality of every downstream artifact (chat answers, quiz questions, print editions, graph visualization). Don't shortcut it.

## The page template

Every page has YAML frontmatter + body sections in this canonical order:

```markdown
---
id: <type>:<slug>
type: <node_type>          # one of the schema types
title: <Human Readable Title>
slug: <kebab-case-slug>
aliases: ["alternate name", "abbreviation"]   # optional
tags: [chapter-09, foo, bar]                  # optional
status: active
created: YYYY-MM-DD
updated: YYYY-MM-DD
chapters: [9]              # primary chapter(s) this page belongs to
exam_topics: [meiosis-overview, crossing-over]  # study-guide bullets this answers
---

## Summary
1–3 sentence plain-English summary. Bold key terms. Use [[wikilinks]] for related concepts.

## Key Facts                # generic content section
- Bullet point 1
- Bullet point 2

## Steps                    # processes only — numbered list of [[wikilinks]]
1. [[step-one]]
2. [[step-two]]

## Compared To              # for comparisons
- [[other-concept]]

## Related                  # general cross-references
- [[concept-one]] — why related
- [[concept-two]] — why related

## Sources
- [[../raw/extracted/chapter-09-name.md#slide-12]] — where this is covered
```

## Section heading conventions

The KG builder infers edge types from section headings. The mapping (in `tools/build_kg.py`'s `SECTION_TO_RELATION`):

| Section heading | Inferred edge | Use when... |
|---|---|---|
| `## Summary` | `mentioned_in` | Always include. 1-3 sentences. |
| `## Key Facts` / `## Details` | `mentioned_in` | Bulleted facts. |
| `## Steps` / `## Phases` / `## Stages` | `part_of` | Sequential process steps. |
| `## Components` / `## Consists Of` | `part_of` | Compound structure breakdown. |
| `## Produces` / `## Products` | `produces` | Outputs of a process. |
| `## Catalyzes` | `catalyzes` | Enzyme catalyzing a process. |
| `## Causes` / `## Caused By` | `causes` / `caused_by` | Causal relationships. |
| `## Located In` / `## Occurs In` | `located_in` | Spatial / contextual location. |
| `## Demonstrates` / `## Demonstrated By` | `demonstrates` | Experiment proving a principle. |
| `## Discovered By` | `discovered_by` | Person discovered this. |
| `## Compared To` | `compared_to` | For comparison-type pages. |
| `## Examples` / `## Example` | `example_of` | Concrete instances. |
| `## Covers` / `## Exam Relevance` | `covers` | What exam topics this answers. |
| `## See Also` / `## Related` | `related_to` | Soft cross-references. |
| `## Sources` | `cites` | Source citations. |
| `## Gotchas` / `## Common Confusions` | `related_to` | Edge cases, traps. |

Use the canonical names. If you invent a new section heading, the builder will fall back to `related_to` (which is fine, just less specific).

## Wikilink discipline

Use `[[slug]]` to link to another page. The builder resolves slugs in this order:
1. Exact slug match (`crossing-over` → `process:crossing-over`)
2. Path-style (`processes/crossing-over` → drops the prefix, looks up `crossing-over`)
3. Aliases (any string in another page's `aliases:` list)
4. Slugified form of the target (case-insensitive, kebabbed)

**Discipline rules**:
1. **First mention rule** — the first time a term with its own page appears in a body, link it. Subsequent mentions in the same paragraph don't need to be re-linked.
2. **Don't link the page's own title** — `meiosis.md` shouldn't contain `[[meiosis]]`.
3. **Use `[[target|display]]` to override the link text**: `see [[principles/law-of-segregation|Mendel's first law]]`.
4. **Source links use raw paths**: `[[../raw/extracted/chapter-09.md#slide-12]]` — these get treated as `cites` edges.
5. **Aim for 5–15 wikilinks per concept page**. Less means the page is isolated; more means it's a spaghetti of references.

## Authoring procedure

The order matters. Build in this sequence to maximize cross-link density:

1. **Chapter-overview pages first** (one per chapter). These are the highest-level table of contents.
2. **Exam-topic pages** (one per study-guide bullet). The "spine" — these define what the exam actually covers.
3. **Atomic content pages** type by type:
   - Principles / laws / theorems (foundational claims)
   - Experiments (historical context for principles)
   - Processes / mechanisms (multi-step things)
   - Structures / objects (anatomical, physical, conceptual)
   - Molecules / particles / agents (the "stuff")
   - Enzymes / actors / techniques (the "doers")
   - Inheritance patterns / classifications
   - Diseases / cases / phenomena
   - People (scientists, authors, historical figures)
   - Comparisons (X vs Y)
   - Concepts (catch-all)
   - Terms / vocabulary (last — these are usually short)

Within each type, walk the source slides linearly and write a page for every named entity.

## Quality bar per page

Each page should:
- **Stand alone** — make sense without context
- **Cite its source** — `## Sources` lists at least one slide-anchor reference
- **Cross-link 5–15 times** — into other concepts
- **Be exam-relevant** — connect back to at least one `exam_topic` (either via `exam_topics:` frontmatter or a `[[wikilink]]` from the body)
- **Be tight** — concept page bodies are typically 80–250 words. Overview pages can be longer.

## Coverage checks

After each major batch (e.g. finishing a chapter), run:
```bash
python3 tools/build_kg.py
python3 tools/validate.py
```

Inspect:
- `kg/manifest.json` — node counts per type. If `enzyme: 1` after chapter 11 but the chapter mentions 7 enzymes, you missed pages.
- `kg/indexes/orphans.json` — pages with no inbound links. Sometimes legitimate (a chapter overview page); often a sign the page should be referenced from something else.
- `kg/indexes/coverage.json` — every exam-topic page with zero outbound `covers` edges. These are study-guide bullets you haven't actually covered yet.
- `kg/indexes/coverage.json` `uncovered_terms_in_raw` — bolded terms in the slides that never made it into the wiki. Audit this list and decide which to add.

## When to stop

The wiki is "done" when:
1. Every study-guide bullet has a covering exam-topic page.
2. Every chapter has a chapter-overview page that links to its key concepts.
3. The orphan list is short (≤10–15) and every orphan is justifiable (chapter overviews, hub pages, etc.).
4. Spot-checking: pick 3 random terms from the source slides. Each should have its own page or be explicitly mentioned in another page.

For a 5-chapter undergraduate course set, this is typically **150–300 atomic pages**.
