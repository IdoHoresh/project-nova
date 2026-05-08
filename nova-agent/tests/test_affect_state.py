import math

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
    a.update(rpe=0.5, empty_cells=10, terminal=False, trauma_intensity=0.0)
    after = a.vector
    assert after.dopamine > before.dopamine
    assert after.valence > before.valence


def test_negative_rpe_increases_frustration() -> None:
    a = AffectState()
    a.update(rpe=-0.5, empty_cells=10, terminal=False, trauma_intensity=0.0)
    assert a.vector.frustration > 0


def test_anxiety_rises_when_few_empty_cells() -> None:
    a = AffectState()
    a.update(rpe=0.0, empty_cells=1, terminal=False, trauma_intensity=0.0)
    assert a.vector.anxiety > 0.4


def test_terminal_pins_anxiety_to_one() -> None:
    a = AffectState()
    out = a.update(rpe=0.0, empty_cells=8, terminal=True, trauma_intensity=0.0)
    assert out.anxiety == 1.0


def test_trauma_adds_anxiety() -> None:
    a = AffectState()
    a.update(rpe=0.0, empty_cells=10, terminal=False, trauma_intensity=1.0)
    assert a.vector.anxiety >= 0.3


def test_values_are_clamped_to_ranges() -> None:
    a = AffectState()
    for _ in range(20):
        a.update(rpe=1.0, empty_cells=0, terminal=False, trauma_intensity=1.0)
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


def test_trauma_intensity_scales_anxiety_amplitude_linearly() -> None:
    """anxiety bump is 0.3 × trauma_intensity, not a constant 0.3 (ADR-0012)."""
    a = AffectState()
    a.update(rpe=0.0, empty_cells=10, terminal=False, trauma_intensity=0.5)
    half = a.vector.anxiety

    a2 = AffectState()
    a2.update(rpe=0.0, empty_cells=10, terminal=False, trauma_intensity=1.0)
    full = a2.vector.anxiety

    assert full > half > 0.0
    # full bump = 0.3 × 1.0 = 0.3; half bump = 0.3 × 0.5 = 0.15
    assert math.isclose(full - half, 0.15, abs_tol=1e-6)


def test_trauma_intensity_zero_adds_no_anxiety() -> None:
    """trauma_intensity=0.0 reproduces the old trauma_triggered=False path."""
    a = AffectState()
    a.update(rpe=0.0, empty_cells=10, terminal=False, trauma_intensity=0.0)
    expected_baseline = 0.7 * max(0.0, (3 - 10) / 3)  # = 0.0
    assert math.isclose(a.vector.anxiety, max(0.0, expected_baseline), abs_tol=1e-6)
