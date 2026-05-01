from unittest.mock import MagicMock

from nova_agent.llm.protocol import Usage
from nova_agent.reflection.postmortem import run_reflection


def _llm(response_text: str) -> MagicMock:
    fake = MagicMock()
    fake.model = "test-model"
    fake.complete.return_value = (
        response_text,
        Usage(input_tokens=200, output_tokens=80, model="test-model"),
    )
    return fake


def test_reflection_returns_lessons() -> None:
    fake = _llm(
        '{"summary":"died on tight board",'
        '"lessons":["protect the corner","merge mid-tier early"],'
        '"notable_episodes":["ep_1"]}'
    )
    out = run_reflection(llm=fake, last_30_moves_summary="...", prior_lessons=[])
    assert "lessons" in out
    assert len(out["lessons"]) == 2
    assert out["summary"] == "died on tight board"


def test_reflection_passes_prior_lessons_into_prompt() -> None:
    fake = _llm('{"summary":"s","lessons":["l1","l2","l3"],"notable_episodes":["ep_x"]}')
    run_reflection(
        llm=fake,
        last_30_moves_summary="moves",
        prior_lessons=["older1", "older2", "older3", "older4"],
    )
    user_text = fake.complete.call_args.kwargs["messages"][0]["content"]
    # Only top-3 (most-recent slice) prior lessons should be included.
    assert "older2" in user_text
    assert "older3" in user_text
    assert "older4" in user_text
    assert "older1" not in user_text


def test_reflection_returns_dict_with_required_keys() -> None:
    fake = _llm('{"summary":"s","lessons":["a","b","c"],"notable_episodes":["ep_1","ep_2"]}')
    out = run_reflection(llm=fake, last_30_moves_summary="m", prior_lessons=[])
    assert set(out.keys()) >= {"summary", "lessons", "notable_episodes"}
