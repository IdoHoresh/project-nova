import pytest
from nova_agent.llm import tiers


def test_default_is_dev(monkeypatch):
    monkeypatch.delenv("NOVA_TIER", raising=False)
    assert tiers.current_tier() == "dev"


def test_invalid_raises(monkeypatch):
    monkeypatch.setenv("NOVA_TIER", "moonshot")
    with pytest.raises(ValueError):
        tiers.current_tier()


def test_dev_uses_haiku_for_decision(monkeypatch):
    monkeypatch.setenv("NOVA_TIER", "dev")
    assert tiers.model_for("decision") == "claude-haiku-4-5"


def test_production_uses_sonnet_for_tot(monkeypatch):
    """Production-tier ToT runs on Claude Sonnet 4.6 per ADR-0006 Amendment 1.

    Original ADR-0006 mapped this to gemini-2.5-pro. The amendment moved
    ToT to Sonnet because Pro's 1000 RPD daily quota cannot absorb the
    Phase 0.7 N=20 workload and rate-limit clustering at any non-trivial
    concurrency produced a 20% Carla trial-abort rate in the 2026-05-06
    pilot. See ADR-0006 Amendment 1 for the full rationale.
    """
    monkeypatch.setenv("NOVA_TIER", "production")
    assert tiers.model_for("tot") == "claude-sonnet-4-6"


def test_demo_is_sonnet_only_for_decisions(monkeypatch):
    monkeypatch.setenv("NOVA_TIER", "demo")
    assert tiers.model_for("decision") == "claude-sonnet-4-6"


def test_plumbing_routes_everything_to_flash_lite(monkeypatch):
    """plumbing tier (UI dev / smoke / infra-only) uses flash-lite for
    every cognitive role. Safe ONLY because callsites pass response_schema —
    do not unset NOVA_TIER=plumbing while tuning Arbiter or evaluating
    ToT quality."""
    monkeypatch.setenv("NOVA_TIER", "plumbing")
    assert tiers.model_for("decision") == "gemini-2.5-flash-lite"
    assert tiers.model_for("tot") == "gemini-2.5-flash-lite"
    assert tiers.model_for("reflection") == "gemini-2.5-flash-lite"
    assert tiers.model_for("perception_fallback") == "gemini-2.5-flash-lite"
    assert tiers.model_for("importance_rating") == "gemini-2.5-flash-lite"


def test_plumbing_uses_fewer_tot_branches(monkeypatch):
    """plumbing trims tot_branches to 2 to keep the per-decision cost
    proportional to the savings from cheaper-per-call models."""
    monkeypatch.setenv("NOVA_TIER", "plumbing")
    assert tiers.model_for("tot_branches") == 2
