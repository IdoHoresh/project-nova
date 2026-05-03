from nova_agent.affect.types import AffectVector


def _clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


class AffectState:
    """Tracks Nova's affective state across a session.

    Update rules per spec §3.5. Most variables decay slightly each tick; the
    decay term is tuned so that after ~10 'normal' moves the state returns
    near the baseline.
    """

    def __init__(self) -> None:
        self.vector = AffectVector()

    def update(
        self,
        *,
        rpe: float,
        empty_cells: int,
        terminal: bool,
        trauma_triggered: bool,
    ) -> AffectVector:
        v = self.vector
        valence = v.valence * 0.95
        arousal = v.arousal * 0.92
        dopamine = v.dopamine * 0.6
        frustration = v.frustration * 0.92
        anxiety = v.anxiety * 0.85
        confidence = v.confidence * 0.98 + 0.5 * 0.02

        valence += 0.7 * _clamp(rpe, -1.0, 1.0)
        if rpe > 0:
            dopamine += min(1.0, rpe)
        else:
            frustration += min(1.0, -rpe * 0.6)

        pressure = 1.0 - empty_cells / 16
        arousal += 0.4 * pressure + 0.2 * abs(rpe)

        anxiety += 0.7 * max(0.0, (3 - empty_cells) / 3)
        if trauma_triggered:
            anxiety += 0.3
        if terminal:
            anxiety = 1.0

        if rpe != 0:
            confidence += 0.4 * (rpe / max(1e-3, abs(rpe))) * (abs(rpe) ** 0.5)

        self.vector = AffectVector(
            valence=_clamp(valence, -1.0, 1.0),
            arousal=_clamp(arousal, 0.0, 1.0),
            dopamine=_clamp(dopamine, 0.0, 1.0),
            frustration=_clamp(frustration, 0.0, 1.0),
            anxiety=_clamp(anxiety, 0.0, 1.0),
            confidence=_clamp(confidence, 0.0, 1.0),
        )
        return self.vector

    def reset_for_new_game(self) -> AffectVector:
        """§3.6 defense D — cross-game affect reset on game_start.

        Fast variables (anxiety, frustration, dopamine) are zeroed; valence
        is a slow variable so it carries over partially (×0.3) by design.
        Arousal and confidence reset to baseline. Logged as a hygiene step,
        not a load-bearing spiral defense.
        """
        v = self.vector
        baseline = AffectVector()
        self.vector = AffectVector(
            valence=v.valence * 0.3,
            arousal=baseline.arousal,
            dopamine=0.0,
            frustration=0.0,
            anxiety=0.0,
            confidence=baseline.confidence,
        )
        return self.vector
