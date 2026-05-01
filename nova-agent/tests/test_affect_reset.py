from nova_agent.affect.state import AffectState
from nova_agent.affect.types import AffectVector


def test_reset_zeroes_fast_variables() -> None:
    s = AffectState()
    s.vector = AffectVector(
        valence=0.8,
        arousal=0.9,
        dopamine=0.7,
        frustration=0.6,
        anxiety=0.95,
        confidence=0.2,
    )
    out = s.reset_for_new_game()
    assert out.anxiety == 0.0
    assert out.frustration == 0.0
    assert out.dopamine == 0.0


def test_reset_partially_carries_valence() -> None:
    s = AffectState()
    s.vector = AffectVector(valence=0.8)
    out = s.reset_for_new_game()
    assert abs(out.valence - 0.24) < 1e-9


def test_reset_restores_baseline_arousal_and_confidence() -> None:
    s = AffectState()
    s.vector = AffectVector(arousal=0.95, confidence=0.05)
    out = s.reset_for_new_game()
    baseline = AffectVector()
    assert out.arousal == baseline.arousal
    assert out.confidence == baseline.confidence
