from nova_agent.decision.prompts import build_user_prompt_v2, build_user_prompt_v3


def test_v3_appends_mood_when_text_present() -> None:
    grid = [[0] * 4 for _ in range(4)]
    text = build_user_prompt_v3(grid=grid, score=0, memories=[], affect_text="You feel anxious.")
    assert text.endswith("Mood: You feel anxious.")


def test_v3_falls_back_to_v2_for_empty_affect() -> None:
    grid = [[0] * 4 for _ in range(4)]
    v2 = build_user_prompt_v2(grid=grid, score=0, memories=[])
    v3 = build_user_prompt_v3(grid=grid, score=0, memories=[], affect_text="")
    assert v2 == v3


def test_v3_keeps_v2_body_intact() -> None:
    grid = [[0] * 4 for _ in range(4)]
    v2 = build_user_prompt_v2(grid=grid, score=42, memories=[])
    v3 = build_user_prompt_v3(grid=grid, score=42, memories=[], affect_text="You feel calm.")
    assert v3.startswith(v2)
    assert "Mood: You feel calm." in v3
