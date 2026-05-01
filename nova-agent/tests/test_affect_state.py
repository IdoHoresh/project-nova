from nova_agent.affect.state import AffectState
from nova_agent.affect.types import AffectVector


def test_initial_state_neutral() -> None:
    a = AffectState()
    assert -0.1 <= a.vector.valence <= 0.1
    assert 0.0 <= a.vector.arousal <= 0.3
    assert a.vector.dopamine == 0.0


def test_positive_rpe_spikes_dopamine_and_lifts_valence() -> None:
    a = AffectState()
    before = a.vector
    a.update(rpe=0.5, empty_cells=10, terminal=False, trauma_triggered=False)
    after = a.vector
    assert after.dopamine > before.dopamine
    assert after.valence > before.valence


def test_negative_rpe_increases_frustration() -> None:
    a = AffectState()
    a.update(rpe=-0.5, empty_cells=10, terminal=False, trauma_triggered=False)
    assert a.vector.frustration > 0


def test_anxiety_rises_when_few_empty_cells() -> None:
    a = AffectState()
    a.update(rpe=0.0, empty_cells=1, terminal=False, trauma_triggered=False)
    assert a.vector.anxiety > 0.4


def test_terminal_pins_anxiety_to_one() -> None:
    a = AffectState()
    out = a.update(rpe=0.0, empty_cells=8, terminal=True, trauma_triggered=False)
    assert out.anxiety == 1.0


def test_trauma_adds_anxiety() -> None:
    a = AffectState()
    a.update(rpe=0.0, empty_cells=10, terminal=False, trauma_triggered=True)
    assert a.vector.anxiety >= 0.3


def test_values_are_clamped_to_ranges() -> None:
    a = AffectState()
    for _ in range(20):
        a.update(rpe=1.0, empty_cells=0, terminal=False, trauma_triggered=True)
    v = a.vector
    assert -1.0 <= v.valence <= 1.0
    assert 0.0 <= v.arousal <= 1.0
    assert 0.0 <= v.dopamine <= 1.0
    assert 0.0 <= v.frustration <= 1.0
    assert 0.0 <= v.anxiety <= 1.0
    assert 0.0 <= v.confidence <= 1.0


def test_affect_vector_is_immutable() -> None:
    v = AffectVector()
    try:
        v.valence = 0.9  # type: ignore[misc]
    except Exception:
        return
    raise AssertionError("AffectVector should be frozen")
