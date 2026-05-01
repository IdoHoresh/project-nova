import math
from dataclasses import dataclass
from datetime import datetime, timezone

from nova_agent.memory.types import MemoryRecord


def recency_score(
    *, last_accessed: datetime | None, now: datetime, half_life_days: float = 7.0
) -> float:
    """Power-law decay: 1 / (1 + t/half_life)^1.5 where t is in days.

    Wixted & Carpenter (2007) — closer to human forgetting than exponential.
    """
    if last_accessed is None:
        return 0.0
    delta_days = max(0.0, (now - last_accessed).total_seconds() / 86400.0)
    return float(1.0 / (1.0 + delta_days / half_life_days) ** 1.5)


def cosine(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def combined_score(
    *,
    recency: float,
    importance_norm: float,
    relevance: float,
    w_recency: float = 1.0,
    w_importance: float = 1.0,
    w_relevance: float = 1.0,
) -> float:
    return w_recency * recency + w_importance * importance_norm + w_relevance * relevance


@dataclass(frozen=True)
class RetrievedMemory:
    record: MemoryRecord
    score: float


def retrieve_top_k(
    *,
    candidates: list[MemoryRecord],
    query_embedding: list[float],
    now: datetime | None = None,
    k: int = 5,
    w_recency: float = 1.0,
    w_importance: float = 1.0,
    w_relevance: float = 1.0,
) -> list[RetrievedMemory]:
    now = now or datetime.now(timezone.utc)
    scored: list[RetrievedMemory] = []
    for rec in candidates:
        rec_recency = recency_score(last_accessed=rec.last_accessed or rec.timestamp, now=now)
        rec_relevance = cosine(query_embedding, rec.embedding)
        importance_norm = (rec.importance - 1) / 9  # 1..10 -> 0..1
        s = combined_score(
            recency=rec_recency,
            importance_norm=importance_norm,
            relevance=rec_relevance,
            w_recency=w_recency,
            w_importance=w_importance,
            w_relevance=w_relevance,
        )
        scored.append(RetrievedMemory(record=rec, score=s))
    scored.sort(key=lambda x: x.score, reverse=True)
    return scored[:k]
