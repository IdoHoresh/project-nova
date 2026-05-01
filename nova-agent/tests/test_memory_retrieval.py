import math
from datetime import datetime, timedelta, timezone
from nova_agent.memory.retrieval import recency_score, cosine, combined_score


def test_recency_decays_power_law():
    now = datetime.now(timezone.utc)
    fresh = recency_score(last_accessed=now, now=now)
    week_old = recency_score(last_accessed=now - timedelta(days=7), now=now)
    month_old = recency_score(last_accessed=now - timedelta(days=30), now=now)
    assert fresh > week_old > month_old > 0


def test_cosine_identical_is_one():
    assert math.isclose(cosine([1, 0, 0], [1, 0, 0]), 1.0, abs_tol=1e-6)
    assert math.isclose(cosine([1, 0, 0], [-1, 0, 0]), -1.0, abs_tol=1e-6)


def test_combined_score_weights():
    s = combined_score(recency=0.5, importance_norm=0.5, relevance=0.5,
                       w_recency=1.0, w_importance=1.0, w_relevance=1.0)
    assert math.isclose(s, 1.5, abs_tol=1e-6)
