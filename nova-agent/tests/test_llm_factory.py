import pytest
from nova_agent.llm.factory import build_llm


def test_factory_gemini_for_gemini_model():
    llm = build_llm(
        model="gemini-2.5-flash",
        google_api_key="AIzaSy-test",
        anthropic_api_key="",
        daily_cap_usd=0,
    )
    assert llm.__class__.__name__ == "GeminiLLM"


def test_factory_anthropic_for_claude_model():
    llm = build_llm(
        model="claude-sonnet-4-6",
        google_api_key="",
        anthropic_api_key="sk-ant-test",
        daily_cap_usd=0,
    )
    assert llm.__class__.__name__ == "AnthropicLLM"


def test_factory_raises_on_unknown_model():
    with pytest.raises(ValueError):
        build_llm(model="gpt-9000", google_api_key="x", anthropic_api_key="y", daily_cap_usd=0)
