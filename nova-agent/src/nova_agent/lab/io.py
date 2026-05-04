"""SimGameIO — wraps Game2048Sim + brutalist renderer behind GameIO.

Tiny adapter; zero state of its own. Lives in nova_agent.lab.io to
keep the lab-specific imports (sim, render) co-located.
"""

from __future__ import annotations

import base64

from nova_agent.action.adb import SwipeDirection
from nova_agent.lab.render import render_board
from nova_agent.lab.sim import Game2048Sim
from nova_agent.perception.types import BoardState


class SimGameIO:
    def __init__(self, *, sim: Game2048Sim) -> None:
        self._sim = sim

    def read_board(self) -> BoardState:
        return self._sim.board

    def apply_move(self, direction: SwipeDirection) -> None:
        # Discard the bool return; GameIO contract returns None.
        self._sim.apply_move(direction)

    def screenshot_b64(self) -> str:
        return base64.b64encode(render_board(self._sim.board)).decode("ascii")
