import os
import pytest

@pytest.fixture(autouse=True)
def stub_env(monkeypatch):
    """Provide safe defaults so unit tests don't accidentally hit real APIs."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test-fake-key-do-not-use")
    monkeypatch.setenv("NOVA_DAILY_BUDGET_USD", "0.00")  # 0 = unlimited in tests
    monkeypatch.setenv("NOVA_LOG_LEVEL", "WARNING")
