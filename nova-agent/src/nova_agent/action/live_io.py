"""LiveGameIO — wraps Capture + BoardOCR + ADB behind the GameIO protocol.

Behavioural-equivalent extraction of today's inline I/O wiring in
main.run(). The cognitive loop calls read_board() / apply_move() /
screenshot_b64() instead of poking Capture / OCR / ADB directly.

Cache invariant: read_board() caches the latest captured PIL Image so
screenshot_b64() doesn't trigger a redundant ADB capture per loop step.
apply_move() invalidates the cache so the next read_board() forces a
fresh capture — this prevents the loop from feeding the post-move VLM
prompt a pre-move screenshot.
"""

from __future__ import annotations

import base64

from PIL import Image

from nova_agent.action.adb import ADB, SwipeDirection
from nova_agent.perception.capture import Capture
from nova_agent.perception.ocr import BoardOCR, CalibrationError
from nova_agent.perception.types import BoardState


class LiveGameIO:
    def __init__(self, *, capture: Capture, ocr: BoardOCR, adb: ADB) -> None:
        self._capture = capture
        self._ocr = ocr
        self._adb = adb
        self._last_image: Image.Image | None = None

    def read_board(self) -> BoardState:
        self._last_image = self._capture.grab_stable()
        try:
            return self._ocr.read(self._last_image)
        except CalibrationError:
            return BoardState(grid=[[0] * 4 for _ in range(4)], score=0)

    def apply_move(self, direction: SwipeDirection) -> None:
        self._adb.swipe(direction)
        self._last_image = None  # next read_board needs a fresh capture

    def screenshot_b64(self) -> str:
        if self._last_image is None:
            self._last_image = self._capture.grab_stable()
        return base64.b64encode(Capture.to_vlm_bytes(self._last_image)).decode("ascii")
