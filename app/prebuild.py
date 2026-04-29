"""Pre-generate starter quiz/flashcard/match content for instant first-launch playability.

Run once:
    cd /Users/macbook/Documents/Study
    python3 app/prebuild.py
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

APP = Path(__file__).resolve().parent
REPO = APP.parent
sys.path.insert(0, str(APP))

from games import generate_flashcards, generate_match_game, generate_quiz  # noqa: E402
from kg_loader import load_pages  # noqa: E402

OUT = APP / "starter_content"
OUT.mkdir(parents=True, exist_ok=True)


def _time(label: str, fn):
    t0 = time.time()
    try:
        result = fn()
        print(f"  ✓ {label} ({time.time() - t0:.1f}s)")
        return result
    except Exception as e:
        print(f"  ✗ {label} FAILED: {e}")
        return None


def build_quizzes(pages):
    targets = [
        ("Mixed · Easy · 5", "all", "easy", 5),
        ("Mixed · Medium · 5", "all", "medium", 5),
        ("Mixed · Hard · 5", "all", "hard", 5),
        ("Ch 9 Meiosis · Medium · 5", "chapter-9", "medium", 5),
        ("Ch 11 DNA · Medium · 5", "chapter-11", "medium", 5),
        ("Ch 12 Genes · Medium · 5", "chapter-12", "medium", 5),
    ]
    out = []
    for label, scope, diff, n in targets:
        qs = _time(f"quiz: {label}",
                   lambda s=scope, d=diff, k=n: generate_quiz(pages, scope=s, n=k, difficulty=d))
        if qs:
            out.append({"label": label, "scope": scope, "difficulty": diff, "questions": qs})
    return out


def build_flashcards(pages):
    targets = [
        ("Mixed · 10 cards", "all", 10),
        ("Ch 9 Meiosis · 10 cards", "chapter-9", 10),
        ("Ch 10 Inheritance · 10 cards", "chapter-10", 10),
        ("Ch 11 DNA · 10 cards", "chapter-11", 10),
        ("Ch 12 Genes · 10 cards", "chapter-12", 10),
        ("Ch 13 Biotech · 10 cards", "chapter-13", 10),
    ]
    out = []
    for label, scope, n in targets:
        cards = _time(f"deck: {label}",
                      lambda s=scope, k=n: generate_flashcards(pages, scope=s, n=k))
        if cards:
            out.append({"label": label, "scope": scope, "cards": cards})
    return out


def build_match(pages):
    targets = [
        ("Mixed · 6 pairs", "all", 6),
        ("Ch 9 · 6 pairs", "chapter-9", 6),
        ("Ch 10 · 6 pairs", "chapter-10", 6),
        ("Ch 11 · 6 pairs", "chapter-11", 6),
        ("Ch 12 · 6 pairs", "chapter-12", 6),
        ("Ch 13 · 6 pairs", "chapter-13", 6),
    ]
    out = []
    for label, scope, n in targets:
        pairs = _time(f"match: {label}",
                      lambda s=scope, k=n: generate_match_game(pages, scope=s, n=k))
        if pairs:
            out.append({"label": label, "scope": scope, "pairs": pairs})
    return out


def main():
    print(f"Loading wiki…")
    pages = load_pages()
    print(f"  {len(pages)} pages\n")

    print("Building starter quizzes…")
    quizzes = build_quizzes(pages)
    (OUT / "quizzes.json").write_text(json.dumps(quizzes, indent=2), encoding="utf-8")
    print(f"  → {OUT / 'quizzes.json'} ({len(quizzes)} quizzes)\n")

    print("Building starter flashcard decks…")
    decks = build_flashcards(pages)
    (OUT / "flashcards.json").write_text(json.dumps(decks, indent=2), encoding="utf-8")
    print(f"  → {OUT / 'flashcards.json'} ({len(decks)} decks)\n")

    print("Building starter match games…")
    games = build_match(pages)
    (OUT / "match.json").write_text(json.dumps(games, indent=2), encoding="utf-8")
    print(f"  → {OUT / 'match.json'} ({len(games)} games)\n")

    print("Done.")


if __name__ == "__main__":
    main()
