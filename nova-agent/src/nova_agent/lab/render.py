"""Brutalist 2048 board renderer.

400x400 RGB PNG, solid power-of-2 palette, PIL default font, no chrome.
Sole contract: structural identity with the emulator pipeline (PNG +
base64 + ~similar dimensions + tile-value legibility for the VLM).
Pixel-faithful Unity match is explicitly rejected per ADR-0008.

Implementation budget: ~30 LoC for render_board. >50 LoC is a stop-and-
review signal; the test_render_total_loc_under_50 test enforces this.
"""

from __future__ import annotations

from io import BytesIO

from PIL import Image, ImageDraw, ImageFont

from nova_agent.perception.types import BoardState

PALETTE: dict[int, str] = {
    0: "#cdc1b4",
    2: "#eee4da",
    4: "#ede0c8",
    8: "#f2b179",
    16: "#f59563",
    32: "#f67c5f",
    64: "#f65e3b",
    128: "#edcf72",
    256: "#edcc61",
    512: "#edc850",
    1024: "#edc53f",
    2048: "#edc22e",
    4096: "#3c3a32",  # cap; values >2048 use this entry
}

_BG = "#bbada0"
_CELL_PX = 100
_TEXT_DARK = "#776e65"  # for tiles <= 4
_TEXT_LIGHT = "#f9f6f2"  # for tiles >= 8


def render_board(board: BoardState) -> bytes:
    """Render a 4x4 BoardState to a 400x400 PNG; return raw bytes."""
    img = Image.new("RGB", (400, 400), color=_BG)
    draw = ImageDraw.Draw(img)
    font = ImageFont.load_default()
    for r in range(4):
        for c in range(4):
            value = board.grid[r][c]
            color = PALETTE.get(value, PALETTE[4096])
            x0, y0 = c * _CELL_PX, r * _CELL_PX
            draw.rectangle((x0, y0, x0 + _CELL_PX, y0 + _CELL_PX), fill=color)
            if value > 0:
                text = str(value)
                text_color = _TEXT_DARK if value <= 4 else _TEXT_LIGHT
                bbox = draw.textbbox((0, 0), text, font=font)
                tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
                tx = x0 + (_CELL_PX - tw) // 2
                ty = y0 + (_CELL_PX - th) // 2
                draw.text((tx, ty), text, fill=text_color, font=font)
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()
