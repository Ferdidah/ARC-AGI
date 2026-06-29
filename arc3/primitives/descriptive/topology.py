"""
topology.py — spatial relationships BETWEEN objects, and symmetry of the
whole grid.

These are relations you get "for free" just from where things are positioned:
    - adjacency        -> are two objects touching?
    - alignment        -> do two objects share a row or column?
    - grid symmetry     -> is the whole grid mirror-symmetric, or the same
                           after a 90/180-degree rotation?

Symmetry matters beyond just being a nice fact to know: several possible game
goals are defined directly in terms of it (e.g. "make this side of the grid
mirror the other side"), so this isn't just descriptive — it's something a
goal-checker may need to query directly.

Everything here is exact and deterministic — no guessing involved.
"""

from __future__ import annotations

import numpy as np

from ...model.object import GridObject
from ...raw.grid import Grid

_NEI4 = [(-1, 0), (1, 0), (0, -1), (0, 1)]
_NEI8 = _NEI4 + [(-1, -1), (-1, 1), (1, -1), (1, 1)]


# ---- object adjacency -------------------------------------------------------

def adjacent(a: GridObject, b: GridObject, connectivity: int = 4) -> bool:
    """True if any cell of a touches any cell of b under the given connectivity."""
    nei = _NEI4 if connectivity == 4 else _NEI8
    bcells = b.cells
    for ar, ac in a.cells:
        for dr, dc in nei:
            if (ar + dr, ac + dc) in bcells:
                return True
    return False


def touching_pairs(objects: list[GridObject], connectivity: int = 4) -> list[tuple[int, int]]:
    """All (id_a, id_b) pairs of objects that are adjacent. O(n^2) over objects,
    fine for the tens-of-objects scale of these grids."""
    pairs = []
    for i in range(len(objects)):
        for j in range(i + 1, len(objects)):
            if adjacent(objects[i], objects[j], connectivity):
                pairs.append((objects[i].id, objects[j].id))
    return pairs


# ---- alignment --------------------------------------------------------------

def same_row_band(a: GridObject, b: GridObject) -> bool:
    """Bounding boxes overlap vertically (share at least one row)."""
    a0, _, a1, _ = a.bbox
    b0, _, b1, _ = b.bbox
    return not (a1 < b0 or b1 < a0)


def same_col_band(a: GridObject, b: GridObject) -> bool:
    """Bounding boxes overlap horizontally (share at least one column)."""
    _, a0, _, a1 = a.bbox
    _, b0, _, b1 = b.bbox
    return not (a1 < b0 or b1 < a0)


# ---- grid-level symmetry ----------------------------------------------------

def symmetries(grid: Grid) -> dict[str, bool]:
    """Which whole-grid symmetries currently hold. A default prior is
    colour-permutation invariance, but symmetry here is checked on the raw
    colours (exact), which is what a 'symmetrize/match' goal is judged against."""
    a = grid.array
    return {
        "mirror_horizontal": bool(np.array_equal(a, np.fliplr(a))),  # left-right
        "mirror_vertical": bool(np.array_equal(a, np.flipud(a))),    # top-bottom
        "rotate_180": bool(np.array_equal(a, np.rot90(a, 2))),
        "rotate_90": (a.shape[0] == a.shape[1]) and bool(np.array_equal(a, np.rot90(a))),
        "transpose": (a.shape[0] == a.shape[1]) and bool(np.array_equal(a, a.T)),
    }


def region_symmetries(grid: Grid, bbox: tuple[int, int, int, int]) -> dict[str, bool]:
    """Same symmetry check restricted to a sub-region (e.g. one half a goal
    asks to make symmetric). bbox = (min_row, min_col, max_row, max_col)."""
    r0, c0, r1, c1 = bbox
    sub = grid.array[r0:r1 + 1, c0:c1 + 1]
    return {
        "mirror_horizontal": bool(np.array_equal(sub, np.fliplr(sub))),
        "mirror_vertical": bool(np.array_equal(sub, np.flipud(sub))),
        "rotate_180": bool(np.array_equal(sub, np.rot90(sub, 2))),
    }
