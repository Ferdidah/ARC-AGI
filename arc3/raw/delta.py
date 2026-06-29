"""
delta.py — exact cell-by-cell comparison between two grids.

Given two grids of the same shape (typically "before an action" and "after
an action"), this file computes exactly which cells changed and how.

CellChange  — one cell that changed: its position, its old color, its new color.
Delta       — the full set of CellChanges between two grids, plus some
              convenient summaries:
                  empty              -> did anything change at all?
                  n_changed          -> how many cells changed
                  bbox               -> smallest rectangle containing all changes
                  gained(color)      -> how many cells became this color
                  lost(color)        -> how many cells stopped being this color
                  net_color_change() -> net change in cell count, per color

diff(a, b) -- the function that actually computes a Delta from two grids.

This is purely mechanical: it compares raw colors cell-by-cell and reports
the facts, with no interpretation. It does not know that "5 cells changed
from blue to red because an object moved" — it only reports that 5 specific
cells changed color. Turning raw cell changes into object-level events
("object X moved") is a separate, later step.

Note: diff() requires both grids to have the same shape, and will raise an
error otherwise. If a game ever resizes the grid between frames, that case
needs to be handled separately before calling this.
"""

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
