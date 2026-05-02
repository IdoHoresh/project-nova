from nova_agent.llm.mock import MockLLMClient


def test_script_returns_in_order():
    m = MockLLMClient(script=['{"action":"swipe_up"}', '{"action":"swipe_down"}'])
    a, _ = m.complete(system="x", messages=[{"role": "user", "content": "go"}])
    b, _ = m.complete(system="x", messages=[{"role": "user", "content": "go"}])
    assert a == '{"action":"swipe_up"}'
    assert b == '{"action":"swipe_down"}'


def test_keyed_matches_substring():
    m = MockLLMClient(keyed={"trauma": '{"action":"swipe_left"}'})
    out, _ = m.complete(
        system="x", messages=[{"role": "user", "content": "you remember a trauma board"}]
    )
    assert out == '{"action":"swipe_left"}'


def test_calls_recorded():
    # Strict-mode default requires a recognized role fingerprint in the system prompt;
    # use the decision-role fingerprint so the call routes to the default factory.
    # Fingerprint was rewritten 2026-05-02 from the prose phrase
    # "emit Observation, Reasoning, Action" to the schema field name
    # `"observation":` (more stable across prompt rewrites).
    m = MockLLMClient()
    m.complete(
        system='schema: { "observation": "..." }',
        messages=[{"role": "user", "content": "hi"}],
    )
    assert len(m.calls) == 1
