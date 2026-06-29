"""
segmentation.py — different ways of grouping grid cells into objects.

There's no single "correct" way to decide what counts as one object — that's
a question with COMPETING valid answers, and which answer is right gets
decided later, by watching what actually moves together when an action is
taken, and by seeing which grouping makes the game's rules simplest to state.
This file provides two such grouping methods, each as a separate function, so
the system can try more than one and compare:

    - connected_components(): cells of the same color count as one object
      only if they're actually touching (4-way or 8-way). This assumes
      "things that are near each other and the same color are one object."

    - color_classes(): ALL cells of a given color count as one object,
      anywhere on the grid, touching or not. This assumes "things that look
      the same are one object" — useful when a color represents a "kind" of
      thing that's scattered across the board rather than one solid shape.

Background handling: whichever color is designated as "background" gets
skipped entirely — it's treated as empty space that objects sit on top of,
not an object itself. guess_background() is a cheap fallback that just picks
the most common color as a guess; it's explicitly a guess, not a fact, and
something later in the pipeline should confirm or correct it.

NOTE: the strongest way to group cells — by what actually moves together
when you take an action — is NOT done here, because it needs two frames and
an action to compare, not just one. That logic belongs in a later step (the
delta/diff-based interpreter), not in this file. This file only ever looks
at a single, still frame.
"""

from __future__ import annotations

from collections import deque

import numpy as np

from ...raw.grid import Grid
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
