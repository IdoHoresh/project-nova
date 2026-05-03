from unittest.mock import MagicMock, patch
from nova_agent.llm.anthropic_client import AnthropicLLM


@patch("nova_agent.llm.anthropic_client.Anthropic")
def test_anthropic_adapter_calls_messages_create(mock_cls):
    fake_client = MagicMock()
    fake_resp = MagicMock()
    fake_resp.content = [MagicMock(text='{"action":"swipe_up"}', type="text")]
    fake_resp.usage.input_tokens = 1000
    fake_resp.usage.output_tokens = 50
    fake_client.messages.create.return_value = fake_resp
    mock_cls.return_value = fake_client

    llm = AnthropicLLM(api_key="sk-ant-test", model="claude-sonnet-4-6", daily_cap_usd=0)
    out, usage = llm.complete(system="be brief", messages=[{"role": "user", "content": "hi"}])
    assert "swipe_up" in out
    assert usage.input_tokens == 1000
