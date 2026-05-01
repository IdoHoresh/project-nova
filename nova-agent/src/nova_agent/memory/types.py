from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal

from nova_agent.perception.types import BoardState

Action = Literal["swipe_up", "swipe_down", "swipe_left", "swipe_right", "none"]


@dataclass(frozen=True)
class AffectSnapshot:
    valence: float
    arousal: float
    dopamine: float
    frustration: float
    anxiety: float
    confidence: float


@dataclass
class MemoryRecord:
    id: str
    timestamp: datetime
    board_before: BoardState
    board_after: BoardState
    action: Action
    score_delta: int
    rpe: float
    importance: int  # 1..10
    tags: list[str] = field(default_factory=list)
    embedding: list[float] = field(default_factory=list)
    last_accessed: datetime | None = None
    source_reasoning: str | None = None
    affect: AffectSnapshot | None = None
    aversive_weight: float = 0.0
