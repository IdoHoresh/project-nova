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


def test_react_decider_preserves_image_when_screenshot_present() -> None:
    """Regression: non-empty screenshot_b64 must produce an image block in the
    user message. Live emulator path always passes a real screenshot; this test
    ensures that path is not accidentally broken by the optional-screenshot refactor."""
    fake_llm = MockLLMClient()
    board = BoardState(grid=[[2, 0, 0, 0]] + [[0] * 4] * 3, score=0)
    decider = ReactDecider(llm=fake_llm)
    decider.decide_with_context(
        board=board,
        screenshot_b64="dGVzdA==",  # non-empty base64
        memories=[],
    )
    last_messages = fake_llm.calls[-1]["messages"]
    assert len(last_messages) == 1
    assert last_messages[0]["role"] == "user"
    content = last_messages[0]["content"]
    assert any(block.get("type") == "image" for block in content)
    assert any(block.get("type") == "text" for block in content)


def test_react_decider_handles_screenshot_none() -> None:
    """Phase 0.7 runs on Game2048Sim which produces no pixels.
    ReactDecider must accept screenshot_b64=None without crashing.
    Verify the user-message content has no image block when screenshot omitted."""
    fake_llm = MockLLMClient()
    board = BoardState(grid=[[2, 0, 0, 0]] + [[0] * 4] * 3, score=0)
    decider = ReactDecider(llm=fake_llm)
    decision = decider.decide_with_context(
        board=board,
        screenshot_b64=None,
        memories=[],
    )
    assert decision.action in {"swipe_up", "swipe_down", "swipe_left", "swipe_right"}
    last_messages = fake_llm.calls[-1]["messages"]
    assert len(last_messages) == 1
    assert last_messages[0]["role"] == "user"
    assert all(block.get("type") != "image" for block in last_messages[0]["content"])


def test_react_decider_handles_screenshot_empty_string() -> None:
    """Empty string is treated identically to None — no image block in the
    user message content."""
    fake_llm = MockLLMClient()
    board = BoardState(grid=[[2, 0, 0, 0]] + [[0] * 4] * 3, score=0)
    decider = ReactDecider(llm=fake_llm)
    decision = decider.decide_with_context(
        board=board,
        screenshot_b64="",
        memories=[],
    )
    assert decision.action in {"swipe_up", "swipe_down", "swipe_left", "swipe_right"}
    last_messages = fake_llm.calls[-1]["messages"]
    assert all(block.get("type") != "image" for block in last_messages[0]["content"])
