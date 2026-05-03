from dataclasses import dataclass


@dataclass(frozen=True)
class AffectVector:
    valence: float = 0.0
    arousal: float = 0.2
    dopamine: float = 0.0
    frustration: float = 0.0
    anxiety: float = 0.0
    confidence: float = 0.5
