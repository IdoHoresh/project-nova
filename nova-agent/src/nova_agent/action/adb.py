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


class ADB:
    """Thin wrapper around `adb shell input` for swipes."""

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

    def swipe(self, direction: SwipeDirection, duration_ms: int = 100) -> None:
        cx, cy = self.w // 2, self.h // 2
        margin_x, margin_y = self.w // 4, self.h // 4
        match direction:
            case SwipeDirection.UP:
                x1, y1, x2, y2 = cx, cy + margin_y, cx, cy - margin_y
            case SwipeDirection.DOWN:
                x1, y1, x2, y2 = cx, cy - margin_y, cx, cy + margin_y
            case SwipeDirection.LEFT:
                x1, y1, x2, y2 = cx + margin_x, cy, cx - margin_x, cy
            case SwipeDirection.RIGHT:
                x1, y1, x2, y2 = cx - margin_x, cy, cx + margin_x, cy
            case _:
                raise ValueError(f"Unknown direction {direction}")
        args = self._base_args() + [
            "shell", "input", "swipe",
            str(x1), str(y1), str(x2), str(y2), str(duration_ms),
        ]
        log.info("adb.swipe", direction=direction.value, args=args)
        result = subprocess.run(args, capture_output=True, timeout=5.0)
        if result.returncode != 0:
            raise RuntimeError(
                f"adb swipe failed: rc={result.returncode}; "
                f"stderr={result.stderr.decode(errors='ignore')!r}"
            )
        time.sleep(0.3)  # wait for tile-slide animation
