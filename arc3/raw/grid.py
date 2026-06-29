"""
Grid — the raw, unprocessed grid data for one ARC-AGI-3 frame.

A frame is a grid (up to 64x64) of color values (integers 0-15), with
(0,0) at the TOP-LEFT.

CRITICAL coordinate convention (a classic source of bugs — read this):
    - Cells are indexed as (row, col), which is the same as (y, x).
    - The API's ACTION6 click takes {"x": col, "y": row}.
    - So `grid[row, col]` and a click at `x=col, y=row` refer to the SAME cell.
    - The helper functions below make the row/col <-> x/y conversion explicit,
      so nothing has to guess which order to use.

A Grid is immutable: it wraps a read-only numpy array and is hashable, so it
can be stored in sets later (e.g. for tracking visited states during search,
or for detecting duplicate frames).

This class holds ONLY colors and positions — no concept of "objects" or
"meaning" exists at this level. Objects are built from this in a later step
(see object.py).
"""

from __future__ import annotations

from collections import Counter
from typing import Iterable

import numpy as np

NUM_COLORS = 16  # palette is 0..15
MAX_SIDE = 64    # frames are at most 64x64


class Grid:
    """Immutable, hashable 2D array of colour indices (0..15)."""

    __slots__ = ("_a", "_hash")

    def __init__(self, array: np.ndarray | Iterable):
        a = np.asarray(array, dtype=np.int16)
        if a.ndim != 2:
            raise ValueError(f"Grid must be 2D, got shape {a.shape!r}")
        if a.size and (a.min() < 0 or a.max() >= NUM_COLORS):
            raise ValueError(
                f"colour indices must be in [0,{NUM_COLORS - 1}], "
                f"got range [{a.min()},{a.max()}]"
            )
        if a.shape[0] > MAX_SIDE or a.shape[1] > MAX_SIDE:
            raise ValueError(f"grid {a.shape} exceeds max side {MAX_SIDE}")
        a.setflags(write=False)  # enforce immutability
        self._a = a
        self._hash = None

    # ---- construction helpers ------------------------------------------------

    @classmethod
    def from_nested(cls, rows: list[list[int]]) -> "Grid":
        """Build from the API's nested-list frame representation."""
        return cls(np.array(rows, dtype=np.int16))

    # ---- basic shape / access ------------------------------------------------

    @property
    def array(self) -> np.ndarray:
        """Read-only view of the underlying array, indexed [row, col]."""
        return self._a

    @property
    def height(self) -> int:
        return self._a.shape[0]

    @property
    def width(self) -> int:
        return self._a.shape[1]

    @property
    def shape(self) -> tuple[int, int]:
        return self._a.shape  # (height, width) == (rows, cols)

    def at(self, row: int, col: int) -> int:
        """Colour at (row, col). Same cell as a click {x: col, y: row}."""
        return int(self._a[row, col])

    def at_xy(self, x: int, y: int) -> int:
        """Colour at API coordinates (x=col, y=row)."""
        return int(self._a[y, x])

    def in_bounds(self, row: int, col: int) -> bool:
        return 0 <= row < self.height and 0 <= col < self.width

    # ---- colour statistics (still pure substrate, no semantics) --------------

    def color_counts(self) -> Counter:
        """How many cells hold each colour."""
        vals, counts = np.unique(self._a, return_counts=True)
        return Counter({int(v): int(c) for v, c in zip(vals, counts)})

    def colors(self) -> set[int]:
        return set(int(v) for v in np.unique(self._a))

    def most_common_color(self) -> int:
        """The commonest colour. NOTE: a prior for 'background', NOT a fact.
        Background is defined functionally (a colour objects pass through),
        which only later layers can confirm. This is just the cheap guess."""
        return self.color_counts().most_common(1)[0][0]

    def mask(self, color: int) -> np.ndarray:
        """Boolean mask of cells equal to `color`."""
        return self._a == color

    # ---- equality / hashing (enables visited-sets and exact diffing) ---------

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Grid):
            return NotImplemented
        return self._a.shape == other._a.shape and bool(np.array_equal(self._a, other._a))

    def __hash__(self) -> int:
        if self._hash is None:
            self._hash = hash((self._a.shape, self._a.tobytes()))
        return self._hash

    def __repr__(self) -> str:
        return f"Grid({self.height}x{self.width}, colors={sorted(self.colors())})"

    def render(self, charmap: str = " .:-=+*#%@01234X") -> str:
        """Tiny ASCII render for debugging (16 chars for 16 colours)."""
        rows = []
        for r in range(self.height):
            rows.append("".join(charmap[self._a[r, c]] for c in range(self.width)))
        return "\n".join(rows)
