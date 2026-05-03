from nova_agent.memory.importance import score_programmatic


def test_score_programmatic_high_for_game_over():
    s = score_programmatic(rpe=-2.0, terminal=True, max_tile=1024, empty_cells=0, milestone=False)
    assert s >= 8


def test_score_programmatic_low_for_routine():
    s = score_programmatic(rpe=0.0, terminal=False, max_tile=4, empty_cells=14, milestone=False)
    assert s <= 2


def test_score_programmatic_milestone_bumps():
    base = score_programmatic(
        rpe=0.5, terminal=False, max_tile=1024, empty_cells=8, milestone=False
    )
    bumped = score_programmatic(
        rpe=0.5, terminal=False, max_tile=1024, empty_cells=8, milestone=True
    )
    assert bumped > base
