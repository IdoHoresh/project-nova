from nova_agent.llm.embeddings import embed_board, EMBED_DIM


def _cos(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def test_embed_dim_is_16():
    e = embed_board([[0] * 4] * 4)
    assert len(e) == EMBED_DIM == 16


def test_similarity_high_for_one_tile_diff():
    a = [[2, 0, 0, 0], [0, 4, 0, 0], [0, 0, 8, 0], [0, 0, 0, 16]]
    b = [[2, 0, 0, 0], [0, 4, 0, 0], [0, 0, 8, 0], [0, 0, 0, 32]]
    e_a = embed_board(a)
    e_b = embed_board(b)
    assert _cos(e_a, e_b) > 0.85


def test_similarity_low_for_completely_different_boards():
    a = [[2, 0, 0, 0]] + [[0] * 4] * 3
    b = [[0] * 4] * 3 + [[0, 0, 0, 2048]]
    assert _cos(embed_board(a), embed_board(b)) < 0.5


def test_identical_boards_cosine_one():
    g = [[2, 4, 8, 16]] * 4
    e = embed_board(g)
    assert abs(_cos(e, e) - 1.0) < 1e-9


def test_empty_board_returns_zero_vector():
    e = embed_board([[0] * 4] * 4)
    assert all(x == 0.0 for x in e)
