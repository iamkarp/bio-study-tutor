# build-study-tutor

> A Claude Code skill that turns any folder of course materials into a complete, private, offline-capable interactive study tutor — grounded in a hand-authored wiki and a typed knowledge graph.

| | |
|---|---|
| **Skill** | [`skill/SKILL.md`](skill/SKILL.md) — drop into `~/.claude/skills/build-study-tutor/` |
| **Reference instance** | Bio 1320 Exam 3 — Chapters 9–13 (Meiosis, Inheritance, DNA, Gene Expression, Biotechnology) |
| **Live demo** | https://karpeles.shinyapps.io/bio_study_tutor/ |
| **Hackathon** | Submission to [The Gemma 4 Good Hackathon](https://kaggle.com/competitions/gemma-4-good-hackathon) — Future of Education track |

---

## What the skill builds

Give Claude a folder of slides, textbook chapters, PDFs, or any course documents. The skill produces:

| Layer | What it is |
|---|---|
| `raw/extracted/` | Plain-text dumps of every source file, one per slide deck or document |
| `wiki/` | Atomic Markdown pages — one per concept — cross-linked with `[[wikilinks]]` |
| `kg/` | Typed JSON knowledge graph derived from the wiki: nodes, edges, and indexes |
| `tools/` | Scripts for extraction, KG build, validation, and print generation |
| `app/` | Python Shiny web app with 6 tabs (see below) |
| `app/starter_content/` | Hand-curated quizzes, flashcards, and match games — playable on first launch |
| `print/` | Full reference (one section per wiki page) + 4-page compact "night before" sheet |

### The six app tabs

| Tab | What it does |
|---|---|
| **Study Guide** | Browse all wiki pages by chapter and type; click any `[[wikilink]]` to navigate |
| **Ask** | LLM-powered chat tutor that answers using **only** the wiki — no hallucinations |
| **Quiz** | Hand-authored question packs + on-demand generation by the LLM |
| **Flashcards** | Flip-card decks + on-demand generation |
| **Print** | Full PDF-ready reference + 4-page compact cheat sheet |
| **Knowledge Graph** | Interactive PyVis network; click any node to highlight 2-degree neighbors |

---

## How to install the skill

```bash
# 1. Clone the repo
git clone https://github.com/iamkarp/bio-study-tutor

# 2. Copy the skill into Claude Code's skills directory
cp -r bio-study-tutor/skill ~/.claude/skills/build-study-tutor
```

Then in any Claude Code session, just say:

> "I have a folder of organic chemistry slides. Build me a study tutor for Exam 2."

Claude invokes the `build-study-tutor` skill and walks through the 9-phase procedure automatically.

---

## Skill structure

```
skill/
├── SKILL.md                    ← The skill itself — 9-phase procedure Claude follows
├── templates/                  ← Source files copied verbatim (or with light edits) into each new project
│   ├── app.py                  ← Shiny app (edit: chapter titles, node types, theme)
│   ├── llm.py                  ← OpenRouter + Ollama client (auto-routes by env)
│   ├── build_kg.py             ← Wiki → JSON knowledge graph builder (edit: node/edge schema)
│   ├── build_print_version.py  ← Wiki → print-ready HTML (full + compact editions)
│   ├── graph_viz.py            ← PyVis knowledge graph with 2-degree BFS highlight
│   ├── games.py                ← LLM-driven quiz / flashcard / match generators
│   ├── kg_loader.py            ← Loads wiki + KG into memory at app startup
│   ├── extract_pptx.py         ← PPTX → raw/extracted/<slug>.md
│   ├── extract_docx.py         ← DOCX → raw/extracted/<slug>.md
│   ├── extract/                ← Shared parsing utilities (frontmatter, wikilinks, sections, tables)
│   ├── validate.py             ← JSON-Schema + edge-integrity validator
│   ├── render_index.py         ← Regenerates wiki/index.md from KG
│   ├── prebuild.py             ← One-shot LLM starter-content generator
│   ├── wikilink.py             ← Renders [[wikilinks]] to HTML anchors
│   ├── study-guide-compact.template.html  ← Compact 4-page reference template
│   ├── .env.example            ← API key placeholder
│   ├── .gitignore              ← Standard ignores + .env excluded
│   ├── .python-version         ← Pins 3.11 for shinyapps.io
│   └── .rscignore              ← Excludes source binaries from rsconnect bundle
└── reference/                  ← Reference docs Claude reads during the skill
    ├── wiki-authoring.md       ← Page template, section conventions, wikilink discipline
    ├── schema-design.md        ← Node/edge schema for 8 subject domains
    ├── architecture.md         ← The 4-layer design (raw → wiki → kg → app) and why
    ├── CLAUDE-template.md      ← CLAUDE.md schema contract to drop into a new project
    ├── deployment.md           ← shinyapps.io deployment, gotchas, env vars
    ├── pdf-extraction.md       ← Handling PDFs, scanned docs, mixed sources
    ├── starter-content-template.md  ← Quiz/flashcard/match JSON format
    ├── templates-manifest.md   ← What each template file does and where it goes
    ├── troubleshooting.md      ← Common errors and fixes
    └── html-static-alternative.md  ← Zero-infrastructure static HTML site instead of Shiny
```

---

## The 9 phases

| Phase | What happens | Time |
|---|---|---|
| 0: Intake | Confirm scope, source folder, project slug, API key | 5 min |
| 1: Schema design | Choose node types and edge relations for the subject | 15–30 min |
| 2: Scaffold | Create directory tree, copy and customize template files | 20 min |
| 3: Extraction | Convert PPTX/DOCX/PDF to raw Markdown | 15 min |
| 4: Wiki authoring | Hand-author one page per concept — the substantial step | 4–8 hours |
| 5: Starter content | Author quizzes, flashcards, match games | 30–60 min |
| 6: Print editions | Generate full + compact PDF-ready HTML | 15 min |
| 7: App test | Smoke-test all 6 tabs; verify KG renders and tutor answers are grounded | 20 min |
| 8: Deploy (optional) | Publish to shinyapps.io | 15 min |
| 9: Video (optional) | Demo video with TTS narration via edge-tts + ffmpeg | 15 min |

Phase 4 (wiki authoring) is where the real work happens — and where the quality of the final app is determined. Everything else is automated.

---

## Deployment options

The skill supports two runtime modes. Choose based on what the user needs:

### Option A — Python Shiny app (default)

A live server with full LLM integration: Ask tab, on-demand quiz/flashcard generation, and local Ollama support.

```bash
pip3 install shiny pyvis requests pyyaml markdown networkx python-pptx python-docx jsonschema

# Run locally
python3 -m shiny run --port 8765 app/app.py

# Or deploy to shinyapps.io (see skill/reference/deployment.md)
pip3 install rsconnect-python
```

Needs: Python 3.11 + a shinyapps.io account (free tier works) or a local machine running the app.

### Option B — Static HTML site (zero infrastructure)

Pre-renders everything to a `site/` folder. Deploy to GitHub Pages, Netlify, or just zip and share — no Python needed at runtime.

```bash
python3 tools/build_static.py   # generates site/
python3 -m http.server 8080 --directory site/   # preview
```

| | Shiny | Static HTML |
|---|---|---|
| Ask (LLM tutor) | ✅ server-side | ⚠️ client-side key or omit |
| On-demand quiz/flashcard generation | ✅ | ❌ pre-authored only |
| Hosting | shinyapps.io / local server | GitHub Pages / Netlify / ZIP |
| Runtime dependency | Python 3.11 | None |
| Offline / zip-and-share | ❌ | ✅ |

Full details, the `build_static.py` script, and LLM Ask tab options for static mode are in [`skill/reference/html-static-alternative.md`](skill/reference/html-static-alternative.md).

## Requirements

```bash
pip3 install shiny pyvis requests pyyaml markdown networkx python-pptx python-docx jsonschema
```

- **OpenRouter API key** (free tier works) — for the chat tutor and on-demand content generation. Get one at https://openrouter.ai/keys
- **Or Ollama** — run entirely offline with `gemma4:26b` (24 GB RAM), `gemma4:9b` (16 GB), or `gemma4:e4b` (phone). Set `OLLAMA_URL=http://localhost:11434/v1` in `.env`.
- **For Shiny deployment:** `pip3 install rsconnect-python` + a shinyapps.io account

---

## Works for any subject

The schema (node types, edge relations) is designed per-subject. The skill's `reference/schema-design.md` includes ready-made schemas for:

Biology · Chemistry · Mathematics · History · Programming · Law · Medicine · Business · Languages

One conversation with Claude + a folder of documents → a working tutor for that subject.

---

## Reference instance — Bio 1320 Exam 3

The `wiki/`, `kg/`, `app/`, and `tools/` directories in this repo are the working reference instance built for a real biology course (Exam 3, Chapters 9–13).

| | |
|---|---|
| Wiki pages | 254 atomic concepts |
| KG nodes / edges | 254 / 1,178 typed |
| Node types | 16 (chapter, exam_topic, concept, process, structure, molecule, enzyme, term, inheritance_pattern, experiment, person, disease, technique, principle, comparison, source) |
| Hand-authored starter content | 30 quiz questions · 60 flashcards · 36 match pairs |
| Print editions | Full (254 sections) + compact (4 pages, 92 facts) |
| Source material | 5 PowerPoint chapters + 1 study guide DOCX |
| Build time | ~1 day (wiki authoring is the bottleneck; everything else is automated) |

### Run the reference instance locally

```bash
git clone https://github.com/iamkarp/bio-study-tutor
cd bio-study-tutor
pip3 install -r requirements.txt

# Option A: local Ollama (offline, free, private)
ollama pull gemma4:26b          # or gemma4:9b (16 GB RAM) or gemma4:e4b (phone)
echo "OLLAMA_URL=http://localhost:11434/v1" >> .env
echo "OLLAMA_MODEL=gemma4:26b" >> .env

# Option B: OpenRouter (hosted backend)
echo "OPENROUTER_API_KEY=sk-or-v1-..." > .env

python3 -m shiny run --port 8765 app/app.py
# open http://localhost:8765
```

---

## How Gemma 4 powers this

Three roles, each chosen because open weights make them possible where general APIs can't go:

1. **Grounded chat tutor** — ~80 KB of wiki content as system context. Answers every question from the wiki only. Every claim is traceable to a source slide.
2. **Dynamic content generation** — On-demand quizzes, flashcards, and match games scoped to chapters or topics, returned as strict JSON.
3. **Local-first deployment** — Same code runs against a hosted backend or a local Ollama instance. Toggle with one env var.

---

## Architecture

```
raw/        →  wiki/        →  kg/         →  app/
sources       human-readable   machine-      runtime
              source of truth  queryable     UI
```

Edit a wiki page → rerun `tools/build_kg.py` → every downstream artifact (chat context, quiz scope, print editions, graph) updates consistently.

Full details: [`skill/reference/architecture.md`](skill/reference/architecture.md)

---

## Repository layout

```
.
├── skill/                      ← The Claude Code skill (install this)
│   ├── SKILL.md                ← 9-phase procedure
│   ├── templates/              ← Source files for any new project
│   └── reference/              ← Docs Claude reads during the skill
│
├── wiki/                       ← Reference instance: 254 bio concept pages
├── kg/                         ← Reference instance: derived knowledge graph
├── app/                        ← Reference instance: Shiny app source
│   ├── app.py                  ← UI + reactive logic
│   ├── llm.py                  ← Gemma 4 client (Ollama or OpenRouter)
│   ├── kg_loader.py, games.py, graph_viz.py, wikilink.py
│   └── starter_content/        ← Hand-authored quiz/flashcard/match starters
├── tools/                      ← Reference instance: extraction + build scripts
├── raw/                        ← Reference instance: original PPTX/DOCX + text dumps
├── print/                      ← Reference instance: full + compact PDF-ready editions
├── CLAUDE.md                   ← Schema contract for the bio reference instance
├── WRITEUP.md                  ← Hackathon submission writeup
└── ABOUT.md                    ← Impact essay
```

---

## License

Code: MIT. Course material in `raw/` and `wiki/` is © the textbook authors (used here as a private study tool, not redistribution).
