"""OpenRouter client for the study app."""
from __future__ import annotations

import json
import os
import re
from pathlib import Path

import requests

REPO = Path(__file__).resolve().parents[1]
ENV_PATH = REPO / ".env"

DEFAULT_MODEL = os.environ.get("OPENROUTER_MODEL", "google/gemma-4-26b-a4b-it")
URL = "https://openrouter.ai/api/v1/chat/completions"


def _load_api_key() -> str:
    key = os.environ.get("OPENROUTER_API_KEY")
    if key:
        return key
    if ENV_PATH.exists():
        for line in ENV_PATH.read_text().splitlines():
            m = re.match(r"^\s*OPENROUTER_API_KEY\s*=\s*(.+?)\s*$", line)
            if m:
                return m.group(1).strip().strip('"\'')
    raise RuntimeError("OPENROUTER_API_KEY not found in env or .env file")


def chat(messages: list[dict], model: str | None = None,
         temperature: float = 0.4, response_json: bool = False,
         max_tokens: int = 2000) -> str:
    """Send a chat completion request. Returns assistant message content."""
    key = _load_api_key()
    payload: dict = {
        "model": model or DEFAULT_MODEL,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if response_json:
        payload["response_format"] = {"type": "json_object"}
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost",
        "X-Title": "Bio 1320 Study Guide",
    }
    resp = requests.post(URL, headers=headers, data=json.dumps(payload), timeout=90)
    if resp.status_code != 200:
        raise RuntimeError(f"OpenRouter error {resp.status_code}: {resp.text[:300]}")
    data = resp.json()
    return data["choices"][0]["message"]["content"]


def extract_json(text: str) -> dict | list:
    """Try to pull JSON out of an LLM response that may include code fences or prose."""
    text = text.strip()
    # Strip ```json ... ``` fences
    m = re.search(r"```(?:json)?\s*(.+?)\s*```", text, re.DOTALL)
    if m:
        text = m.group(1)
    # First try direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # Fallback: find the outermost JSON object/array
    for opener, closer in [("{", "}"), ("[", "]")]:
        first = text.find(opener)
        last = text.rfind(closer)
        if first != -1 and last > first:
            try:
                return json.loads(text[first:last + 1])
            except json.JSONDecodeError:
                continue
    raise ValueError(f"Could not parse JSON from LLM response: {text[:200]!r}")
