from nova_agent.affect.types import AffectVector
from nova_agent.affect.verbalize import describe


def test_describe_anxious_state() -> None:
    v = AffectVector(
        valence=-0.3,
        arousal=0.8,
        dopamine=0.1,
        frustration=0.4,
        anxiety=0.7,
        confidence=0.4,
    )
    s = describe(v)
    assert "anxious" in s.lower() or "nervous" in s.lower()


def test_describe_happy_state() -> None:
    v = AffectVector(
        valence=0.7,
        arousal=0.5,
        dopamine=0.6,
        frustration=0.0,
        anxiety=0.0,
        confidence=0.9,
    )
    s = describe(v)
    lc = s.lower()
    assert "good" in lc or "satisfied" in lc or "confident" in lc


def test_describe_frustrated_state() -> None:
    v = AffectVector(
        valence=-0.2,
        arousal=0.5,
        dopamine=0.0,
        frustration=0.7,
        anxiety=0.2,
        confidence=0.5,
    )
    s = describe(v)
    assert "frustrated" in s.lower() or "impatient" in s.lower()


def test_describe_low_confidence_appended() -> None:
    v = AffectVector(
        valence=0.0,
        arousal=0.3,
        dopamine=0.0,
        frustration=0.0,
        anxiety=0.0,
        confidence=0.1,
    )
    assert "trust" in describe(v).lower()


def test_describe_returns_non_empty_for_neutral() -> None:
    s = describe(AffectVector())
    assert s.strip() != ""
