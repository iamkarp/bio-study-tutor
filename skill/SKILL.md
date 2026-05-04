---
name: build-study-tutor
description: Use when the user provides a folder of course or training documents (PPTX, DOCX, PDF, MD) and wants a complete interactive study tutor produced from them. Builds a hybrid wiki + knowledge graph, an LLM-grounded chat tutor, dynamic quizzes/flashcards/match games, printable PDF editions (full + compact 4-page), an interactive 2-degree-highlight knowledge graph, and a Shiny web app — all from the provided source material. Triggers on phrases like "build a study tutor for X", "turn these slides into an app", "make me a study app from these docs", "create an interactive study guide from this material", "build me a course tutor".
---

# Build a Study Tutor

This skill produces a working replica of the Bio Study Tutor stack (https://github.com/iamkarp/bio-study-tutor) for **any subject**, given a folder of source documents.

The output is a self-contained project directory with:

1. `raw/extracted/` — text dumps of every source file
2. `wiki/` — atomic Markdown pages, one per concept, cross-linked with `[[wikilinks]]`
3. `kg/` — derived JSON knowledge graph (nodes + typed edges + indexes)
4. `tools/` — extraction, KG build, validation, print, video pipelines
5. `app/` — Python Shiny app with 6 tabs: Study Guide, Ask, Quiz, Flashcards, Print, Knowledge Graph
6. `app/starter_content/` — hand-curated quizzes, flashcards, match games for instant first-launch playability
7. `print/` — two PDF-ready editions: full (one section per wiki page) and compact (4-page hand-curated)
8. Optional: deployed shinyapps.io app, demo video with TTS narration

The reference Bio Study Tutor produces ~250 wiki pages, ~1,200 typed edges, 30 hand-authored quiz questions, 60 flashcards, 36 match pairs, and a 4-page compact reference — from 5 PowerPoint chapters and a study guide, in roughly a day of automated work plus author review.

---

## When to invoke

- User points at a folder of slides/docs and says "build a tutor" / "build a study app" / "make this interactive"
- User mentions exam prep, course material, or training material and wants more than a flashcard app
- User specifically references the Bio Study Tutor pattern or wants something like it for a different subject

## When NOT to invoke

- User just wants to chat with a single PDF (use a normal RAG approach, not this skill)
- User wants raw flashcards only (Anki/Quizlet are simpler)
- User wants a polished commercial-grade product (this skill produces a working sketch, not a finished product)

---

## Using the llm-wiki and knowledge-graph patterns

The two most labor-intensive artifacts — the wiki and the knowledge graph — each have an established pattern. Use them to structure your work in Phases 1 and 4.

### The LLM-Wiki pattern (for Phase 4 — wiki authoring)

The LLM-Wiki pattern (from [Andrej Karpathy's gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)) is the authoring model this skill uses. The key principles:

1. **One Markdown file per concept.** Every page has YAML frontmatter (`id`, `type`, `slug`, `title`, `aliases`, `tags`, `status`, `chapters`, `exam_topics`). The LLM reads and writes these files incrementally — it never tries to generate everything at once.
2. **`[[wikilinks]]` are the connective tissue.** Every page that mentions a concept with its own page should link to it with `[[slug]]` syntax. The KG builder infers edges from these links.
3. **Section headings drive edge types.** The heading under which a `[[wikilink]]` appears tells the KG builder what *kind* of relationship it is (see `SECTION_TO_RELATION` in `tools/build_kg.py`). For example, a link under `## Steps` becomes a `part_of` edge; under `## Produces` becomes a `produces` edge.
4. **Author incrementally, validate continuously.** After every batch of pages, run `python3 tools/build_kg.py && python3 tools/validate.py`. Fix broken wikilinks before adding more pages.
5. **Coverage, not perfection.** The goal is one page per concept in the source material — not flawless prose. A page with a two-sentence summary and three wikilinks is better than no page at all.

To create the wiki folder structure for a new subject:
```bash
mkdir -p wiki/{chapters,exam-topics,concepts,processes,structures,<your-types>}
touch wiki/index.md wiki/log.md
```

Then author pages following `reference/wiki-authoring.md`.

### The Knowledge Graph pattern (for Phase 4 — KG build)

The knowledge graph is **derived from the wiki** — you never hand-edit `kg/`. The build pipeline:

```bash
# Build the graph from wiki/
python3 tools/build_kg.py

# Validate all edge endpoints resolve and frontmatter is well-formed
python3 tools/validate.py

# Regenerate wiki/index.md from the graph
python3 tools/render_index.py
```

The KG builder (`tools/build_kg.py`) does three things:
1. Parses every wiki page's frontmatter → creates a node in `kg/nodes/<type>/<slug>.json`
2. Scans every `[[wikilink]]` and the section it appears in → creates a typed edge in `kg/edges.jsonl`
3. Builds lookup indexes: `kg/indexes/by-chapter.json`, `by-type.json`, `alias-map.json`, `coverage.json`, `orphans.json`

**Coverage check** — run this after each authoring session:
```bash
python3 -c "import json; c=json.load(open('kg/indexes/coverage.json')); print('Uncovered exam topics:', c.get('uncovered_exam_topics', []))"
```

**Orphan check** — pages no other page links to (signals a coverage gap):
```bash
python3 -c "import json; print('Orphans:', json.load(open('kg/indexes/orphans.json')))"
```

The app reads the KG at startup (via `app/kg_loader.py`) to populate the Study Guide tab, scope quiz/flashcard generation to the right chapters, and power the knowledge graph visualization.

---

## Procedure

Follow these phases in order. Each phase has a **Goal**, **Action**, and **Verify** step. Don't skip the verifications — they catch the silent failures that kill the final result.

### Phase 0 — Intake

**Goal:** understand the subject, scope, and target.

**Action:**
1. Ask the user (use AskUserQuestion):
   - **Subject + scope** — e.g. "Bio 1320 Exam 3", "Calculus II Midterm 2", "AWS Solutions Architect cert prep"
   - **Source location** — absolute path to the folder of documents
   - **Project name (slug)** — kebab-case, e.g. `bio-1320-exam-3`. This becomes the directory name and the shinyapps.io app name.
   - **Deployment target** — local only / shinyapps.io / both
   - **LLM backend** — how should the chat tutor and game generator call an LLM? Choose one:
     - **LM Studio** (local, free, private) — set `LMSTUDIO_URL=http://localhost:1234/v1` in `.env`. Start LM Studio, load any model, enable the local server.
     - **Ollama** (local, free, private) — set `OLLAMA_URL=http://localhost:11434/v1` and `OLLAMA_MODEL=gemma4:26b` (or `gemma4:9b` for 16 GB RAM).
     - **Claude via Anthropic API** — set `ANTHROPIC_API_KEY=sk-ant-...` in `.env`. Set `LLM_MODEL=claude-sonnet-4-6` or any Claude model id.
     - **Claude Code CLI** (no API key) — set `CLAUDE_CODE_CLI=1`. Uses the current Claude Code session. Requires `claude` CLI installed and authenticated.
     - **OpenRouter** (hosted, many models) — set `OPENROUTER_API_KEY=sk-or-v1-...`. Free tier available at https://openrouter.ai/keys. Default model: `google/gemma-4-26b-a4b-it`.
   - Confirm which `.env` key(s) the user has available.

2. List the source folder. Identify file types (PPTX, DOCX, PDF, MD, etc.). Flag any unsupported formats.

**Verify:** you have a clear scope, a source folder with at least one supported file, the user has confirmed the project slug, and the LLM backend is known.

### Phase 1 — Schema design

**Goal:** decide the node-type schema for this subject.

The bio app uses 16 node types tuned for biology. Other subjects need different types. **Read `reference/schema-design.md`** for the universal core (8 types) and domain-specific extensions for math, chemistry, history, programming, law, medicine, business, languages.

**Action:**
1. Read 1–2 sample source files to identify what kinds of "things" the material covers. (Concepts? Theorems? Reactions? Events? Historical figures? Vocabulary? Procedures?)
2. Propose a schema: 8 universal types + 3–6 domain-specific. Show the user the proposed type list with examples from their material.
3. Get user approval (AskUserQuestion or just summarize-and-confirm).

**Verify:** the schema feels natural for the subject — every concept in 2–3 sample source files maps cleanly to exactly one type.

### Phase 2 — Project scaffold

**Goal:** create the project directory with copied template files.

The `templates/` directory of this skill contains the reference Bio Study Tutor source. **Read `reference/templates-manifest.md`** for the complete file list and what each does.

**Action:**
1. Create the directory tree:
   ```
   <project_slug>/
   ├── raw/extracted/
   ├── wiki/<one subdir per node type>/
   ├── kg/{schema,nodes,indexes,overlays,proposed}/
   ├── tools/extract/
   ├── app/{www,starter_content}/
   ├── print/
   └── video/{audio,parts}/
   ```
2. Copy these template files **verbatim** (they're domain-agnostic):
   - `tools/extract_pptx.py`, `tools/extract_docx.py`
   - `tools/extract/{frontmatter,sections,tables,wikilinks}.py` + `__init__.py`
   - `tools/validate.py`, `tools/render_index.py`
   - `tools/build_video.py`
   - `app/{__init__,kg_loader,llm,games,graph_viz,wikilink}.py`
   - `app/prebuild.py`
   - `.python-version`, `.rscignore`, `.gitignore`, `.env.example`

3. Create the `.env` file based on the backend the user confirmed in Phase 0:
   ```bash
   cp .env.example .env
   # then edit .env — uncomment ONE backend block and fill in credentials
   ```
   Test the backend immediately:
   ```bash
   python3 -c "from app.llm import chat; print(chat([{'role':'user','content':'say hello'}]))"
   ```
   If that succeeds, the LLM backend is wired. If it fails, fix `.env` before continuing.

4. Copy these template files **with subject-specific edits**:
   - `tools/build_kg.py` — update `NODE_TYPES`, `EDGE_RELATIONS`, and the `SECTION_TO_RELATION` mapping for the chosen schema
   - `app/app.py` — update the `CHAPTER_TITLES`, type colors in `TYPE_COLORS`, navbar title (logo path + subject name), starter-content paths
   - `tools/build_print_version.py` — update `TYPE_ORDER`, `CHAPTER_LABELS`
   - `app/graph_viz.py` — update `TYPE_COLORS` to include any new node types

4. Write the schema files: `kg/schema/node.base.schema.json` and `kg/schema/edge.schema.json` with the new type/relation enums.

5. Write a project-specific `CLAUDE.md` documenting the schema (use `reference/CLAUDE-template.md` as starting point).

**Verify:**
```bash
python3 -c "import sys; sys.path.insert(0, 'app'); import ast; ast.parse(open('app/app.py').read()); print('OK')"
python3 tools/build_kg.py --help  # smoke test
```

### Phase 3 — Source extraction

**Goal:** convert source documents to plain Markdown the wiki author (you) can read.

**Action:**
1. Place the user's source files into `<project_slug>/raw/`.
2. Run extractors:
   ```bash
   python3 tools/extract_pptx.py
   python3 tools/extract_docx.py
   ```
   For PDFs, use `pdftotext` or `pypdf` (write a small `extract_pdf.py` if needed — see `reference/pdf-extraction.md`).

3. Inspect every output file (`raw/extracted/*.md`). Each should have a `## Slide N` or `## Section N` anchor structure, contain readable text, and not be empty.

**Verify:** `wc -l raw/extracted/*.md` shows non-trivial line counts (typically 200+ lines per chapter).

### Phase 4 — Wiki authoring (the substantial step)

**Goal:** produce one Markdown page per concept with consistent frontmatter and `[[wikilinks]]`.

This is the most labor-intensive step. **Read `reference/wiki-authoring.md`** for the full procedure including the page template, the canonical section order, and the wiki-link discipline.

**Action:**
1. **If a study guide / syllabus / exam topics list exists** (signal of importance), author exam-topic / topic pages first — these are the "spine" of the wiki. One page per study-guide bullet.
2. **Walk each chapter slide-by-slide.** For every bolded term, named structure/process/person, diagram label, comparison, or principle, create or update a page.
3. **Use the canonical page template** in `reference/wiki-authoring.md` — frontmatter + Summary + Key Facts + (type-specific sections) + Sources.
4. **Cross-link aggressively.** Every term that has its own page should appear as a `[[wikilink]]` in pages that mention it.
5. **Track coverage as you go:**
   - Every chapter should produce at least one chapter-overview page.
   - Every study-guide bullet should produce one exam-topic page.
   - The set of pages of each type should feel complete (no obvious gap like "we wrote 30 enzymes but the slides mention 35").

For scale, the bio app produced 254 pages across 16 types. A typical undergraduate course chapter set produces **150–300 atomic pages**.

**Verify:**
```bash
python3 tools/build_kg.py
python3 tools/validate.py     # exits 0 if every edge endpoint resolves
python3 tools/render_index.py # produces wiki/index.md
```
Inspect `kg/manifest.json` for non-zero counts in every node type. Inspect `kg/indexes/coverage.json` for any uncovered exam topics.

### Phase 5 — Starter content

**Goal:** hand-author quiz/flashcard/match-game starter sets for instant first-launch playability.

**Action:**
Hand-write into `app/starter_content/`:
- `quizzes.json` — 6 quiz packs × 5 multiple-choice questions = 30 questions
- `flashcards.json` — 6 decks × 10 cards = 60 cards
- `match.json` — 6 match games × 6 term/definition pairs = 36 pairs

**Read `reference/starter-content-template.md`** for the JSON schemas with examples.

The reference Bio app's hand-authored starter content is a useful comparison point — clear, tight, exam-relevant. Avoid generic LLM-generated content here; the starter set is what users see first and sets the bar for the whole app's perceived quality.

**Verify:**
```bash
python3 -c "import json; [json.load(open(f'app/starter_content/{f}.json')) for f in ['quizzes', 'flashcards', 'match']]"
```

### Phase 6 — Print editions

**Goal:** produce both PDF-ready printable editions with internal hyperlinks.

**Action:**
1. **Full edition** — handled by the script: `python3 tools/build_print_version.py` walks every wiki page in `(chapter, type, title)` order, assigns sequential section numbers §1 → §N, replaces `[[wikilinks]]` with `<a href="#sec-N">…[§N]</a>` references, emits `print/study-guide.html` with a TOC, body, and alphabetical index.
2. **Compact 4-page edition** — hand-author this. The reference bio app's `print/study-guide-compact.html` is your template (see `templates/study-guide-compact.template.html`). The structure is:
   - 2-column layout, 8.5pt serif, 0.45" margins
   - 4 pages × ~25 numbered facts (§1–§N) ≈ 90–100 facts
   - Each fact is one short paragraph with bold term name, content, optional inline `<a href="#sec-N">` cross-references
   - Mnemonics (`<div class="mnemonic">`) and "don't confuse" callouts (`<div class="callout">`) where useful
   - Title page → 4 dense pages → no full TOC (it's only 4 pages, the headings are enough)

**Verify:**
- Open both HTMLs in a browser and check the Print preview shows page breaks correctly.
- `grep -cE 'id="sec-' print/study-guide.html` should equal the number of sections in the full edition.
- The compact edition should fit in exactly 4 pages when printed at default zoom.

### Phase 7 — App test

**Goal:** local Shiny app runs without errors and all 6 tabs render content.

**Action:**
```bash
pkill -f "shiny run" 2>/dev/null
python3 -m shiny run --port 8765 app/app.py &
sleep 4
curl -sf http://localhost:8765/ -o /dev/null -w "HTTP %{http_code}\n"
```

If HTTP 200, browse to http://localhost:8765/ and verify each tab:
- **Study Guide** — list of cards renders for the default chapter; clicking a card opens detail view; clicking a `[[wikilink]]` in a body navigates within the app
- **Ask** — answer to a basic question grounded in the wiki
- **Quiz** — first starter quiz renders with 4 clickable choice buttons; clicking one shows correct/wrong and explanation
- **Flashcards** — first card renders front side; click to flip
- **Match Game** — terms + definitions in two columns; click pairs to match
- **Print** — both "Open compact 4-page version" and "Open full version" links work
- **Knowledge Graph** — graph renders with nodes/edges; clicking a node highlights 2-degree neighbors

**Verify:** all 6 tabs work. If anything fails, see `reference/troubleshooting.md`.

### Phase 8 — Optional: deploy

**Goal:** push to shinyapps.io.

**Action (only if user wants deployment):**
**Read `reference/deployment.md`** for the full recipe (`.python-version` to 3.11, manifest editing, `rsconnect deploy manifest`).

Critical reminders:
- shinyapps.io does NOT support Python 3.14 — use 3.11.
- The package shim `app/__init__.py` exposes `app.app`; the manifest entrypoint must be `app`.
- Use **relative** paths in HTML links (`href="print-static/..."`, not `/print-static/...`) — shinyapps.io serves under a subpath and absolute paths break.
- Exclude `.env` from the deployment via `.rscignore` if it contains a secret; set `OPENROUTER_API_KEY` as an env var in the shinyapps.io dashboard instead.

### Phase 9 — Optional: demo video

**Goal:** produce an interview-style video tour with TTS narration.

**Action (only if user wants a video):**
Use `tools/build_video.py` (already copied as a template). Customize the `SCRIPT` list of `Seg(speaker, text, screenshot)` tuples for the new subject. Voices `en-US-AvaNeural` (female interviewer) and `en-US-AndrewNeural` (male interviewee) work well via `edge-tts` (free, no API key needed).

Required input: 8 screenshots in `screenshots/` (one per tab/feature), captured by the user via cmd+shift+4 or similar.

---

## Critical references

- **`reference/architecture.md`** — the 4-layer architecture (raw → wiki → kg → app) and why each layer matters
- **`reference/schema-design.md`** — universal node types + domain-specific extensions (math, chem, history, etc.)
- **`reference/wiki-authoring.md`** — the page template, section conventions, wikilink discipline, and authoring tips
- **`reference/templates-manifest.md`** — what each file in `templates/` does
- **`reference/starter-content-template.md`** — JSON schemas for quizzes, flashcards, match games
- **`reference/deployment.md`** — shinyapps.io recipe with all the gotchas
- **`reference/troubleshooting.md`** — known failure modes and fixes

## Cost & time estimate

Built end-to-end for a typical undergraduate chapter set (5 chapters, ~50 slides each, +1 study guide):

| Phase | Time (Claude time) | LLM tokens (rough) |
|---|---|---|
| 0–2: intake, schema, scaffold | 15 min | 15k |
| 3: extraction | 5 min | (no LLM) |
| 4: wiki authoring | 4–8 hours | 800k–1.5M |
| 5: starter content | 30–60 min | 50k |
| 6: compact print | 30–45 min | 50k |
| 7–8: test + deploy | 15 min | (no LLM) |
| 9: video (optional) | 15 min + screenshots | (no LLM, edge-tts free) |

**Total tokens**: ~1M context (use Sonnet/Haiku for cost). **Total real time**: a focused day for a single course.

## Quality bar

The output should pass these tests:
1. A student looking at the Study Guide tab can find any term they remember from class and read a useful page about it.
2. The Ask tab answers a question correctly and never invents content not in the wiki.
3. The first quiz pack has zero wrong answers (i.e. the marked-correct option really is correct per the source material).
4. The compact 4-page print fits in 4 pages and contains the highest-leverage facts only.
5. Clicking a node in the Knowledge Graph immediately reveals its conceptual neighborhood.

If any of these fail, the issue is upstream: insufficient wiki coverage (Phase 4), low-quality starter content (Phase 5), or schema mismatch (Phase 1).
