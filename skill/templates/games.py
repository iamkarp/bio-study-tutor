"""LLM-driven quiz and flashcard generators."""
from __future__ import annotations

import random
from typing import Any

from kg_loader import Page, corpus_text
from llm import chat, extract_json


def _scope_context(pages: dict[str, Page], scope: str) -> str:
    """Convert a scope selector ('chapter-9', 'all', 'type-process') to corpus text."""
    if scope == "all" or not scope:
        return corpus_text(pages, max_chars=40000)
    if scope.startswith("chapter-"):
        try:
            ch = int(scope.split("-", 1)[1])
            return corpus_text(pages, chapter=ch, max_chars=40000)
        except ValueError:
            pass
    if scope.startswith("type-"):
        return corpus_text(pages, node_type=scope.split("-", 1)[1], max_chars=40000)
    return corpus_text(pages, max_chars=40000)


def generate_quiz(pages: dict[str, Page], scope: str = "all",
                  n: int = 5, difficulty: str = "medium") -> list[dict[str, Any]]:
    """Return a list of quiz questions:
       [{question, choices: [4], answer_index: 0..3, explanation}].
    """
    ctx = _scope_context(pages, scope)
    seed = random.randint(1000, 9999)
    sys = (
        "You are a biology professor writing exam questions for Bio 1320 Exam 3 "
        "(Chapters 9–13: Meiosis, Inheritance, DNA Structure & Replication, How Genes Work, "
        "New Biology / Biotechnology). Write multiple-choice questions grounded in the "
        "provided study material. Questions should test understanding, not just recall. "
        "Each question must have exactly 4 plausible choices, only one correct."
    )
    user = (
        f"Material:\n{ctx}\n\n"
        f"Generate {n} {difficulty}-difficulty multiple-choice questions covering different "
        f"topics from the material above (use seed {seed} to vary your selections). "
        f"Return STRICTLY valid JSON in this shape:\n"
        f'{{"questions": [{{"question": "...", "choices": ["A", "B", "C", "D"], '
        f'"answer_index": 0, "explanation": "..."}}, ...]}}\n'
        f"answer_index is the 0-based index of the correct choice. "
        f"explanation should be 1–2 sentences citing specific facts."
    )
    raw = chat(
        [{"role": "system", "content": sys}, {"role": "user", "content": user}],
        temperature=0.7, response_json=True, max_tokens=2500,
    )
    data = extract_json(raw)
    if isinstance(data, list):
        return data
    return data.get("questions", [])


def generate_flashcards(pages: dict[str, Page], scope: str = "all",
                        n: int = 10) -> list[dict[str, str]]:
    """Return a list of flashcards: [{front, back}]."""
    ctx = _scope_context(pages, scope)
    seed = random.randint(1000, 9999)
    sys = (
        "You are creating study flashcards for Bio 1320 Exam 3. Each flashcard has a "
        "FRONT (a question, term, or prompt) and a BACK (a complete, exam-ready answer). "
        "Cards should be concise but information-dense; the back should fit on a 3x5 card."
    )
    user = (
        f"Material:\n{ctx}\n\n"
        f"Generate {n} flashcards drawn from this material (seed {seed}). Vary across "
        f"vocabulary terms, processes, comparisons, and worked examples. Return STRICTLY "
        f'valid JSON: {{"cards": [{{"front": "...", "back": "..."}}, ...]}}'
    )
    raw = chat(
        [{"role": "system", "content": sys}, {"role": "user", "content": user}],
        temperature=0.6, response_json=True, max_tokens=2500,
    )
    data = extract_json(raw)
    if isinstance(data, list):
        return data
    return data.get("cards", [])


def generate_match_game(pages: dict[str, Page], scope: str = "all",
                        n: int = 6) -> list[dict[str, str]]:
    """Return n pairs for a matching game: [{term, definition}]."""
    ctx = _scope_context(pages, scope)
    seed = random.randint(1000, 9999)
    sys = (
        "You generate matching-game pairs for biology study. Each pair is a term "
        "(very short — 1–4 words) and a definition (one tight sentence)."
    )
    user = (
        f"Material:\n{ctx}\n\n"
        f"Generate {n} term/definition pairs from the material above (seed {seed}). "
        f'Return JSON: {{"pairs": [{{"term": "...", "definition": "..."}}, ...]}}'
    )
    raw = chat(
        [{"role": "system", "content": sys}, {"role": "user", "content": user}],
        temperature=0.5, response_json=True, max_tokens=1500,
    )
    data = extract_json(raw)
    if isinstance(data, list):
        return data
    return data.get("pairs", [])


def answer_question(pages: dict[str, Page], question: str,
                    history: list[dict] | None = None) -> str:
    """Free-form Q&A grounded in the wiki."""
    ctx = corpus_text(pages, max_chars=80000)
    sys = (
        "You are a biology tutor for Bio 1320 (Cells, Genetics, and Biotechnology). "
        "Answer the student's question using ONLY the study material provided. If the "
        "question is outside that scope, say so and suggest the closest topic that IS "
        "covered. Be concrete: cite specific terms, processes, and chapter context. "
        "Format with markdown when it helps comprehension. Keep answers focused — "
        "thoroughness without padding."
    )
    messages = [{"role": "system", "content": sys},
                {"role": "user", "content": f"Study material:\n{ctx}\n\n---\n\n"}]
    if history:
        messages.extend(history)
    messages.append({"role": "user", "content": question})
    return chat(messages, temperature=0.3, max_tokens=1500)
