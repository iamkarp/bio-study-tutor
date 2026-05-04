# A Tutor for Every Course

### Built for **Future of Education** — turning a single course's source material into a private, grounded, multi-modal study tutor that runs offline on a consumer laptop with Gemma 4.

> **Live demo:** https://karpeles.shinyapps.io/bio_study_tutor/
> **Repo:** https://github.com/iamkarp/bio-study-tutor
> **Video (3 min):** [YouTube link]

---

## The problem

The single biggest predictor of academic outcomes isn't curriculum, classroom size, or tech. It's **how much one-on-one explanation a student gets when they're stuck**. Bloom's 2-sigma problem (1984) showed individual mastery tutoring lifts students two standard deviations above conventional instruction. But one-on-one tutoring has historically been a privilege — a few hundred dollars an hour, gated to families that can pay.

Until 2023 there was no scalable substitute. Today's general LLMs come close, but two issues block real classroom adoption:

1. **Hallucination** — a generic chatbot will confidently invent facts that contradict the textbook, fabricate citations, and answer questions outside the syllabus. Disqualifying for any course-grade material.
2. **Cost & privacy** — calling cloud APIs costs money, sends every student question to a third party, and stops working on a flight, in rural broadband, or in a school that won't whitelist outbound traffic.

The students who would benefit most from AI tutoring are the ones least likely to have a $20/month subscription, fast home internet, or permission to send class material to OpenAI.

## The solution

A **course-specific, grounded tutor** built from one professor's PowerPoints and a study guide. The reference instance covers Bio 1320 Exam 3 (chapters 9–13: Meiosis, Inheritance, DNA, Gene Expression, Biotechnology). Six modes of study, all running off the same source-of-truth wiki:

| Tab | What it does |
|---|---|
| **Study Guide** | Browse 254 atomic wiki pages by chapter or by type, with cross-links between concepts |
| **Ask** | Chat with a Gemma 4-powered tutor that answers using **only** the wiki — no hallucinated facts |
| **Quiz** | Six pre-authored MCQ packs + on-demand generation of new packs scoped to chapters or types |
| **Flashcards / Match Game** | Six pre-authored decks + a term/definition matching mini-game |
| **Print** | Two PDF-ready editions: full 254-section reference with hyperlinks, and a hand-curated 4-page compact "night before" sheet |
| **Knowledge Graph** | Interactive PyVis network of all 254 nodes and 1,178 typed edges. Click any concept → 1- and 2-degree neighbors stay full color while the rest fade to gray |

**Built in two days** from raw lecture material. The architecture is the contribution: any student or instructor with source material and a laptop can stand up the same stack for their course.

## How Gemma 4 powers it

Gemma 4 is doing three jobs in this app, each chosen specifically because Gemma 4's open weights let it work where general APIs can't:

**1. Grounded chat tutor (RAG with the wiki).** Every Ask question gets ~80 KB of wiki content concatenated as system context. The model is instructed: *"Use ONLY the study material provided. If the question is outside scope, say so and suggest the closest topic that IS covered."* Output: factually grounded answers with markdown formatting, every claim traceable to a wiki page → which itself cites a specific source slide.

**2. Dynamic content generation (structured JSON output).** When a student exhausts the six pre-authored quizzes, "Generate quiz" prompts Gemma 4 with a slice of the wiki and a JSON schema. The model returns five new MCQs with explanations. Same pattern for flashcards and match-game pairs. The starter content is hand-authored; Gemma 4 extends it indefinitely.

**3. Local-first deployment.** The app's `llm.py` reads `OPENROUTER_API_KEY` for the hosted demo, but the same code path works against a local Ollama instance running Gemma 4: change one line in `.env` from OpenRouter's URL to `http://localhost:11434/v1` and a student running Ollama gets a fully offline tutor. **Gemma 4's E4B and 26B variants both fit on consumer hardware** — 24 GB system RAM is enough for a quantized 26B, and the 9B variant runs comfortably on 16 GB. No GPU required for usable latency.

The full tutor can run with **zero network calls** and **zero recurring cost**. That's the contest's whole point: open weights make the difference between "AI that exists" and "AI that's actually accessible."

## The architecture (four layers)

```
raw/        →  wiki/        →  kg/         →  app/
sources       human-readable   machine-      runtime
              source of truth  queryable     UI
```

1. **`raw/`** — original PPTX/DOCX, plus per-slide text dumps. Never modified.
2. **`wiki/`** — 254 hand-authored atomic Markdown pages, one per concept, cross-linked with `[[wikilinks]]`. **The single source of truth.**
3. **`kg/`** — derived JSON knowledge graph. `tools/build_kg.py` parses the wiki and emits typed nodes/edges. 1,178 edges across 16 node types. Edges are inferred from the section a wikilink appears in (`## Steps` → `part_of`, `## Sources` → `cites`, etc.).
4. **`app/`** — Python Shiny app. Loads wiki + KG into memory at startup; never writes back.

Edit a wiki page, rerun `tools/build_kg.py`, and every downstream artifact — chat context, quiz scope filters, print-edition cross-references, graph topology — updates consistently.

This **wiki + KG hybrid** is the technical innovation. Most "AI study tools" today are flashcard apps with an LLM stapled on. They produce content but no structure. The wiki+KG pattern produces both: text humans can read and edit, and a typed graph machines can query — both derived from the same source. An instructor reviewing the wiki can spot coverage gaps mechanically (`kg/indexes/coverage.json` lists every study-guide bullet without a covering page).

## Why this matters — the impact case

**Equity, in three dimensions:**

- **Cost** → with Gemma 4 + Ollama, marginal cost per student is **zero**. No subscription. No per-token billing. The model is the same one a $400/hour private tutor would use behind a paywall.
- **Privacy** → student questions never leave their laptop. Critical for IEPs, mental-health-adjacent topics, and any student in a jurisdiction or family that doesn't trust cloud AI.
- **Access** → works offline. On a plane. In a power outage. In a rural school with bad bandwidth. In a country where OpenAI is blocked.

**Trust by construction:** because the tutor only answers from the wiki, an instructor who has reviewed the wiki has reviewed every claim the tutor will make. That's the missing piece that turns "AI in education" from a marketing slogan into something a curriculum committee can approve. The same architecture works for medical residency studying pathophysiology, an apprentice electrician studying NEC code, a pilot training on a new aircraft, an employee onboarding to internal company processes. Course material changes; architecture doesn't.

**Reproducibility:** the project ships a Claude Code skill (`build-study-tutor`) that takes a folder of source documents and produces this entire stack for any subject in roughly a day of automated work. Calculus, anatomy, organic chemistry, the LSAT — same recipe.

The student who has the most expensive private tutor in their school district sets the upper bound on how good education has to get before AI levels the playing field. With Gemma 4 the upper bound just collapsed.

## Honest limitations

- **Wiki authoring is the hard part.** Extraction is automated; cross-linking takes a person reviewing every page. Bio took ~8 hours of focused work for 254 pages.
- **Gemma 4 still makes mistakes.** Grounding reduces hallucination dramatically; it doesn't eliminate it. Treat the tutor like a smart classmate, not an oracle.
- **Scope is bounded.** Ask about cellular respiration (chapter 7) and the tutor says "outside scope, here's the closest covered topic." That's a feature for trust, not a bug.

## Try it & repository

- **Live demo** (Gemma 4 via OpenRouter): https://karpeles.shinyapps.io/bio_study_tutor/
- **Local-first mode** (Gemma 4 via Ollama): clone the repo, `ollama pull gemma4:26b`, edit `.env`, `python3 -m shiny run app/app.py`
- **Repo + skill scaffold:** https://github.com/iamkarp/bio-study-tutor

Both modes use the same wiki, same KG, same six-tab UI, same dynamic generation. The only thing that changes is whether Gemma 4 is being served by a remote API or by an Ollama process on the same laptop.

The 3-minute video walks through the experience end-to-end. The code is open source under MIT. The architecture is reproducible: `build-study-tutor` is a Claude Code skill that scaffolds the same stack for any course.

*If you build one for another subject, tell us. The pattern wants to spread.*
