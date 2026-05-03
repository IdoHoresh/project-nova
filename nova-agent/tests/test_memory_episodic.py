from datetime import datetime, timezone
from nova_agent.memory.episodic import EpisodicStore
from nova_agent.memory.types import MemoryRecord
from nova_agent.perception.types import BoardState


def make_record(score: int = 0, action: str = "swipe_right") -> MemoryRecord:
    b = BoardState(grid=[[0, 0, 0, 0]] * 4, score=score)
    return MemoryRecord(
        id=f"ep_{score}",
        timestamp=datetime.now(timezone.utc),
        board_before=b,
        board_after=b,
        action=action,
        score_delta=0,
        rpe=0.0,
        importance=1,
        tags=[],
        embedding=[0.0] * 8,
    )


def test_episodic_store_round_trip(tmp_path):
    store = EpisodicStore(tmp_path / "test.db")
    rec = make_record()
    store.insert(rec)
    fetched = store.get(rec.id)
    assert fetched is not None
    assert fetched.action == "swipe_right"


def test_episodic_store_list_recent(tmp_path):
    store = EpisodicStore(tmp_path / "test.db")
    for i in range(20):
        store.insert(make_record(score=i, action="swipe_up"))
    recent = store.list_recent(limit=5)
    assert len(recent) == 5
    assert recent[0].id == "ep_19"
