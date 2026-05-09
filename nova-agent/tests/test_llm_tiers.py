import pytest
from nova_agent.llm import tiers


def test_default_is_dev(monkeypatch):
    monkeypatch.delenv("NOVA_TIER", raising=False)
    assert tiers.current_tier() == "dev"


def test_invalid_raises(monkeypatch):
    monkeypatch.setenv("NOVA_TIER", "moonshot")
    with pytest.raises(ValueError):
        tiers.current_tier()


def test_dev_uses_flash_for_decision(monkeypatch):
    monkeypatch.setenv("NOVA_TIER", "dev")
    assert tiers.model_for("decision") == "gemini-2.5-flash"


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


def test_phase_0_7a_routes_all_cognitive_roles_to_gemini_pro(monkeypatch):
    """Phase 0.7a counterfactual run (spec 2026-05-09-phase-0.7a-counterfactual-design.md
    §2.2) must run gemini-2.5-pro paid tier on every cognitive role to
    reproduce the 2026-05-06 morning-pilot model surface while testing the
    null_empty_cells_anxiety_term ablation. ADR-0006 Amendment 1 moved
    production-tier ToT off Pro for daily-quota reasons; Phase 0.7a is a
    one-shot N=15 run (~1575 calls) that runs on paid Pro to disambiguate
    C1 (mechanical empty_cells dominance) from C6B (Gemini-specific
    reasoning failure on the recalibrated grids)."""
    monkeypatch.setenv("NOVA_TIER", "phase_0_7a")
    assert tiers.model_for("decision") == "gemini-2.5-pro"
    assert tiers.model_for("tot") == "gemini-2.5-pro"
    assert tiers.model_for("reflection") == "gemini-2.5-pro"
    assert tiers.model_for("perception_fallback") == "gemini-2.5-pro"
    # importance_rating stays on flash-lite for cost: it's a memory-write
    # ranker, not a cognitive-judgment role, and routing it to Pro would
    # roughly triple the per-trial call cost without changing the
    # counterfactual signal under test.
    assert tiers.model_for("importance_rating") == "gemini-2.5-flash-lite"
    # tot_branches=4 matches the original ADR-0006 production-tier setting
    # the morning pilot ran with, so the counterfactual reproduces the
    # morning-pilot ToT depth exactly.
    assert tiers.model_for("tot_branches") == 4
