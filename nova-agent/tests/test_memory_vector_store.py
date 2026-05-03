from nova_agent.memory.vector_store import VectorStore


def test_vector_store_insert_and_search(tmp_path):
    vs = VectorStore(tmp_path / "lancedb")
    a = [0.0] * 16
    a[0] = 1.0
    b = [0.0] * 16
    b[5] = 1.0
    c = [0.0] * 16
    c[0] = 0.95
    c[1] = 0.05
    vs.upsert("a", a)
    vs.upsert("b", b)
    vs.upsert("c", c)
    q = [0.0] * 16
    q[0] = 1.0
    hits = vs.search(q, k=2)
    ids = [id_ for id_, _score in hits]
    assert ids[0] in ("a", "c")


def test_vector_store_rejects_wrong_dim(tmp_path):
    vs = VectorStore(tmp_path / "lancedb")
    import pytest

    with pytest.raises(ValueError):
        vs.upsert("bad", [1.0, 0.0, 0.0])
