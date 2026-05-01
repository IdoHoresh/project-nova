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


def test_production_uses_pro_for_tot(monkeypatch):
    monkeypatch.setenv("NOVA_TIER", "production")
    assert tiers.model_for("tot") == "gemini-2.5-pro"


def test_demo_is_sonnet_only_for_decisions(monkeypatch):
    monkeypatch.setenv("NOVA_TIER", "demo")
    assert tiers.model_for("decision") == "claude-sonnet-4-6"
