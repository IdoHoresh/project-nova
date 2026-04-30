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
    with pytest.raises(Exception) as exc:
        Settings()
    assert "GOOGLE_API_KEY" in str(exc.value)

def test_settings_default_models(monkeypatch):
    monkeypatch.setenv("GOOGLE_API_KEY", "AIzaSy-test")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
    s = Settings()
    assert s.decision_model == "gemini-2.5-flash"
    assert s.deliberation_model == "gemini-2.5-pro"
    assert s.cheap_vision_model == "gemini-2.5-flash-lite"
    assert s.reflection_model == "claude-sonnet-4-6"
    assert s.demo_model == "claude-opus-4-7"

def test_settings_default_paths(monkeypatch):
    monkeypatch.setenv("GOOGLE_API_KEY", "AIzaSy-test")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
    s = Settings()
    assert str(s.sqlite_path).endswith("nova.db")
    assert str(s.lancedb_path).endswith("lancedb")
