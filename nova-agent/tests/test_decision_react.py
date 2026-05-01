from nova_agent.decision.react import Decision, ReactDecider
from nova_agent.llm.mock import MockLLMClient
from nova_agent.perception.types import BoardState


def test_react_returns_valid_action() -> None:
    fake_llm = MockLLMClient(
        script=[
            '{"observation":"two 2s","reasoning":"merge them","action":"swipe_right","confidence":"high"}',
        ],
    )
    decider = ReactDecider(llm=fake_llm)
    board = BoardState(
        grid=[[0, 2, 0, 0], [0, 0, 0, 2], [0, 0, 0, 0], [0, 0, 0, 0]],
        score=0,
    )
    result = decider.decide(board=board, screenshot_b64="ignored")
    assert isinstance(result, Decision)
    assert result.action == "swipe_right"
    assert "merge" in result.reasoning.lower()


def test_react_routes_to_decision_role_by_default() -> None:
    """No script: MockLLMClient must identify the decision role by fingerprint
    in SYSTEM_PROMPT_V1. This is the regression test for prompt-template drift —
    if the system prompt is rewritten and loses the fingerprint phrase, the
    strict mock raises and this test fails loudly."""
    fake_llm = MockLLMClient()
    decider = ReactDecider(llm=fake_llm)
    board = BoardState(grid=[[0] * 4 for _ in range(4)], score=0)
    result = decider.decide(board=board, screenshot_b64="ignored")
    assert result.action in {"swipe_up", "swipe_down", "swipe_left", "swipe_right"}
    assert len(fake_llm.calls) == 1
