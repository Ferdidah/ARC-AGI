from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

import numpy as np

from .grid import Grid


@dataclass(frozen=True)
class CellChange:
    """One exact cell-level difference between two same-shaped grids."""

    row: int
    col: int
    old: int
    new: int


@dataclass(frozen=True)
class Delta:
    """Exact substrate diff between two grids."""

    changes: tuple[CellChange, ...]

    @property
    def empty(self) -> bool:
        return not self.changes

    @property
    def n_changed(self) -> int:
        return len(self.changes)

    @property
    def bbox(self) -> tuple[int, int, int, int] | None:
        """Changed-cell bounds as (min_row, min_col, max_row, max_col)."""
        if not self.changes:
            return None
        rows = [change.row for change in self.changes]
        cols = [change.col for change in self.changes]
        return (min(rows), min(cols), max(rows), max(cols))

    def gained(self, color: int) -> int:
        return sum(1 for change in self.changes if change.new == color)

    def lost(self, color: int) -> int:
        return sum(1 for change in self.changes if change.old == color)

    def net_color_change(self) -> dict[int, int]:
        net: Counter[int] = Counter()
        for change in self.changes:
            net[change.new] += 1
            net[change.old] -= 1
        return dict(net)


def grids_equal(a: Grid, b: Grid) -> bool:
    return a == b


def diff(a: Grid, b: Grid) -> Delta:
    if a.shape != b.shape:
        raise ValueError(f"cannot diff grids with different shapes: {a.shape} != {b.shape}")

    changed = np.argwhere(a.array != b.array)
    changes = tuple(
        CellChange(
            row=int(row),
            col=int(col),
            old=a.at(int(row), int(col)),
            new=b.at(int(row), int(col)),
        )
        for row, col in changed
    )
    return Delta(changes)
