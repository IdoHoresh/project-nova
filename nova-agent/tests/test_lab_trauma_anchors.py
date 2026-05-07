import hashlib

from nova_agent.lab.trauma_ablation import (
    ANCHOR_HASH,
    ANCHOR_ORBIT,
    _BASE_ANCHORS,
    _build_orbit,
    _flip_h,
    _rotate_cw,
)


def test_base_anchors_match_appendix_a() -> None:
    assert _BASE_ANCHORS["corner-abandonment-256"] == [
        [0, 4, 0, 0],
        [4, 8, 4, 2],
        [0, 16, 8, 128],
        [64, 256, 128, 32],
    ]
    assert _BASE_ANCHORS["snake-collapse-128"] == [
        [0, 4, 0, 0],
        [0, 32, 4, 4],
        [8, 4, 32, 4],
        [2, 8, 64, 128],
    ]
    assert _BASE_ANCHORS["512-wall"] == [
        [0, 4, 0, 0],
        [4, 8, 16, 32],
        [8, 16, 32, 64],
        [256, 128, 512, 0],
    ]


def test_rotate_cw_4_times_is_identity() -> None:
    grid = _BASE_ANCHORS["corner-abandonment-256"]
    rotated = grid
    for _ in range(4):
        rotated = _rotate_cw(rotated)
    assert rotated == grid


def test_flip_h_twice_is_identity() -> None:
    grid = _BASE_ANCHORS["snake-collapse-128"]
    assert _flip_h(_flip_h(grid)) == grid


def test_orbit_size_le_8_per_anchor() -> None:
    for grid in _BASE_ANCHORS.values():
        orbit = _build_orbit(grid)
        assert 1 <= len(orbit) <= 8
        for elem in orbit:
            assert isinstance(elem, tuple)
            assert all(isinstance(row, tuple) for row in elem)


def test_full_dictionary_size_le_24() -> None:
    assert 1 <= len(ANCHOR_ORBIT) <= 24


def test_full_dictionary_unique() -> None:
    assert len(set(ANCHOR_ORBIT)) == len(ANCHOR_ORBIT)


def test_anchor_hash_is_sha256_of_sorted_orbit() -> None:
    expected = hashlib.sha256(repr(sorted(ANCHOR_ORBIT)).encode("utf-8")).hexdigest()
    assert ANCHOR_HASH == expected


def test_anchor_hash_stable_across_imports() -> None:
    from nova_agent.lab.trauma_ablation import ANCHOR_HASH as second

    assert ANCHOR_HASH == second
