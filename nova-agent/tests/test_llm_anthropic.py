from unittest.mock import MagicMock, patch

from pydantic import BaseModel

from nova_agent.llm.anthropic_client import AnthropicLLM


class _SchemaForTest(BaseModel):
    answer: str


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


@patch("nova_agent.llm.anthropic_client.Anthropic")
def test_anthropic_accepts_and_ignores_response_schema(mock_cls):
    """Anthropic Messages API has no native schema enforcement, so the
    provider must accept `response_schema` without raising and without
    forwarding it to the SDK. Callsites pass it unconditionally for
    cross-provider symmetry."""
    fake_client = MagicMock()
    fake_resp = MagicMock()
    fake_resp.content = [MagicMock(text='{"answer": "ok"}', type="text")]
    fake_resp.usage.input_tokens = 10
    fake_resp.usage.output_tokens = 5
    fake_client.messages.create.return_value = fake_resp
    mock_cls.return_value = fake_client

    llm = AnthropicLLM(api_key="sk-ant-test", model="claude-sonnet-4-6", daily_cap_usd=0)
    llm.complete(
        system="x",
        messages=[{"role": "user", "content": "hi"}],
        response_schema=_SchemaForTest,
    )

    forwarded = fake_client.messages.create.call_args.kwargs
    assert "response_schema" not in forwarded
