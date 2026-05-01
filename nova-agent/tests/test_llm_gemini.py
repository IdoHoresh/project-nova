from unittest.mock import MagicMock, patch
from nova_agent.llm.gemini_client import GeminiLLM


@patch("nova_agent.llm.gemini_client.genai.Client")
def test_gemini_adapter_calls_generate(mock_cls):
    fake_client = MagicMock()
    fake_resp = MagicMock()
    fake_resp.text = '{"action":"swipe_left"}'
    fake_resp.usage_metadata.prompt_token_count = 1200
    fake_resp.usage_metadata.candidates_token_count = 40
    fake_client.models.generate_content.return_value = fake_resp
    mock_cls.return_value = fake_client

    llm = GeminiLLM(api_key="AIzaSy-test", model="gemini-2.5-flash", daily_cap_usd=0)
    out, usage = llm.complete(system="be brief", messages=[{"role": "user", "content": "hi"}])
    assert "swipe_left" in out
    assert usage.input_tokens == 1200
