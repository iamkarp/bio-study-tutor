"""LLM client — auto-routes between local Ollama and OpenRouter.

Routing rules (in priority order):
1. If OLLAMA_URL is set in env or .env → use local Ollama (offline, free, private).
   Model defaults to OLLAMA_MODEL (e.g. "gemma4:26b" or "gemma4:9b").
2. Otherwise → use OpenRouter with OPENROUTER_API_KEY.
   Model defaults to OPENROUTER_MODEL (e.g. "google/gemma-4-26b-a4b-it").

Both backends speak the OpenAI-compatible /v1/chat/completions protocol, so the
chat(...) function and the rest of the app are unchanged.

To run fully local:
    ollama pull gemma4:26b   # or gemma4:9b for 16GB-RAM laptops
    echo "OLLAMA_URL=http://localhost:11434/v1" >> .env
    echo "OLLAMA_MODEL=gemma4:26b" >> .env

To use the hosted demo backend:
    echo "OPENROUTER_API_KEY=sk-or-v1-..." >> .env
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path

import requests

REPO = Path(__file__).resolve().parents[1]
ENV_PATH = REPO / ".env"

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_DEFAULT_MODEL = "google/gemma-4-26b-a4b-it"
OLLAMA_DEFAULT_MODEL = "gemma4:26b"


def _read_env(key: str) -> str | None:
    """Look up a key in process env first, then .env file."""
    val = os.environ.get(key)
    if val:
        return val
    if ENV_PATH.exists():
        for line in ENV_PATH.read_text().splitlines():
            m = re.match(rf"^\s*{re.escape(key)}\s*=\s*(.+?)\s*$", line)
            if m:
                return m.group(1).strip().strip('"\'')
    return None


def _backend() -> tuple[str, str, dict, str]:
    """Choose backend based on env. Returns (url, model, headers, name)."""
    ollama_url = _read_env("OLLAMA_URL")
    if ollama_url:
        # Local Ollama via OpenAI-compatible endpoint.
        url = ollama_url.rstrip("/")
        if not url.endswith("/v1/chat/completions"):
            if url.endswith("/v1"):
                url = url + "/chat/completions"
            else:
                url = url + "/v1/chat/completions"
        model = _read_env("OLLAMA_MODEL") or OLLAMA_DEFAULT_MODEL
        # Ollama's OpenAI-compat layer accepts any non-empty Authorization header.
        return url, model, {"Authorization": "Bearer ollama",
                            "Content-Type": "application/json"}, "ollama"

    key = _read_env("OPENROUTER_API_KEY")
    if not key:
        raise RuntimeError(
            "No LLM backend configured. Set either OLLAMA_URL (local) or "
            "OPENROUTER_API_KEY (hosted) in env or .env."
        )
    model = _read_env("OPENROUTER_MODEL") or OPENROUTER_DEFAULT_MODEL
    return OPENROUTER_URL, model, {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost",
        "X-Title": "Tutor for Every Course",
    }, "openrouter"


def backend_name() -> str:
    """Return 'ollama' or 'openrouter' — useful for display in the UI."""
    try:
        return _backend()[3]
    except Exception:
        return "unknown"


def backend_model() -> str:
    """Return the model id currently in use — for display."""
    try:
        return _backend()[1]
    except Exception:
        return "unknown"


def chat(messages: list[dict], model: str | None = None,
         temperature: float = 0.4, response_json: bool = False,
         max_tokens: int = 2000) -> str:
    """Send a chat completion request. Returns assistant message content.

    Auto-routes to Ollama or OpenRouter based on env. Both backends speak the
    OpenAI-compatible chat completions protocol.
    """
    url, default_model, headers, name = _backend()
    payload: dict = {
        "model": model or default_model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if response_json:
        # Both Ollama (>=0.5) and OpenRouter accept response_format json_object.
        payload["response_format"] = {"type": "json_object"}

    # Local Ollama can take longer for the first call (model load); give it room.
    timeout = 180 if name == "ollama" else 90
    resp = requests.post(url, headers=headers, data=json.dumps(payload), timeout=timeout)
    if resp.status_code != 200:
        raise RuntimeError(f"{name} error {resp.status_code}: {resp.text[:300]}")
    data = resp.json()
    return data["choices"][0]["message"]["content"]


def extract_json(text: str) -> dict | list:
    """Pull JSON out of an LLM response that may include code fences or prose."""
    text = text.strip()
    m = re.search(r"```(?:json)?\s*(.+?)\s*```", text, re.DOTALL)
    if m:
        text = m.group(1)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    for opener, closer in [("{", "}"), ("[", "]")]:
        first = text.find(opener)
        last = text.rfind(closer)
        if first != -1 and last > first:
            try:
                return json.loads(text[first:last + 1])
            except json.JSONDecodeError:
                continue
    raise ValueError(f"Could not parse JSON from LLM response: {text[:200]!r}")
