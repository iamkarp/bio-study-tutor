# Starter content — JSON schemas and authoring tips

`app/starter_content/{quizzes,flashcards,match}.json` are loaded at app startup and shown on first launch. Their quality sets the user's first impression of the entire app — **hand-author them**, don't generate them with the LLM.

## quizzes.json

```json
[
  {
    "label": "Mixed · Hard · 5 challenging questions",
    "scope": "all",
    "difficulty": "hard",
    "questions": [
      {
        "question": "Question prompt as a complete sentence.",
        "choices": ["A. First option", "B. Second", "C. Third", "D. Fourth"],
        "answer_index": 1,
        "explanation": "1-2 sentences citing why this is correct, referring to specific facts from the source material."
      }
    ]
  }
]
```

**Authoring tips**:
- Aim for **6 quiz packs × 5 questions = 30 total questions** for a starter set.
- Pack labels should describe scope and difficulty: `"Ch 9 · Easy"`, `"Mixed · Medium · 5"`, `"Ch 11 DNA · Medium · 5"`.
- One pack per major chapter + a `"Mixed · Hard"` pack at the end for review.
- `scope` values: `"all"` (any), `"chapter-N"` (specific chapter), or `"type-X"` (specific node type).
- `answer_index` is **0-based**.
- `choices` should be 4 items, all plausible. Easy pack: 1 obvious right answer. Hard pack: subtle distinctions.
- `explanation` is shown after the user answers — make it instructive, not just confirmatory.

## flashcards.json

```json
[
  {
    "label": "Ch 9 · Meiosis essentials · 10 cards",
    "scope": "chapter-9",
    "cards": [
      {
        "front": "Question or prompt (front of card).",
        "back": "Complete, exam-ready answer. **Bold** key terms. Use markdown."
      }
    ]
  }
]
```

**Authoring tips**:
- Aim for **6 decks × 10 cards = 60 total cards**.
- One deck per chapter + a "Mixed · Comparison drills" deck contrasting paired concepts (mitosis vs meiosis, etc.).
- The "back" can be multi-line markdown — bold terms, tables, comparisons all welcome.
- Front prompts should be questions or partial statements, not just a term name. Bad: "Mitosis." Good: "What does mitosis produce?"

## match.json

```json
[
  {
    "label": "Ch 9 · Meiosis terms · 6 pairs",
    "scope": "chapter-9",
    "pairs": [
      {
        "term": "Short term (1-4 words)",
        "definition": "One tight sentence definition."
      }
    ]
  }
]
```

**Authoring tips**:
- Aim for **6 games × 6 pairs = 36 total pairs**.
- Term should be **short** — 1-4 words. The match game UI gets crowded with long terms.
- Definition should be **one sentence**. Two sentences makes the visual layout fight itself.
- Don't include trivially distinguishable pairs (e.g. "Mitosis | Cell division" + "DNA | Genetic material" — too easy). Mix in close pairs that require real discrimination.

## Why hand-author the starters?

The reference Bio app's first attempt at starter content used the LLM (via `app/prebuild.py`) and produced mediocre, generic output. The user reported "no prefilled games, can't create new games" and quality was the issue.

Replacement was hand-authored from the actual study guide. Result: 30 quiz questions that map exactly to study-guide bullets, 60 flashcards with bold key terms and structured comparisons, 36 match pairs with sharp distinctions.

The lesson: **the starter content is the demo of your app's quality**. Don't outsource it.

The "Generate new" button **does** use the LLM — that's the right place for LLM generation. By the time the user clicks it, they've already played with the hand-authored starters and trust the app.
