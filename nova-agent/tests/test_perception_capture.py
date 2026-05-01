import pytest
from nova_agent.perception.types import BoardState


def test_board_state_properties():
    b = BoardState(grid=[[0, 2, 0, 0], [0, 0, 0, 2], [0, 0, 0, 0], [0, 0, 0, 0]], score=0)
    assert b.empty_cells == 14
    assert b.max_tile == 2


def test_board_state_validates_4x4():
    with pytest.raises(ValueError):
        BoardState(grid=[[0, 2], [0, 0]], score=0)


def test_to_vlm_bytes_downscales_to_512_max_side():
    """R1 — token hemorrhage protection. A raw 1080×2400 PNG to the VLM on
    every move would obliterate the budget. The capture layer always
    downscales before encoding."""
    from io import BytesIO
    from PIL import Image as PILImage
    from nova_agent.perception.capture import Capture

    big = PILImage.new("RGB", (1080, 2400), color="white")
    payload = Capture.to_vlm_bytes(big)
    decoded = PILImage.open(BytesIO(payload))
    assert max(decoded.size) <= 512
    # PNG should be tiny (high-contrast solid white compresses well, but the
    # critical assertion is that no path can slip a full-res image through)
    assert len(payload) < 50_000
