"""
LLM client for the study app.

Backend selection order (first match wins):
1. LMSTUDIO_URL set  → LM Studio (or any OpenAI-compatible local server)
2. OLLAMA_URL set    → Ollama
3. ANTHROPIC_API_KEY → Claude via Anthropic API
4. CLAUDE_CODE_CLI=1 → pipe through `claude` CLI (no API key needed)
5. OPENROUTER_API_KEY → OpenRouter (default: google/gemma-4-26b-a4b-it)

Set ONE of the above in your .env file or shell environment.
Override the model with LLM_MODEL=<model-id> in .env.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import urllib.request
import urllib.error
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
ENV_PATH = REPO / ".env"


def _load_env() -> dict[str, str]:
    env: dict[str, str] = {}
    if ENV_PATH.exists():
        for line in ENV_PATH.read_text().splitlines():
            m = re.match(r"^\s*([A-Z0-9_]+)\s*=\s*(.+?)\s*$", line)
            if m:
                env[m.group(1)] = m.group(2).strip().strip('"\'')
    return env


_ENV = _load_env()


def _e(key: str, fallback: str = "") -> str:
    return os.environ.get(key) or _ENV.get(key, fallback)


def _backend() -> str:
    if _e("LMSTUDIO_URL"):
        return "lmstudio"
    if _e("OLLAMA_URL"):
        return "ollama"
    if _e("ANTHROPIC_API_KEY"):
        return "anthropic"
    if _e("CLAUDE_CODE_CLI"):
        return "claude_cli"
    if _e("OPENROUTER_API_KEY"):
        return "openrouter"
    raise RuntimeError(
        "No LLM backend configured. Set one of: LMSTUDIO_URL, OLLAMA_URL, "
        "ANTHROPIC_API_KEY, CLAUDE_CODE_CLI=1, or OPENROUTER_API_KEY in .env"
    )


def _openai_compat(
    base_url: str, api_key: str, model: str,
    messages: list[dict], temperature: float, max_tokens: int,
    response_json: bool, extra_headers: dict | None = None,
) -> str:
    payload = {
        "model": model, "messages": messages,
        "temperature": temperature, "max_tokens": max_tokens,
    }
    if response_json:
        payload["response_format"] = {"type": "json_object"}
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        **(extra_headers or {}),
    }
    req = urllib.request.Request(
        f"{base_url}/chat/completions",
        data=json.dumps(payload).encode(),
        headers=headers,
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            return json.loads(resp.read())["choices"][0]["message"]["content"]
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"LLM HTTP {e.code}: {e.read()[:300]}") from e


def _anthropic(messages: list[dict], model: str, temperature: float, max_tokens: int) -> str:
    system, conv = "", []
    for m in messages:
        (conv if m["role"] != "system" else []).append(m) if m["role"] != "system" else None
        if m["role"] == "system":
            system = m["content"]
        else:
            conv.append(m)
    payload: dict = {"model": model, "max_tokens": max_tokens, "temperature": temperature, "messages": conv}
    if system:
        payload["system"] = system
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=json.dumps(payload).encode(),
        headers={"x-api-key": _e("ANTHROPIC_API_KEY"), "anthropic-version": "2023-06-01", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            return json.loads(resp.read())["content"][0]["text"]
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"Anthropic API {e.code}: {e.read()[:300]}") from e


def _claude_cli(messages: list[dict]) -> str:
    """Route through the `claude` CLI — uses Claude Code session, no API key needed."""
    prompt = "\n\n".join(f"[{m['role'].upper()}]\n{m['content']}" for m in messages)
    result = subprocess.run(
        ["claude", "--print", "--no-markdown", "-"],
        input=prompt, capture_output=True, text=True, timeout=120,
    )
    if result.returncode != 0:
        raise RuntimeError(f"claude CLI error: {result.stderr[:300]}")
    return result.stdout.strip()


def chat(
    messages: list[dict],
    model: str | None = None,
    temperature: float = 0.4,
    response_json: bool = False,
    max_tokens: int = 2000,
) -> str:
    """Send a chat completion. Returns assistant message content.

    Backend is auto-selected from env vars (see module docstring).
    Override the model with LLM_MODEL=<id> in .env or the model arg.
    """
    backend = _backend()
    m = model or _e("LLM_MODEL")

    if backend == "lmstudio":
        url = _e("LMSTUDIO_URL", "http://localhost:1234/v1")
        if not m:
            try:
                req = urllib.request.Request(f"{url}/models", headers={"Authorization": "Bearer not-needed"})
                with urllib.request.urlopen(req, timeout=5) as r:
                    loaded = [x["id"] for x in json.loads(r.read()).get("data", []) if "embedding" not in x["id"].lower()]
                    m = loaded[0] if loaded else "local-model"
            except Exception:
                m = "local-model"
        return _openai_compat(url, "not-needed", m, messages, temperature, max_tokens, response_json)

    if backend == "ollama":
        return _openai_compat(
            _e("OLLAMA_URL", "http://localhost:11434/v1"), "ollama",
            m or _e("OLLAMA_MODEL", "gemma4:26b"),
            messages, temperature, max_tokens, response_json,
        )

    if backend == "anthropic":
        return _anthropic(messages, m or "claude-sonnet-4-6", temperature, max_tokens)

    if backend == "claude_cli":
        return _claude_cli(messages)

    if backend == "openrouter":
        return _openai_compat(
            "https://openrouter.ai/api/v1", _e("OPENROUTER_API_KEY"),
            m or "google/gemma-4-26b-a4b-it",
            messages, temperature, max_tokens, response_json,
            extra_headers={"HTTP-Referer": "http://localhost", "X-Title": "Study Tutor"},
        )

    raise RuntimeError(f"Unknown backend: {backend}")


def extract_json(text: str) -> dict | list:
    """Pull JSON out of a response that may include code fences or prose."""
    text = text.strip()
    fence = re.search(r"```(?:json)?\s*(.+?)\s*```", text, re.DOTALL)
    if fence:
        text = fence.group(1)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    for opener, closer in [("{", "}"), ("[", "]")]:
        a, b = text.find(opener), text.rfind(closer)
        if a != -1 and b > a:
            try:
                return json.loads(text[a:b + 1])
            except json.JSONDecodeError:
                continue
    raise ValueError(f"Could not parse JSON from response: {text[:200]!r}")
