"""Brutalist renderer tests.

Verifies:
- Output is a 400x400 RGB PNG (parsed via Pillow).
- Palette is keyed by power of 2; values above 2048 use the cap entry.
- LoC bound: render_board source is <= 50 LoC (drift guard).

Per ADR-0008, this renderer's only contract is structural identity with
the emulator pipeline (PNG + base64 + ~similar dimensions + tile-value
legibility for the VLM). Pixel-perfect Unity-fork match is explicitly
rejected; tests do NOT assert exact hex values, only that the palette
mapping function returns DIFFERENT colors for different tile values.
"""

from __future__ import annotations

import inspect
from io import BytesIO

from PIL import Image

from nova_agent.lab.render import render_board, PALETTE
from nova_agent.perception.types import BoardState


def _empty_board() -> BoardState:
    return BoardState(grid=[[0] * 4 for _ in range(4)], score=0)


def test_render_returns_400x400_png_bytes() -> None:
    raw = render_board(_empty_board())
    assert isinstance(raw, bytes)
    img = Image.open(BytesIO(raw))
    assert img.format == "PNG"
    assert img.size == (400, 400)


def test_render_empty_board_uses_empty_palette() -> None:
    # The empty palette entry (0) must exist; this test pins the
    # palette table's shape, not its specific values.
    assert 0 in PALETTE
    raw = render_board(_empty_board())
    img = Image.open(BytesIO(raw)).convert("RGB")
    # Sample the center of cell [0][0] (50, 50) — should be the empty color.
    expected_rgb = Image.new("RGB", (1, 1), color=PALETTE[0]).getpixel((0, 0))
    assert img.getpixel((50, 50)) == expected_rgb


def test_render_max_tile_2048_uses_2048_palette() -> None:
    grid = [[2048, 0, 0, 0], [0] * 4, [0] * 4, [0] * 4]
    raw = render_board(BoardState(grid=grid, score=0))
    img = Image.open(BytesIO(raw)).convert("RGB")
    # Sample the corner of cell [0][0] — pure tile color before the
    # centered text overlays it.
    expected_rgb = Image.new("RGB", (1, 1), color=PALETTE[2048]).getpixel((0, 0))
    assert img.getpixel((5, 5)) == expected_rgb


def test_render_above_2048_uses_4096_palette() -> None:
    # Tiles above 2048 (e.g. 4096, 8192) should fall back to the cap
    # entry. The palette has a 4096 entry that all higher values use.
    grid = [[8192, 0, 0, 0], [0] * 4, [0] * 4, [0] * 4]
    raw = render_board(BoardState(grid=grid, score=0))
    img = Image.open(BytesIO(raw)).convert("RGB")
    expected_rgb = Image.new("RGB", (1, 1), color=PALETTE[4096]).getpixel((0, 0))
    assert img.getpixel((5, 5)) == expected_rgb


def test_render_does_not_raise_on_zero_filled_grid() -> None:
    # Smoke test for the all-empty case (renderer must not crash on
    # the empty palette entry's text rendering).
    render_board(_empty_board())  # no exception


def test_render_total_loc_under_50() -> None:
    """Drift guard: render_board source must stay under 50 lines.

    If this fires, the renderer is being over-engineered. See
    ADR-0008's brutalist-renderer constraint.
    """
    src_lines = inspect.getsource(render_board).splitlines()
    # Count non-blank, non-comment-only lines.
    code_lines = [line for line in src_lines if line.strip() and not line.strip().startswith("#")]
    assert len(code_lines) <= 50, f"render_board has {len(code_lines)} code lines; cap is 50"
