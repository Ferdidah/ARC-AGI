"""
measurement.py — measurements that require comparing TWO things (two objects,
or an object and the grid), as opposed to measurements of a single object
alone.

A single object's own geometry (its area, bounding box, center, width,
height) lives directly on the GridObject itself, since those can be computed
from that one object's cells alone. Everything in THIS file needs a second
reference point to mean anything — e.g. "distance" or "position relative to"
only make sense once you say distance/relative TO WHAT. That's why these
functions all take two arguments (two objects, or an object and the grid).

Object-to-object:
    centroid_offset()              -> direction + distance from one object's
                                       center to another's
    manhattan_centroid_distance()  -> straight-line-ish distance between centers
    min_cell_distance()            -> closest distance between the two
                                       objects' actual cells (not just centers)
    bbox_contains()                -> does one object's bounding rectangle
                                       fully contain another's? (NOTE: this
                                       checks rectangles only — it does NOT
                                       check if one object is truly enclosed
                                       inside another, e.g. inside a ring shape)

Object-to-grid:
    distance_to_edges()  -> gap between an object and each edge of the grid
    touches_edge()       -> is the object touching any edge at all?

Color-as-position:
    color_scale_value()  -> where does this color fall on an ordered scale
                            (e.g. low to high)? Only relevant for the rare
                            game where color values represent an ordered
                            quantity (like a fill level) rather than just a
                            category/label.

Everything here is exact and deterministic — these functions report
measured numbers, not guesses about meaning.
"""

from __future__ import annotations

from ...model.object import GridObject
from ...raw.grid import Grid


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
