import asyncio
from unittest.mock import AsyncMock, MagicMock

from nova_agent.decision.tot import ToTDecider
from nova_agent.llm.protocol import Usage
from nova_agent.perception.types import BoardState


def _llm_with_branches(values: list[float]) -> MagicMock:
    fake = MagicMock()
    fake.model = "test-model"
    fake.complete.side_effect = [
        (
            f'{{"action":"swipe_{d}","reasoning":"r","value":{v}}}',
            Usage(input_tokens=100, output_tokens=20, model="test-model"),
        )
        for d, v in zip(["up", "down", "left", "right"], values)
    ]
    return fake


def _board() -> BoardState:
    return BoardState(grid=[[0, 2, 0, 0]] + [[0] * 4 for _ in range(3)], score=0)


def test_tot_returns_best_branch() -> None:
    fake_llm = _llm_with_branches([0.7, 0.1, 0.4])
    bus = MagicMock()
    bus.publish = AsyncMock()
    decider = ToTDecider(llm=fake_llm, bus=bus)
    decision = asyncio.run(decider.decide(board=_board(), screenshot_b64="x", num_branches=3))
    assert decision.action == "swipe_up"


def test_tot_publishes_branch_event_per_candidate() -> None:
    """§3.8 — branches stream to brain panel as they evaluate."""
    fake_llm = _llm_with_branches([0.5, 0.6, 0.4])
    bus = MagicMock()
    bus.publish = AsyncMock()
    decider = ToTDecider(llm=fake_llm, bus=bus)
    asyncio.run(decider.decide(board=_board(), screenshot_b64="x", num_branches=3))

    branch_calls = [c for c in bus.publish.await_args_list if c.args[0] == "tot_branch"]
    select_calls = [c for c in bus.publish.await_args_list if c.args[0] == "tot_selected"]
    assert len(branch_calls) == 3
    assert len(select_calls) == 1


def test_tot_branch_evaluator_does_not_write_memory() -> None:
    """§3.4 read-only constraint — branches must never call memory.write_*."""
    from nova_agent.decision import tot as tot_module

    src = tot_module.__file__ or ""
    code = open(src).read()
    assert "memory.write_move" not in code
    assert "memory.write_reflection" not in code
    assert "memory.tag_aversive" not in code


def test_tot_selected_event_carries_branch_values() -> None:
    fake_llm = _llm_with_branches([0.3, 0.9, 0.2])
    bus = MagicMock()
    bus.publish = AsyncMock()
    decider = ToTDecider(llm=fake_llm, bus=bus)
    asyncio.run(decider.decide(board=_board(), screenshot_b64="x", num_branches=3))
    selected = next(c for c in bus.publish.await_args_list if c.args[0] == "tot_selected")
    payload = selected.args[1]
    assert payload["chosen_action"] == "swipe_down"
    assert payload["chosen_value"] == 0.9
    assert set(payload["branch_values"].keys()) == {"swipe_up", "swipe_down", "swipe_left"}


def test_tot_skips_branches_with_parse_errors() -> None:
    fake_llm = MagicMock()
    fake_llm.model = "test-model"
    fake_llm.complete.side_effect = [
        ("not-json", Usage(input_tokens=1, output_tokens=1, model="test-model")),
        (
            '{"action":"swipe_down","reasoning":"r","value":0.6}',
            Usage(input_tokens=1, output_tokens=1, model="test-model"),
        ),
        (
            '{"action":"swipe_left","reasoning":"r","value":0.3}',
            Usage(input_tokens=1, output_tokens=1, model="test-model"),
        ),
    ]
    bus = MagicMock()
    bus.publish = AsyncMock()
    decider = ToTDecider(llm=fake_llm, bus=bus)
    decision = asyncio.run(decider.decide(board=_board(), screenshot_b64="x", num_branches=3))
    assert decision.action == "swipe_down"
    parse_errors = [
        c
        for c in bus.publish.await_args_list
        if c.args[0] == "tot_branch" and c.args[1].get("status") == "parse_error"
    ]
    assert len(parse_errors) == 1
