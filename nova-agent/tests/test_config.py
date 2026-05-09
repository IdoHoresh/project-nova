import pytest
from nova_agent.config import Settings


def test_settings_loads_from_env(monkeypatch):
    monkeypatch.setenv("GOOGLE_API_KEY", "AIzaSy-real-looking-key")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-real-looking-key")
    monkeypatch.setenv("NOVA_WS_PORT", "9999")
    s = Settings()
    assert s.google_api_key == "AIzaSy-real-looking-key"
    assert s.anthropic_api_key == "sk-ant-real-looking-key"
    assert s.ws_port == 9999


def test_settings_fails_without_google_key(monkeypatch):
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
    # Suppress on-disk .env discovery so the test only sees env vars.
    # Without this, find_dotenv() walks up to the repo-root `.env` and
    # loads a real GOOGLE_API_KEY, which would mask the missing-key path.
    with pytest.raises(Exception) as exc:
        Settings(_env_file=None)  # type: ignore[call-arg]
    assert "GOOGLE_API_KEY" in str(exc.value)


def test_settings_default_models(monkeypatch):
    monkeypatch.setenv("GOOGLE_API_KEY", "AIzaSy-test")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
    # `_env_file=None` isolates from any developer-local .env overrides
    # (e.g. NOVA_DELIBERATION_MODEL) that would otherwise shadow the
    # constructor defaults this test asserts on. Same pattern as
    # test_settings_fails_without_google_key above.
    s = Settings(_env_file=None)  # type: ignore[call-arg]
    assert s.decision_model == "gemini-2.5-flash"
    assert s.deliberation_model == "gemini-2.5-pro"
    assert s.cheap_vision_model == "gemini-2.5-flash-lite"
    assert s.reflection_model == "claude-sonnet-4-6"
    assert s.demo_model == "claude-opus-4-7"


def test_settings_default_paths(monkeypatch):
    monkeypatch.setenv("GOOGLE_API_KEY", "AIzaSy-test")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
    s = Settings(_env_file=None)  # type: ignore[call-arg]
    assert str(s.sqlite_path).endswith("nova.db")
    assert str(s.lancedb_path).endswith("lancedb")


def test_settings_default_null_empty_cells_anxiety_term_is_false(monkeypatch):
    """Production runs must default to the full formula. Spec §4.1.

    Asserts the new ablation field exists on Settings AND defaults to False
    so a missing env var keeps the empty_cells anxiety term active.
    """
    monkeypatch.setenv("GOOGLE_API_KEY", "AIzaSy-test")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
    monkeypatch.delenv("NOVA_NULL_EMPTY_CELLS_ANXIETY_TERM", raising=False)
    s = Settings(_env_file=None)  # type: ignore[call-arg]
    assert s.null_empty_cells_anxiety_term is False


def test_settings_null_empty_cells_anxiety_term_reads_env(monkeypatch):
    """pydantic-settings parses NOVA_NULL_EMPTY_CELLS_ANXIETY_TERM=1 to True
    via standard bool coercion. Spec §2.1.
    """
    monkeypatch.setenv("GOOGLE_API_KEY", "AIzaSy-test")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
    monkeypatch.setenv("NOVA_NULL_EMPTY_CELLS_ANXIETY_TERM", "1")
    s = Settings(_env_file=None)  # type: ignore[call-arg]
    assert s.null_empty_cells_anxiety_term is True


def test_settings_default_per_call_cost_abort_is_50_cents(monkeypatch):
    """Phase 0.7a §5.2: per-call cost-abort gate defaults to $0.50/call.

    Production runs (Phase 0.7a paid Gemini Pro pilot) get the abort gate
    armed without an explicit env override. Set to 0 to disable.
    """
    monkeypatch.setenv("GOOGLE_API_KEY", "AIzaSy-test")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
    monkeypatch.delenv("NOVA_PER_CALL_COST_ABORT_USD", raising=False)
    s = Settings(_env_file=None)  # type: ignore[call-arg]
    assert s.per_call_cost_abort_usd == 0.50


def test_settings_per_call_cost_abort_reads_env(monkeypatch):
    """NOVA_PER_CALL_COST_ABORT_USD overrides the default."""
    monkeypatch.setenv("GOOGLE_API_KEY", "AIzaSy-test")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
    monkeypatch.setenv("NOVA_PER_CALL_COST_ABORT_USD", "0.25")
    s = Settings(_env_file=None)  # type: ignore[call-arg]
    assert s.per_call_cost_abort_usd == 0.25
