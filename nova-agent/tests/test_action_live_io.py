"""LiveGameIO adapter tests.

Behavioural-equivalent refactor of today's inline Capture+BoardOCR+ADB
wiring in main.run(). These tests pin the public contract; the
adapter's internals are mocked via dependency injection (Capture / OCR
/ ADB are passed in, not constructed inside the adapter).
"""

from __future__ import annotations

from unittest.mock import MagicMock

from PIL import Image

from nova_agent.action.adb import SwipeDirection
from nova_agent.action.live_io import LiveGameIO
from nova_agent.perception.ocr import CalibrationError
from nova_agent.perception.types import BoardState


def _fake_image() -> Image.Image:
    return Image.new("RGB", (1080, 2400), color=(0, 0, 0))


def test_read_board_invokes_capture_then_ocr() -> None:
    capture = MagicMock()
    capture.grab_stable.return_value = _fake_image()
    ocr = MagicMock()
    ocr.read.return_value = BoardState(grid=[[0] * 4 for _ in range(4)], score=42)
    adb = MagicMock()

    io = LiveGameIO(capture=capture, ocr=ocr, adb=adb)
    board = io.read_board()

    capture.grab_stable.assert_called_once()
    ocr.read.assert_called_once()
    assert board.score == 42


def test_read_board_returns_empty_on_calibration_error() -> None:
    capture = MagicMock()
    capture.grab_stable.return_value = _fake_image()
    ocr = MagicMock()
    ocr.read.side_effect = CalibrationError("test")
    adb = MagicMock()

    io = LiveGameIO(capture=capture, ocr=ocr, adb=adb)
    board = io.read_board()

    assert board.grid == [[0] * 4 for _ in range(4)]
    assert board.score == 0


def test_apply_move_invokes_adb_swipe() -> None:
    capture = MagicMock()
    capture.grab_stable.return_value = _fake_image()
    ocr = MagicMock()
    ocr.read.return_value = BoardState(grid=[[0] * 4 for _ in range(4)], score=0)
    adb = MagicMock()

    io = LiveGameIO(capture=capture, ocr=ocr, adb=adb)
    io.apply_move(SwipeDirection.LEFT)

    adb.swipe.assert_called_once_with(SwipeDirection.LEFT)


def test_apply_move_invalidates_cached_image() -> None:
    capture = MagicMock()
    capture.grab_stable.side_effect = [_fake_image(), _fake_image()]
    ocr = MagicMock()
    ocr.read.return_value = BoardState(grid=[[0] * 4 for _ in range(4)], score=0)
    adb = MagicMock()

    io = LiveGameIO(capture=capture, ocr=ocr, adb=adb)
    io.read_board()
    io.apply_move(SwipeDirection.UP)
    io.screenshot_b64()

    # 2 calls because apply_move invalidated the cache,
    # forcing screenshot_b64 to re-grab.
    assert capture.grab_stable.call_count == 2


def test_screenshot_b64_reuses_cached_image_when_available() -> None:
    capture = MagicMock()
    capture.grab_stable.return_value = _fake_image()
    ocr = MagicMock()
    ocr.read.return_value = BoardState(grid=[[0] * 4 for _ in range(4)], score=0)
    adb = MagicMock()

    io = LiveGameIO(capture=capture, ocr=ocr, adb=adb)
    io.read_board()
    b64 = io.screenshot_b64()

    # Only 1 call because read_board cached the image
    # and screenshot_b64 reused it.
    assert capture.grab_stable.call_count == 1
    assert isinstance(b64, str)
    assert len(b64) > 0
