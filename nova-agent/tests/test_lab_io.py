"""SimGameIO adapter tests."""

from __future__ import annotations

import base64
from io import BytesIO
from math import log2

from PIL import Image

from nova_agent.action.adb import SwipeDirection
from nova_agent.lab.io import SimGameIO
from nova_agent.lab.sim import Game2048Sim, Scenario


def _sim(grid: list[list[int]] | None = None) -> Game2048Sim:
    if grid is None:
        return Game2048Sim(seed=42)
    # Compute minimum-implied-score so the validator passes.
    derived_score = sum(int((log2(v) - 1) * v) for r in grid for v in r if v > 0)
    max_tile = max((v for r in grid for v in r), default=0)
    return Game2048Sim(
        seed=42,
        scenario=Scenario(
            id="t",
            initial_grid=grid,
            initial_score=derived_score,
            seed_base=42,
            pattern_name="test",
            high_tile_magnitude=max_tile,
            expected_cliff_window=(11, 14),
            source_citation="test",
        ),
    )


def test_read_board_returns_sim_board() -> None:
    sim = _sim([[2, 0, 0, 0], [0] * 4, [0] * 4, [0] * 4])
    io = SimGameIO(sim=sim)
    board = io.read_board()
    assert board.grid == sim.board.grid
    assert board.score == sim.board.score


def test_apply_move_advances_sim_state() -> None:
    sim = _sim([[2, 2, 0, 0], [0] * 4, [0] * 4, [0] * 4])
    io = SimGameIO(sim=sim)
    io.apply_move(SwipeDirection.LEFT)
    # The 2+2 merge to 4 should land at [0][0]; score +4.
    assert sim.board.grid[0][0] == 4
    assert sim.board.score == 4


def test_screenshot_b64_returns_valid_base64_png() -> None:
    sim = _sim()
    io = SimGameIO(sim=sim)
    b64 = io.screenshot_b64()
    assert isinstance(b64, str)
    raw = base64.b64decode(b64)
    img = Image.open(BytesIO(raw))
    assert img.format == "PNG"
    assert img.size == (400, 400)
