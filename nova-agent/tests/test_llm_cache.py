"""Smoke tests for the fixture-replay cache (§6.6 L1).

The cache write path is gated on `mark_smoke_pass()`. Tests verify:
  - hash key is deterministic
  - get/put roundtrip when smoke passed
  - put is no-op when smoke not passed (poison protection)
"""

from pathlib import Path

import pytest

from nova_agent.llm import cache as llm_cache


@pytest.fixture
def cache_in_tmp(monkeypatch, tmp_path: Path):
    """Point the cache at a tmp dir, reset module-level smoke-pass flag."""
    monkeypatch.setenv("NOVA_CACHE", "record")
    monkeypatch.setattr(llm_cache, "CACHE_DIR", tmp_path / "llm")
    monkeypatch.setattr(llm_cache, "_smoke_passed", False)
    yield tmp_path / "llm"


def test_get_returns_none_when_missing(cache_in_tmp):
    assert llm_cache.get(rendered_prompt="hi", model="m", temperature=0.1) is None


def test_put_skipped_until_smoke_passes(cache_in_tmp):
    llm_cache.put(rendered_prompt="hi", model="m", temperature=0.1, response_text="resp")
    # No write happened — poison protection
    assert llm_cache.get(rendered_prompt="hi", model="m", temperature=0.1) is None


def test_put_then_get_after_smoke(cache_in_tmp, monkeypatch):
    monkeypatch.setattr(llm_cache, "_smoke_passed", True)
    llm_cache.put(rendered_prompt="hi", model="m", temperature=0.1, response_text="resp")
    hit = llm_cache.get(rendered_prompt="hi", model="m", temperature=0.1)
    assert hit is not None
    assert hit.response_text == "resp"


def test_off_mode_disables_get(cache_in_tmp, monkeypatch):
    monkeypatch.setattr(llm_cache, "CACHE_MODE", "off")
    monkeypatch.setattr(llm_cache, "_smoke_passed", True)
    llm_cache.put(rendered_prompt="hi", model="m", temperature=0.1, response_text="resp")
    # In "off" mode, put is also no-op
    monkeypatch.setattr(llm_cache, "CACHE_MODE", "off")
    assert llm_cache.get(rendered_prompt="hi", model="m", temperature=0.1) is None


def test_hash_key_changes_with_inputs():
    k1 = llm_cache._hash_key(rendered_prompt="a", model="m", temperature=0.1, schema_hash="")
    k2 = llm_cache._hash_key(rendered_prompt="b", model="m", temperature=0.1, schema_hash="")
    k3 = llm_cache._hash_key(rendered_prompt="a", model="m", temperature=0.2, schema_hash="")
    assert k1 != k2
    assert k1 != k3
