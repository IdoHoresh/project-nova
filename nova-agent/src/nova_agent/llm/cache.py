"""Fixture-replay LLM cache (§6.6 L1).

Cache key = sha256(rendered_prompt_string + model + temperature + response_schema_hash).
Writes are gated on smoke-pass — buggy build cannot pollute future runs.
NOVA_CACHE controls behavior: "off" disables; "replay" reads only; default
"record" reads + writes (gated by `mark_smoke_pass()`).
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from dataclasses import dataclass
from pathlib import Path

CACHE_DIR = Path(os.environ.get("NOVA_CACHE_DIR", ".cache/llm"))
CACHE_MODE = os.environ.get("NOVA_CACHE", "record")  # off | replay | record

_smoke_passed = False


def mark_smoke_pass() -> None:
    """Called by the smoke gauntlet after every assertion passes.
    Cache writes only happen when this flag is set in the current process.
    """
    global _smoke_passed
    _smoke_passed = True


def _hash_key(*, rendered_prompt: str, model: str, temperature: float, schema_hash: str) -> str:
    payload = json.dumps({
        "p": rendered_prompt,
        "m": model,
        "t": round(temperature, 4),
        "s": schema_hash,
    }, sort_keys=True).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


@dataclass
class CacheHit:
    response_text: str
    cached_at: float
    key: str


def _key_path(key: str) -> Path:
    return CACHE_DIR / f"{key[:2]}" / f"{key}.json"


def get(*, rendered_prompt: str, model: str, temperature: float, schema_hash: str = "") -> CacheHit | None:
    if CACHE_MODE == "off":
        return None
    key = _hash_key(rendered_prompt=rendered_prompt, model=model,
                    temperature=temperature, schema_hash=schema_hash)
    p = _key_path(key)
    if not p.exists():
        return None
    data = json.loads(p.read_text())
    return CacheHit(response_text=data["response_text"], cached_at=data["cached_at"], key=key)


def put(*, rendered_prompt: str, model: str, temperature: float, response_text: str,
        schema_hash: str = "") -> None:
    if CACHE_MODE in ("off", "replay"):
        return
    if not _smoke_passed:
        # writes gated on smoke-pass — protects against poisoning the cache
        return
    key = _hash_key(rendered_prompt=rendered_prompt, model=model,
                    temperature=temperature, schema_hash=schema_hash)
    p = _key_path(key)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({
        "response_text": response_text,
        "cached_at": time.time(),
        "model": model,
        "temperature": temperature,
    }))
