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
    m = MockLLMClient()
    m.complete(
        system="emit Observation, Reasoning, Action",
        messages=[{"role": "user", "content": "hi"}],
    )
    assert len(m.calls) == 1
