"""GameIO protocol — the seam between cognitive layer and game I/O.

Two implementations live elsewhere:
- nova_agent.action.live_io.LiveGameIO (wraps Capture + BoardOCR + ADB)
- nova_agent.lab.io.SimGameIO          (wraps Game2048Sim + brutalist renderer)

The cognitive layer (decision / affect / memory / reflection) MUST NOT
instantiate either implementation directly. main.run() takes a GameIO
instance via the build_io() factory and is otherwise source-agnostic.

See ADR-0008 for the rationale and rejected alternatives.
"""

from typing import Protocol

from nova_agent.action.adb import SwipeDirection
from nova_agent.perception.types import BoardState


class GameIO(Protocol):
    """Game-agnostic I/O surface used by the cognitive layer."""

    def read_board(self) -> BoardState:
        """Return the current board state (4x4 grid + score)."""
        ...

    def apply_move(self, direction: SwipeDirection) -> None:
        """Apply a move. Live: ADB keyevent + animation wait.
        Sim: deterministic merge + spawn (RNG-seeded).
        """
        ...

    def screenshot_b64(self) -> str:
        """Return a base64-encoded PNG of the current board state.
        Live: emulator screen capture (PNG bytes from Capture.to_vlm_bytes).
        Sim: brutalist renderer output.
        """
        ...
