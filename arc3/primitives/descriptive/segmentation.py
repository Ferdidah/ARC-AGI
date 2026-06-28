"""
Segmentation (A4 objectness) — grouping cells into candidate objects.

There is no single 'correct' segmentation; there are COMPETING hypotheses, and
which one is right is decided later (by motion / common-fate and by MDL over the
dynamics). This module provides the hypotheses as separate, deterministic
functions so the system can hold several at once:

    - connected_components(connectivity=4|8): maximal same-colour touching blobs
      (the 'proximity + similarity' hypothesis).
    - color_classes(): all cells of a colour as one object, regardless of
      contiguity (the 'similarity only' hypothesis).

Background handling: cells of the background colour are EXCLUDED from objects
(background is the substrate things move through). Background is a functional
notion the system must confirm; here we accept it as a parameter, and offer
`guess_background` as the cheap most-common-colour PRIOR (explicitly a guess).

Common-fate (grouping by shared motion) is the strongest cue but requires two
frames + an action, so it is NOT here — it belongs to the delta-interpreter
(module 2). This module is single-frame only.
"""

from __future__ import annotations

from collections import deque

import numpy as np

from ...substrate.grid import Grid
from ...model.object import GridObject

_NEI4 = [(-1, 0), (1, 0), (0, -1), (0, 1)]
_NEI8 = _NEI4 + [(-1, -1), (-1, 1), (1, -1), (1, 1)]


def guess_background(grid: Grid) -> int:
    """Cheap PRIOR for the background colour (most common). Not a fact —
    a functional check (what objects pass through) confirms it later."""
    return grid.most_common_color()


def connected_components(
    grid: Grid,
    connectivity: int = 4,
    background: int | None = None,
    next_id: int = 0,
) -> list[GridObject]:
    """Maximal connected regions of equal colour (the connectivity hypothesis).

    Args:
        connectivity: 4 (von Neumann) or 8 (Moore).
        background: colour to skip entirely (None = segment all colours).
        next_id: starting object id (so ids can be unique across calls).
    """
    if connectivity == 4:
        nei = _NEI4
    elif connectivity == 8:
        nei = _NEI8
    else:
        raise ValueError("connectivity must be 4 or 8")

    a = grid.array
    h, w = grid.shape
    seen = np.zeros((h, w), dtype=bool)
    objects: list[GridObject] = []
    oid = next_id

    for r in range(h):
        for c in range(w):
            if seen[r, c]:
                continue
            color = int(a[r, c])
            if background is not None and color == background:
                seen[r, c] = True
                continue
            # BFS flood fill over equal-colour neighbours
            cells: list[tuple[int, int]] = []
            q = deque([(r, c)])
            seen[r, c] = True
            while q:
                cr, cc = q.popleft()
                cells.append((cr, cc))
                for dr, dc in nei:
                    nr, nc = cr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w and not seen[nr, nc] and a[nr, nc] == color:
                        seen[nr, nc] = True
                        q.append((nr, nc))
            objects.append(
                GridObject(
                    id=oid,
                    cells=frozenset(cells),
                    colors=frozenset({color}),
                    grouping=f"connectivity-{connectivity}",
                )
            )
            oid += 1

    return objects


def color_classes(
    grid: Grid,
    background: int | None = None,
    next_id: int = 0,
) -> list[GridObject]:
    """One object per colour, gathering ALL cells of that colour regardless of
    contiguity (the similarity-only hypothesis). Useful when a colour names a
    'kind' that is scattered across the board."""
    a = grid.array
    objects: list[GridObject] = []
    oid = next_id
    for color in sorted(grid.colors()):
        if background is not None and color == background:
            continue
        rs, cs = np.nonzero(a == color)
        cells = frozenset((int(r), int(c)) for r, c in zip(rs, cs))
        objects.append(
            GridObject(
                id=oid,
                cells=cells,
                colors=frozenset({int(color)}),
                grouping="color-class",
            )
        )
        oid += 1
    return objects
