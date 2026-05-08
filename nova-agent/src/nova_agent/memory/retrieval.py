import math
from dataclasses import dataclass
from datetime import datetime, timezone

from nova_agent.memory.aversive import AVERSIVE_TAG, is_inert
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
    relevance: float  # raw cosine; pre-boost; for graded-affect formula (ADR-0012)


# AVERSIVE_RELEVANCE_FLOOR: raised from 0.4 to 0.66 per ADR-0012.
# Empirically derived: instrumented Phase 0.8 §3.2b golden Y_on run on
# 2026-05-08 surfaced 52 aversive-tagged candidates (across 12 distinct
# moves of 150) with raw cosine in the [0.1714, 0.6525] band on the
# trivial easy-win-1024 golden board where the gate's specificity null
# demands zero aversive surfacing. New floor = 0.66 is the smallest
# value strictly excluding the observed max leak (0.6525); preserves
# headroom for legitimate cliff-board surfacing (Phase 0.7 cliff-test
# trap-similar embeddings produce cosines well above 0.7 for true
# matches; retrieval is a coarse pre-filter, not the trap-detection
# layer).
# Run artifact: nova-agent/runs/2026-05-08-phase08-run-rerun/golden/
# retrievals_y_on_-8570493758050568564.jsonl (gitignored; reproducible
# via `python -m nova_agent.lab.trauma_ablation --stage=golden
# --log-retrievals --tier=production`).
AVERSIVE_RELEVANCE_FLOOR = 0.66
AVERSIVE_WIDENED_RELEVANCE = 0.7


def _enforce_aversive_cap(scored: list[RetrievedMemory]) -> list[RetrievedMemory]:
    """Defense A from §3.6 — at most one aversive record per move.

    Keeps relative score order otherwise. The single aversive kept is the
    highest-scoring one; the rest are dropped from the candidate set before
    truncation to top-k.
    """
    aversive = [m for m in scored if AVERSIVE_TAG in m.record.tags]
    if len(aversive) <= 1:
        return scored
    best_aversive = max(aversive, key=lambda m: m.score)
    return [m for m in scored if AVERSIVE_TAG not in m.record.tags or m is best_aversive]


def retrieve_top_k(
    *,
    candidates: list[MemoryRecord],
    query_embedding: list[float],
    now: datetime | None = None,
    k: int = 5,
    w_recency: float = 1.0,
    w_importance: float = 1.0,
    w_relevance: float = 1.0,
    aversive_relevance_floor: float = AVERSIVE_RELEVANCE_FLOOR,
    retrieval_log: list[dict[str, object]] | None = None,
) -> list[RetrievedMemory]:
    now = now or datetime.now(timezone.utc)
    scored: list[RetrievedMemory] = []
    for rec in candidates:
        if is_inert(rec):
            continue
        rec_recency = recency_score(last_accessed=rec.last_accessed or rec.timestamp, now=now)
        raw_relevance = cosine(query_embedding, rec.embedding)
        rec_relevance = raw_relevance
        if AVERSIVE_TAG in rec.tags and rec_relevance > aversive_relevance_floor:
            rec_relevance = max(rec_relevance, AVERSIVE_WIDENED_RELEVANCE)
            rec_relevance *= rec.aversive_weight
        importance_norm = (rec.importance - 1) / 9
        s = combined_score(
            recency=rec_recency,
            importance_norm=importance_norm,
            relevance=rec_relevance,
            w_recency=w_recency,
            w_importance=w_importance,
            w_relevance=w_relevance,
        )
        scored.append(RetrievedMemory(record=rec, score=s, relevance=raw_relevance))
        if retrieval_log is not None:
            retrieval_log.append(
                {
                    "record_id": rec.id,
                    "aversive_tag_present": AVERSIVE_TAG in rec.tags,
                    "raw_cosine": raw_relevance,
                    "score": s,
                }
            )
    scored.sort(key=lambda x: x.score, reverse=True)
    capped = _enforce_aversive_cap(scored)
    return capped[:k]
