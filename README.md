# A Tutor for Every Course

> **Submission to [The Gemma 4 Good Hackathon](https://kaggle.com/competitions/gemma-4-good-hackathon) — Future of Education Impact Track**

A pattern (and one working reference instance) for turning **any course's source material** into a private, grounded, multi-modal study tutor that runs offline on a consumer laptop using Gemma 4.

| | |
|---|---|
| **🎬 Video (3 min)** | [YouTube link — pending upload] |
| **📝 Writeup** | [`WRITEUP.md`](WRITEUP.md) (1,374 words) |
| **🌐 Live demo** | https://karpeles.shinyapps.io/bio_study_tutor/ |
| **🧪 Reference instance** | Bio 1320 Exam 3 (Chapters 9–13: Meiosis, Inheritance, DNA, Gene Expression, Biotechnology) |
| **🛠 Reproducer skill** | [`build-study-tutor`](https://github.com/iamkarp/bio-study-tutor) — Claude Code skill that scaffolds the same stack for any subject |

## How Gemma 4 powers this

Gemma 4 does three jobs in this app, each chosen because Gemma 4's open weights let it work where general APIs can't:

1. **Grounded chat tutor** — Every question gets ~80 KB of wiki content as system context. Model is instructed to use only the wiki. Output: factually grounded answers, every claim traceable to a source slide.
2. **Dynamic content generation (structured JSON)** — When the student exhausts hand-authored quizzes/flashcards/match games, Gemma 4 generates new ones scoped to chapters or topics, returned as strict JSON.
3. **Local-first deployment** — Same code runs against either a hosted backend (`google/gemma-4-26b-a4b-it` via OpenRouter) or a local Ollama instance (`gemma4:26b` on 24 GB RAM, `gemma4:9b` on 16 GB, `gemma4:e4b` on a phone). Toggle with one env var.

## Run it locally with Gemma 4 (offline, free, private)

```bash
git clone https://github.com/iamkarp/bio-study-tutor
cd bio-study-tutor
pip3 install -r requirements.txt

# Install Ollama: https://ollama.com
ollama pull gemma4:26b   # or gemma4:9b for 16 GB RAM, gemma4:e4b for a phone

# Configure local mode
echo "OLLAMA_URL=http://localhost:11434/v1" >> .env
echo "OLLAMA_MODEL=gemma4:26b" >> .env

python3 -m shiny run --port 8765 app/app.py
# open http://localhost:8765
```

**No API key required. No network calls after `ollama pull`. Zero recurring cost.**

## Run it via OpenRouter (hosted backend, no local install)

```bash
echo "OPENROUTER_API_KEY=sk-or-v1-..." > .env   # https://openrouter.ai/keys
python3 -m shiny run --port 8765 app/app.py
```

## What's in the app

Six tabs, all driven by the same source-of-truth wiki:

| Tab | What it does |
|---|---|
| **Study Guide** | Browse 254 atomic wiki pages by chapter or by type, with cross-links between concepts |
| **Ask** | Chat with a Gemma 4-powered tutor that answers using **only** the wiki |
| **Quiz** | Six pre-authored MCQ packs + on-demand generation by Gemma 4 |
| **Flashcards / Match Game** | Six pre-authored decks + a term/definition matching mini-game |
| **Print** | Two PDF-ready editions: full 254-section reference, plus a hand-curated 4-page compact "night before" sheet |
| **Knowledge Graph** | Interactive PyVis network of all 254 nodes and 1,178 typed edges. Click a node → 1- and 2-degree neighbors highlighted; rest fades |

## Architecture (four layers)

```
raw/        →  wiki/        →  kg/         →  app/
sources       human-readable   machine-      runtime
              source of truth  queryable     UI
```

1. **`raw/`** — original PPTX/DOCX, plus per-slide text dumps. Never modified.
2. **`wiki/`** — 254 hand-authored atomic Markdown pages, cross-linked with `[[wikilinks]]`. **The single source of truth.**
3. **`kg/`** — derived JSON knowledge graph. `tools/build_kg.py` parses the wiki → typed nodes/edges. 1,178 edges across 16 node types.
4. **`app/`** — Python Shiny app. Loads wiki + KG into memory at startup; never writes back.

Edit a wiki page, rerun `tools/build_kg.py`, and every downstream artifact (chat context, quiz scope, print editions, graph) updates consistently.

## Repository layout

```
.
├── WRITEUP.md                  ← Kaggle hackathon submission writeup (1,374 words)
├── ABOUT.md                    ← longer-form impact essay (2,400 words)
├── CLAUDE.md                   ← schema contract for the wiki
├── raw/                        ← original course materials (PPTX, DOCX)
├── wiki/                       ← 254 atomic Markdown pages
├── kg/                         ← derived JSON knowledge graph (nodes, edges, indexes)
├── tools/                      ← extraction, KG build, validation, print, video pipeline
├── app/                        ← Shiny app source
│   ├── app.py                  ← UI + reactive logic
│   ├── llm.py                  ← Gemma 4 client (auto-routes Ollama vs OpenRouter)
│   ├── kg_loader.py, games.py, graph_viz.py, wikilink.py
│   └── starter_content/        ← hand-authored quiz/flashcard/match starters
├── print/                      ← full + compact PDF-ready editions
├── video/                      ← 3-minute demo video + script + audio
└── screenshots/                ← captured app screens
```

## Reproducibility — `build-study-tutor` skill

A Claude Code skill at `~/.claude/skills/build-study-tutor/` takes a folder of course documents and produces this entire stack for any subject. Procedure documented in the skill's `SKILL.md` with reference docs for schema design (math, chemistry, history, programming, law, medicine, languages, business), wiki authoring, starter content, deployment, and troubleshooting.

```
"I have a folder of organic chemistry chapter PDFs. Build me a study tutor for Exam 2."
→ Claude invokes build-study-tutor → 9-phase procedure → working app for that subject
```

## Stats

| | |
|---|---|
| Wiki pages | 254 atomic concepts |
| KG nodes / edges | 254 / 1,178 typed |
| Node types | 16 (chapter, exam_topic, concept, process, structure, molecule, enzyme, term, inheritance_pattern, experiment, person, disease, technique, principle, comparison, source) |
| Hand-authored starter content | 30 quiz questions · 60 flashcards · 36 match pairs |
| Print editions | Full (254 sections) + compact (4 pages, 92 facts) |
| Build time from scratch | ~1 day for the wiki (the labor-intensive step); minutes for everything else |

## License

Code: MIT. Course material is © the textbook authors (used here as a private study tool, not redistribution).

## Citation

> Karpeles, J. (2026). *A Tutor for Every Course — Bio Study Tutor reference instance*. The Gemma 4 Good Hackathon. https://github.com/iamkarp/bio-study-tutor
