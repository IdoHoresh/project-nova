"""ADB action wrapper.

The Unity 6 fork of 2048 ignores ``adb shell input swipe`` events — its
input layer only handles keyboard / DPAD keycodes. The wrapper therefore
sends ``input keyevent KEYCODE_DPAD_*`` for each move. The public API stays
``swipe(direction)`` because the agent thinks in board moves, not in the
underlying IPC.
"""

import subprocess
import time
from enum import Enum

import structlog

log = structlog.get_logger()


class SwipeDirection(str, Enum):
    UP = "swipe_up"
    DOWN = "swipe_down"
    LEFT = "swipe_left"
    RIGHT = "swipe_right"


# Android KeyEvent constants (KEYCODE_DPAD_*).
_KEYCODE: dict[SwipeDirection, int] = {
    SwipeDirection.UP: 19,
    SwipeDirection.DOWN: 20,
    SwipeDirection.LEFT: 21,
    SwipeDirection.RIGHT: 22,
}


class ADB:
    """Thin wrapper around `adb shell input keyevent` for board moves."""

    def __init__(self, *, adb_path: str, device_id: str | None, screen_w: int, screen_h: int):
        self.adb_path = adb_path
        self.device_id = device_id
        self.w = screen_w
        self.h = screen_h

    def _base_args(self) -> list[str]:
        args = [self.adb_path]
        if self.device_id:
            args += ["-s", self.device_id]
        return args

    def swipe(self, direction: SwipeDirection) -> None:
        keycode = _KEYCODE[direction]
        args = self._base_args() + ["shell", "input", "keyevent", str(keycode)]
        log.info("adb.swipe", direction=direction.value, keycode=keycode, args=args)
        result = subprocess.run(args, capture_output=True, timeout=5.0)
        if result.returncode != 0:
            raise RuntimeError(
                f"adb keyevent failed: rc={result.returncode}; "
                f"stderr={result.stderr.decode(errors='ignore')!r}"
            )
        time.sleep(0.3)  # wait for tile-slide animation
