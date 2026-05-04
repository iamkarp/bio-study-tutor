# build-study-tutor

> A Claude Code skill that turns any folder of course materials into a complete, private, offline-capable interactive study tutor — grounded in a hand-authored wiki and a typed knowledge graph.

| | |
|---|---|
| **Install** | Copy [`skill/`](skill/) → `~/.claude/skills/build-study-tutor/` |
| **Skill file** | [`skill/SKILL.md`](skill/SKILL.md) — 9-phase procedure Claude follows |
| **Reference instance** | [`examples/bio-1320/`](examples/bio-1320/) — Bio 1320 Exam 3, Chapters 9–13 |
| **Live demo** | https://karpeles.shinyapps.io/bio_study_tutor/ |

---

## What it builds

Give Claude a folder of slides, textbook chapters, PDFs, or any course documents. The skill produces a self-contained project with:

| Layer | What it is |
|---|---|
| `raw/extracted/` | Plain-text dumps of every source file |
| `wiki/` | Atomic Markdown pages — one per concept — cross-linked with `[[wikilinks]]` |
| `kg/` | Typed JSON knowledge graph: nodes, typed edges, and lookup indexes |
| `tools/` | Extraction, KG build, validation, print generation scripts |
| `app/` | Python Shiny web app with 6 tabs |
| `app/starter_content/` | Hand-curated quizzes, flashcards, and match games for first launch |
| `print/` | Full reference + 4-page compact "night before" cheat sheet |

### The six app tabs

| Tab | What it does |
|---|---|
| **Study Guide** | Browse all wiki pages by chapter and type; click `[[wikilinks]]` to navigate |
| **Ask** | LLM chat tutor that answers using **only** the wiki — no hallucinations |
| **Quiz** | Hand-authored packs + on-demand generation by the LLM |
| **Flashcards** | Flip-card decks + on-demand generation |
| **Print** | Full PDF-ready reference + 4-page compact edition |
| **Knowledge Graph** | PyVis network; click any node to highlight 2-degree neighbors |

---

## Install the skill

```bash
git clone https://github.com/iamkarp/bio-study-tutor
cp -r bio-study-tutor/skill ~/.claude/skills/build-study-tutor
```

Then in any Claude Code session:

> "I have a folder of organic chemistry slides. Build me a study tutor for Exam 2."

Claude invokes the skill and walks through the 9-phase procedure automatically. Works for any subject.

---

## Skill structure

```
skill/
├── SKILL.md                    ← The skill itself — 9-phase procedure Claude follows
├── templates/                  ← Source files copied into each new project
│   ├── app.py                  ← Shiny app (customize: chapter titles, node types)
│   ├── llm.py                  ← OpenRouter + Ollama client
│   ├── build_kg.py             ← Wiki → JSON knowledge graph builder
│   ├── build_print_version.py  ← Wiki → print-ready HTML
│   ├── graph_viz.py            ← PyVis 2-degree highlight graph
│   ├── games.py                ← LLM quiz / flashcard / match generators
│   ├── kg_loader.py            ← Loads wiki + KG at app startup
│   ├── extract_pptx.py         ← PPTX → raw/extracted/<slug>.md
│   ├── extract_docx.py         ← DOCX → raw/extracted/<slug>.md
│   ├── extract/                ← Shared parsing utilities
│   ├── validate.py             ← Schema + edge-integrity validator
│   ├── render_index.py         ← Regenerates wiki/index.md
│   ├── prebuild.py             ← One-shot LLM starter-content generator
│   ├── wikilink.py             ← Renders [[wikilinks]] to HTML
│   ├── study-guide-compact.template.html
│   ├── .env.example, .gitignore, .python-version, .rscignore
└── reference/                  ← Docs Claude reads during the skill
    ├── wiki-authoring.md       ← Page template, section conventions, wikilink rules
    ├── schema-design.md        ← Node/edge schema for 9 subject domains
    ├── architecture.md         ← 4-layer design and why
    ├── CLAUDE-template.md      ← CLAUDE.md to drop into each new project
    ├── deployment.md           ← shinyapps.io recipe and gotchas
    ├── pdf-extraction.md       ← Handling PDFs and scanned docs
    ├── starter-content-template.md  ← Quiz/flashcard/match JSON schemas
    ├── templates-manifest.md   ← What each template file does
    ├── troubleshooting.md      ← Common errors and fixes
    └── html-static-alternative.md  ← Zero-infrastructure static HTML variant
```

---

## The 9 phases

| Phase | What happens | Time |
|---|---|---|
| 0: Intake | Confirm scope, source folder, project slug, API key | 5 min |
| 1: Schema design | Choose node types and edge relations for the subject | 15–30 min |
| 2: Scaffold | Create directory tree, copy and customize template files | 20 min |
| 3: Extraction | Convert PPTX/DOCX/PDF to raw Markdown | 15 min |
| 4: Wiki authoring | One page per concept — the substantial step | 4–8 hours |
| 5: Starter content | Author quizzes, flashcards, match games | 30–60 min |
| 6: Print editions | Generate full + compact PDF-ready HTML | 15 min |
| 7: App test | Smoke-test all 6 tabs | 20 min |
| 8: Deploy (optional) | Publish to shinyapps.io | 15 min |
| 9: Video (optional) | Demo video with TTS narration | 15 min |

Phase 4 is where the real work happens — and where the quality of the final app is determined. Everything else is automated.

---

## Requirements

```bash
pip3 install shiny pyvis requests pyyaml markdown networkx python-pptx python-docx jsonschema
```

- **OpenRouter API key** (free tier) — for the chat tutor and on-demand content generation. Get one at https://openrouter.ai/keys
- **Or Ollama** — run fully offline with `gemma4:26b` (24 GB RAM), `gemma4:9b` (16 GB), or `gemma4:e4b` (phone). Set `OLLAMA_URL=http://localhost:11434/v1` in `.env`.
- **For deployment:** `pip3 install rsconnect-python` + a shinyapps.io account (free tier works)

---

## Works for any subject

The schema (node types, edge relations) is designed per-subject. `skill/reference/schema-design.md` includes ready-made schemas for:

Biology · Chemistry · Mathematics · History · Programming · Law · Medicine · Business · Languages

One conversation with Claude + a folder of documents → a working tutor for that subject.

---

## Reference instance — Bio 1320 Exam 3

[`examples/bio-1320/`](examples/bio-1320/) is a complete, working instance built for a real biology course (Exam 3, Chapters 9–13: Meiosis, Inheritance, DNA Replication, Gene Expression, Biotechnology).

| | |
|---|---|
| Wiki pages | 254 atomic concepts |
| KG nodes / edges | 254 / 1,178 typed |
| Node types | 16 |
| Starter content | 30 quiz questions · 60 flashcards · 36 match pairs |
| Print editions | Full (254 sections) + compact (4 pages, 92 facts) |
| Source material | 5 PowerPoint chapters + 1 study guide DOCX |

### Run the reference instance locally

```bash
git clone https://github.com/iamkarp/bio-study-tutor
cd bio-study-tutor/examples/bio-1320

pip3 install -r requirements.txt

# Option A: Ollama (offline, free, private)
ollama pull gemma4:26b
echo "OLLAMA_URL=http://localhost:11434/v1" >> .env
echo "OLLAMA_MODEL=gemma4:26b" >> .env

# Option B: OpenRouter (hosted)
echo "OPENROUTER_API_KEY=sk-or-v1-..." > .env

python3 -m shiny run --port 8765 app/app.py
# open http://localhost:8765
```

---

## Repository layout

```
.
├── skill/                      ← The Claude Code skill (install this)
│   ├── SKILL.md                ← 9-phase build procedure
│   ├── templates/              ← Source files for any new project
│   └── reference/              ← Docs Claude reads during the skill
│
└── examples/
    └── bio-1320/               ← Reference instance: Bio 1320 Exam 3
        ├── app/                ← Shiny app source
        ├── wiki/               ← 254 bio concept pages
        ├── kg/                 ← Derived knowledge graph
        ├── tools/              ← Extraction + build scripts
        ├── raw/                ← Original PPTX/DOCX + text dumps
        ├── print/              ← Full + compact PDF-ready editions
        ├── video/              ← Demo video
        └── CLAUDE.md           ← Schema contract for the bio instance
```

---

## Architecture

```
raw/        →  wiki/        →  kg/         →  app/
sources       human-readable   machine-      runtime
              source of truth  queryable     UI
```

Edit a wiki page → rerun `tools/build_kg.py` → every downstream artifact (chat context, quiz scope, print editions, graph) updates. Full details: [`skill/reference/architecture.md`](skill/reference/architecture.md)

---

## License

Code: MIT. Course material in `examples/bio-1320/raw/` and `examples/bio-1320/wiki/` is © the textbook authors (used here as a private study tool, not redistribution).
