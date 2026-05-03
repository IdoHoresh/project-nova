from nova_agent.affect.types import AffectVector
from nova_agent.perception.types import BoardState

ANXIETY_TRIGGER = 0.6
HARD_MAX_TILE = 256
HARD_EMPTY_CELLS = 3


def should_use_tot(*, board: BoardState, affect: AffectVector) -> bool:
    """Trigger ToT (System 2) when the board is hard AND Nova is anxious.

    Anxiety alone is not enough — calm-but-tight boards are routine for the
    cheap ReAct decider; anxious-but-easy boards are usually a stale memory
    panicking on a trivial state.
    """
    if affect.anxiety <= ANXIETY_TRIGGER:
        return False
    return board.max_tile >= HARD_MAX_TILE or board.empty_cells <= HARD_EMPTY_CELLS
