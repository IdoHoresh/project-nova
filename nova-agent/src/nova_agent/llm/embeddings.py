"""Spatial embedding for 2048 boards.

Cosine similarity reflects board structural similarity. NOT a hash —
hashes destroy similarity by design (avalanche effect) and were a load-
bearing bug in an earlier draft.
"""

from __future__ import annotations

import math
from typing import Sequence

EMBED_DIM: int = 16  # 4x4 grid, one component per cell


def embed_board(grid: Sequence[Sequence[int]], dim: int = EMBED_DIM) -> list[float]:
    """16-D L2-normalized log-tile spatial embedding.

    Component i (0..15) = log2(tile)/16 at row=i//4, col=i%4 (0.0 if empty).
    `dim` kwarg retained for API compatibility but must equal EMBED_DIM=16
    in v1; LanceDB schema asserts dimensionality on connect.
    """
    if dim != EMBED_DIM:
        raise ValueError(
            f"v1 spatial embedding is fixed at {EMBED_DIM} dims (4x4 grid). "
            f"To change dimensionality, update EMBED_DIM and LanceDB schema together."
        )
    flat: list[float] = []
    for row in grid:
        for v in row:
            flat.append(0.0 if v == 0 else math.log2(v) / 16.0)
    if len(flat) != EMBED_DIM:
        raise ValueError(f"grid must yield {EMBED_DIM} cells; got {len(flat)}")
    norm = math.sqrt(sum(x * x for x in flat))
    if norm == 0.0:
        return flat
    return [x / norm for x in flat]
