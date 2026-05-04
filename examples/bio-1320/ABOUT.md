# A Tutor for Every Course

### How one biology class became a wiki, a knowledge graph, an LLM tutor, a quiz engine, an interactive network, and a printable handbook — in a few days. And why the pattern matters more than the app.

> A working sketch of what happens when you turn a single college course's source material into a hybrid wiki + knowledge graph + interactive tutor + dynamic games + printable handbook — built in days, deployable anywhere.

Live: **https://karpeles.shinyapps.io/bio_study_tutor/**

---

## 1. What this app is

The Bio Study Tutor is a personalized, course-specific study companion built from one undergraduate biology class's source material — five chapter PowerPoints (chapters 9–13: Meiosis, Patterns of Inheritance, DNA Structure & Replication, How Genes Work, Biotechnology) and an instructor-issued exam study guide.

It packages that material into six modes of study, available through a single Shiny web app:

| Tab | What it does |
|---|---|
| **Study Guide** | Browse 254 atomic wiki pages by chapter or by type (processes, structures, molecules, enzymes, terms, inheritance patterns, experiments, people, diseases, techniques, principles, comparisons). Click any page → detail view with full body, type tag, source citations, and a "Connected pages" sidebar listing every other page the knowledge graph links it to. |
| **Ask** | A chat tutor backed by Google Gemma (via OpenRouter) that answers using **only** the wiki text — no hallucinated facts. Multi-turn conversation; markdown-rendered answers with inline `[[wikilinks]]` clickable. |
| **Quiz** | Six pre-authored multiple-choice quiz packs (30 questions hand-curated from the study guide), navigable as a queue. Each click on a choice reveals correctness, the right answer, and an explanation. "Add quiz to queue" generates a fresh LLM-authored quiz at chosen scope and difficulty — extending the queue indefinitely. |
| **Flashcards** | Six pre-authored decks (60 cards). Click the card or the Flip button to reveal the back. Front-to-back gradient styling, prev/next navigation, deck queue with on-demand generation. A second sub-tab is a **match game** — drag/click pairs of terms and definitions, with selected/matched/wrong visual states. |
| **Print** | Two PDF-ready editions, both internally hyperlinked: a **compact 4-page** version with 92 hand-curated numbered facts in a 2-column dense layout, and a **full 254-section** version covering the entire wiki with a table of contents and an alphabetical index. Browser print → Save as PDF preserves the cross-references as PDF bookmarks. |
| **Knowledge Graph** | An interactive PyVis network of all 254 nodes and 1,178 typed edges. Filter by chapter or node type. **Click any node** → its 1- and 2-degree neighbors stay full color (with larger labels) while everything else fades to gray with hidden text — turning the graph into a context-isolated micro-textbook for that concept. Adjustable edge length and label size. |

It runs locally in a single command (`shiny run app/app.py`) and is deployed to shinyapps.io for anywhere-access.

---

## 2. How it's built — the architecture

The whole system rests on one design choice: **the source of truth is human-readable Markdown, and everything else is derived from it.**

### Layer 1 — Raw material (immutable)

```
raw/
├── Chapter 9 Meiosis.pptx
├── Chapter 10 Patterns of Inheritance.pptx
├── Chapter 11 DNA Structure and Replication.pptx
├── Chapter 12 How Genes Work.pptx
├── Chapter 13 New Biology.pptx
├── Study Guide Exam 3 Bio 1320 Spring 2026.docx
└── extracted/         ← per-slide markdown text dumps for grep-ability
```

Two extractors (`tools/extract_pptx.py`, `tools/extract_docx.py`) walk every slide and paragraph, preserving `## Slide N` anchors so any wiki page can cite back to the exact source slide.

### Layer 2 — The hybrid wiki + knowledge graph

The wiki is **254 atomic markdown pages**, one per concept. Every page has YAML frontmatter and uses `[[wikilink]]` syntax for cross-references:

```yaml
---
id: process:meiosis
type: process
title: Meiosis
slug: meiosis
chapters: [9]
exam_topics: [full-meiosis-process, rounds-of-replication-in-meiosis]
---

## Summary
Meiosis is the form of cell division that produces **haploid gametes**...

## Steps
1. Interphase (DNA replication during S phase)
2. [[processes/meiosis-i]] — separates homologous pairs
3. [[processes/meiosis-ii]] — separates sister chromatids
```

A builder (`tools/build_kg.py`) parses the wiki and emits a typed knowledge graph:

- **`kg/nodes/<type>/<slug>.json`** — one file per node, with title, type, chapters, summary
- **`kg/edges.jsonl`** — 1,178 typed edges (`covers`, `part_of`, `compared_to`, `mentioned_in`, …)
- **`kg/indexes/`** — derived lookups: `by-chapter.json`, `by-tag.json`, `backlinks.json`, `coverage.json`, `orphans.json`

Edge types are inferred from the section a wikilink appears in: a link inside `## Steps` becomes a `part_of` edge; inside `## Sources` it becomes `cites`; inside `## Compared To` it becomes `compared_to`. The whole graph is regenerated from scratch on every build, so wikis can be edited freely without ever touching the JSON.

### Layer 3 — The Shiny app

A Python Shiny app (`app/app.py`) loads the wiki and KG into memory at startup, then serves the six tabs. The dynamic content uses different mechanisms:

- **LLM-grounded answers** — every Ask question gets up to 80 KB of wiki text concatenated as system context; the model is instructed to answer only from that material.
- **Game generation** — quizzes, flashcards, and match games are generated by structured-JSON-mode LLM calls that pull random subsets of the wiki text as context. The starter content for each game type is **hand-authored** (30 quiz questions, 60 flashcards, 36 match pairs) so the first launch is instant; LLM generation extends the queue when the user wants more.
- **Knowledge graph** — PyVis renders the network to a static HTML file in a static-asset directory; an iframe loads it. A small injected JavaScript snippet implements click-to-highlight: a BFS computes 1- and 2-degree neighbors of the clicked node, and updates colors/sizes/labels accordingly.
- **Print editions** — `tools/build_print_version.py` produces both editions: the compact one is hand-authored for density (92 facts in 4 pages with internal `<a href="#sec-N">` cross-references), the full one walks every wiki page in chapter+type order and replaces every `[[wikilink]]` with a `[§N]` reference.

### Layer 4 — Deployment

```
.python-version       3.11
.rscignore            excludes 90 MB of source PPTX
manifest.json         entrypoint = app (the package), Python 3.11.0
requirements.txt      6 lines (shiny, pyvis, requests, pyyaml, markdown, networkx)
app/__init__.py       package shim that loads app/app.py and re-exports App
```

`rsconnect deploy manifest manifest.json --name karpeles` ships it to shinyapps.io. The whole bundle (excluding 90 MB of source PowerPoints) is around 4 MB.

---

## 3. Why this matters — the impact

A single-course study tutor is a small thing. The pattern behind it is not. Five things stand out about what this kind of system makes possible.

### 3.1 Personalized tutoring goes from luxury to default

The single largest determinant of academic success in K-12 and undergraduate education isn't curriculum, classroom size, or technology — it's **how much one-on-one explanation a student gets** when they're stuck. That's why students of professionals, who can afford private tutors, perform two-thirds of a standard deviation above the mean on standardized tests and why Bloom's "2-sigma problem" (1984) showed that one-on-one mastery learning produces outcomes two standard deviations above conventional instruction.

Until 2023 there was no scalable way to give every student that. Now there is. A study app like this one gives any student with an internet connection access to a tutor who:

- knows their specific course's material and only that material
- is available at 2 a.m. the night before an exam
- can be asked the same question fifteen different ways without judgment
- generates fresh practice questions on demand at the difficulty the student picks
- never tires, never has office-hour conflicts, costs near-zero per student

The cost floor for building this — historically months of work by a team — is now hours of work by one person who has the source material. That's a phase change.

### 3.2 Grounding makes LLMs trustworthy in education

The core problem with using a general-purpose LLM as a tutor is hallucination: ChatGPT will confidently invent facts that aren't in the textbook, contradict the instructor, or apply concepts incorrectly. In high-stakes domains (medical training, law, engineering), this is disqualifying.

The hybrid wiki + KG pattern solves this. The LLM is given **only the canonical course material** as context and instructed to answer from that. If the answer isn't in the wiki, it says so. The wiki itself is human-authored, instructor-reviewable, and version-controlled — every claim in it is auditable back to a specific source slide.

This is the missing piece that turns "AI in education" from a marketing slogan into something a curriculum committee can actually approve. The same architecture works for:

- a medical residency studying pathophysiology
- a law student preparing for the bar exam
- an apprentice electrician studying NEC code
- a pilot training on a new aircraft's systems
- an employee onboarding to internal company processes

The course/textbook/manual changes; the architecture doesn't.

### 3.3 The wiki + KG pattern is architecturally important

Most "AI study tools" today are flashcard apps with an LLM stapled on. They produce content but no structure. The hybrid wiki + KG pattern produces **both** structure and content, with two profound consequences.

**For humans**: every concept gets its own page that can be read, edited, and improved. The wiki is a living artifact that stays useful even if you turn the LLM off. An instructor reviewing the wiki can spot exactly where coverage is thin (`kg/indexes/coverage.json`), which concepts have no incoming references (`orphans.json`), and which edges between concepts are missing.

**For machines**: every concept also has a typed JSON node with typed edges, which means it can be queried like a database. "Which enzymes catalyze which processes?" "What did Mendel demonstrate?" "Show me every page that mentions sister chromatids." All of these are graph queries against a small, fast JSON file — no LLM call required.

This is the pattern that matters: text for humans, structure for machines, both derived from the same source. Edit the wiki, rebuild the graph, and everything downstream — the chat tutor's context, the quiz generator's scope filters, the printable index, the interactive network visualization — updates automatically.

### 3.4 Multi-modal study fits how brains actually work

Cognitive science is unambiguous: **distributed practice with retrieval is the most effective study technique known**, ahead of re-reading, highlighting, and almost everything else (Dunlosky et al. 2013). The Bio Study Tutor lets a student do that in five distinct modes within a single session:

- **Read** the atomic concept page (encoding)
- **Ask** the tutor a clarifying question (deeper encoding)
- **Quiz** themselves with multiple choice (retrieval practice with feedback)
- **Flip flashcards** for terms and comparisons (spaced retrieval)
- **Match** terms to definitions (lateral connection-making)
- **Navigate** the knowledge graph by clicking around the 2-degree neighborhood of a concept (relational learning)

A traditional study guide gives you one mode (read). A flashcard app gives you two (read + flip). A study tutor like this one gives you six, all from the same source material. And the printable editions are there for the contexts where screens don't work — a flight, a power outage, an exam day where phones aren't allowed.

### 3.5 Equity by default

The student who currently has the most expensive tutor in their school district sets the upper bound on how good educational AI needs to be before it equalizes outcomes. Right now the cost of building this kind of system is dropping faster than even the cost of a single tutoring session. By the end of this decade, a well-designed grounded tutor should be a non-issue: every textbook ships with one, every course catalog includes one, every student has access regardless of family resources.

That's the promise. We're not there yet — this app is a working sketch, not a polished product, and it serves one course built by one person in a few days. But the pattern is reproducible. The same architecture can be applied to every course, every certification, every training manual. The work is in the source material; the rest is templated.

---

## 4. Honest limitations

A short list, since polish without honesty is its own kind of failure mode.

- **The LLM still makes mistakes.** Grounding reduces hallucination dramatically but doesn't eliminate it. A student should treat the Ask tutor like a smart classmate, not an oracle.
- **It's only as good as its source.** If the original PowerPoints have errors or omissions, the wiki inherits them. Garbage in, polished garbage out. An instructor needs to review the wiki for correctness before relying on it.
- **It can't replace a great human teacher.** A great teacher reads the room, picks up that you don't actually understand the concept you're nodding along to, and pivots. No LLM does that yet.
- **Scope is bounded.** Ask the tutor about cellular respiration (chapter 7) and it'll tell you that's outside the wiki's coverage and suggest the closest topic that *is* covered. That's a feature for trustworthiness, not a bug — but it does mean the tool is genuinely course-specific, not a general-purpose tutor.
- **Free-tier deployment sleeps.** shinyapps.io free tier puts the container to sleep after 15 minutes of inactivity. First request after sleep takes ~20 seconds to spin up.

---

## 5. What's next

The plan, if anyone runs with this:

1. **Apply the pattern to other courses.** Calculus, anatomy, organic chemistry, statistics, algorithms — anything with stable source material and a defined exam scope.
2. **Add spaced repetition tracking.** Right now the flashcards don't remember what you got wrong. SuperMemo's SM-2 algorithm in ~50 lines of code would change that.
3. **Add image grounding.** The PPTs have important diagrams (the meiosis stages visualized, the central dogma flow, etc.) that the current text-only extraction loses. A multimodal LLM could caption them and add the captions to the wiki.
4. **Add a teacher dashboard.** Show which exam topics students ask about most, which questions they get wrong, which concepts have weak in-wiki coverage. The KG already has the indexing for this; only the dashboard is missing.
5. **Open-source the template.** A `cookiecutter`-style scaffold that takes "a folder of slides + a study guide" and produces this whole stack with one command. The hardest part is already done.

---

## 6. Acknowledgments

This app is an instance of the [llm-wiki](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) pattern: an LLM-maintained collection of markdown files that compounds knowledge over time.

The Knowledge Graph visualization uses [PyVis](https://github.com/WestHealth/pyvis) wrapping vis.js. The web framework is [Shiny for Python](https://shiny.posit.co/py/). The LLM behind dynamic content is Google Gemma via [OpenRouter](https://openrouter.ai/). The print editions use browser-native HTML → PDF.

Course material is © the textbook authors; this app is a private study tool, not a redistribution.

---

*If you build something like this for another course, tell us. The pattern wants to spread.*
