from unittest.mock import MagicMock, patch
from nova_agent.llm.gemini_client import GeminiLLM


def _make_fake_client():
    fake_client = MagicMock()
    fake_resp = MagicMock()
    fake_resp.text = '{"action":"swipe_left"}'
    fake_resp.usage_metadata.prompt_token_count = 1200
    fake_resp.usage_metadata.candidates_token_count = 40
    fake_client.models.generate_content.return_value = fake_resp
    return fake_client


@patch("nova_agent.llm.gemini_client.genai.Client")
def test_gemini_adapter_calls_generate(mock_cls):
    fake_client = _make_fake_client()
    mock_cls.return_value = fake_client

    llm = GeminiLLM(api_key="AIzaSy-test", model="gemini-2.5-flash", daily_cap_usd=0)
    out, usage = llm.complete(system="be brief", messages=[{"role": "user", "content": "hi"}])
    assert "swipe_left" in out
    assert usage.input_tokens == 1200


@patch("nova_agent.llm.gemini_client.genai.Client")
def test_gemini_thinking_budget_default_omitted(mock_cls):
    """When thinking_budget is unset, no ThinkingConfig is attached so the model
    uses its own default (dynamic thinking)."""
    fake_client = _make_fake_client()
    mock_cls.return_value = fake_client

    llm = GeminiLLM(api_key="AIzaSy-test", model="gemini-2.5-pro", daily_cap_usd=0)
    llm.complete(system="x", messages=[{"role": "user", "content": "hi"}])

    config = fake_client.models.generate_content.call_args.kwargs["config"]
    assert getattr(config, "thinking_config", None) is None


@patch("nova_agent.llm.gemini_client.genai.Client")
def test_gemini_thinking_budget_zero_disables(mock_cls):
    """thinking_budget=0 must propagate as ThinkingConfig(thinking_budget=0).
    Used by ReactDecider on Flash to free the full output budget for JSON."""
    fake_client = _make_fake_client()
    mock_cls.return_value = fake_client

    llm = GeminiLLM(
        api_key="AIzaSy-test",
        model="gemini-2.5-flash",
        daily_cap_usd=0,
        thinking_budget=0,
    )
    llm.complete(system="x", messages=[{"role": "user", "content": "hi"}])

    config = fake_client.models.generate_content.call_args.kwargs["config"]
    assert config.thinking_config is not None
    assert config.thinking_config.thinking_budget == 0
