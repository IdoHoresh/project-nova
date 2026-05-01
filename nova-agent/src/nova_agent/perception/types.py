from dataclasses import dataclass


@dataclass(frozen=True)
class BoardState:
    grid: list[list[int]]
    score: int

    def __post_init__(self) -> None:
        if len(self.grid) != 4 or any(len(r) != 4 for r in self.grid):
            raise ValueError("BoardState.grid must be 4x4")

    @property
    def empty_cells(self) -> int:
        return sum(1 for row in self.grid for v in row if v == 0)

    @property
    def max_tile(self) -> int:
        return max((v for row in self.grid for v in row), default=0)
