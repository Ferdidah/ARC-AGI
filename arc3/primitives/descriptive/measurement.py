"""
Measurement (A2) + Frame-of-reference (A5) — the RELATIONAL quantities.

Per-object geometry (area, bbox, centroid, width, height) lives on GridObject
itself, because it is a pure function of one object's cells. This module holds
the measurements that need a SECOND thing — another object, or a declared
reference frame — which is exactly why A5 (frame-of-reference) is inseparable
from A2: "distance" and "offset" are meaningless until you say "to what".

All deterministic. No semantics: these report numbers, not meanings.
"""

from __future__ import annotations

from ...model.object import GridObject
from ...substrate.grid import Grid


# ---- object <-> object ------------------------------------------------------

def centroid_offset(a: GridObject, b: GridObject) -> tuple[float, float]:
    """Vector from a's centroid to b's centroid, as (d_row, d_col).
    The relative-position primitive ('b relative to a')."""
    ar, ac = a.centroid
    br, bc = b.centroid
    return (br - ar, bc - ac)


def manhattan_centroid_distance(a: GridObject, b: GridObject) -> float:
    dr, dc = centroid_offset(a, b)
    return abs(dr) + abs(dc)


def min_cell_distance(a: GridObject, b: GridObject, metric: str = "chebyshev") -> int:
    """Closest approach between the two objects' cells.
    metric: 'manhattan' (4-move) or 'chebyshev' (8-move)."""
    best = None
    for ar, ac in a.cells:
        for br, bc in b.cells:
            dr, dc = abs(ar - br), abs(ac - bc)
            d = (dr + dc) if metric == "manhattan" else max(dr, dc)
            if best is None or d < best:
                best = d
                if best == 0:
                    return 0
    return -1 if best is None else best


def bbox_contains(outer: GridObject, inner: GridObject) -> bool:
    """True if inner's bounding box sits fully inside outer's (a cheap,
    appearance-level containment hypothesis — NOT topological enclosure)."""
    o0, o1, o2, o3 = outer.bbox
    i0, i1, i2, i3 = inner.bbox
    return o0 <= i0 and o1 <= i1 and i2 <= o2 and i3 <= o3


# ---- object <-> grid (reference frame = the grid) ---------------------------

def distance_to_edges(obj: GridObject, grid: Grid) -> dict[str, int]:
    """Gap between the object's bounding box and each grid edge."""
    r0, c0, r1, c1 = obj.bbox
    return {
        "top": r0,
        "left": c0,
        "bottom": grid.height - 1 - r1,
        "right": grid.width - 1 - c1,
    }


def touches_edge(obj: GridObject, grid: Grid) -> bool:
    d = distance_to_edges(obj, grid)
    return any(v == 0 for v in d.values())


# ---- colour-as-scalar (A1/A2) -----------------------------------------------

def color_scale_value(color: int, scale: list[int]) -> int | None:
    """Position of `color` on an ordered colour scale, or None if not on it.
    Used only when colour has been hypothesized to be SCALAR/ordered (e.g.
    liquid levels, dominance). For most games colour is categorical and this is
    not invoked."""
    try:
        return scale.index(color)
    except ValueError:
        return None
