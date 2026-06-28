"""
GridObject — an L1 object: a BUNDLE of stacked descriptive primitives.

A single object simultaneously carries primitives from several descriptive
layers at once:
    A1 substrate   -> colour(s), and (later) a colour-role
    A2 measurement -> area, bbox, centroid, width, height   (computed here)
    A4 objectness  -> the cell mask + a stable identity + which grouping rule
                      produced it
plus two semantic slots that the DETERMINISTIC extractors leave blank and that
ML/inference fill in later:
    role_distribution -> {role: prob}, e.g. {"wall": 0.6, "pushable": 0.3, ...}
    confidence        -> scalar belief in this object's current labelling

Geometry measurements are cached_property functions of the cell mask, so they
can never go stale relative to the cells. Anything RELATIONAL (distance to
another object, containment, alignment) is NOT here — it lives in topology,
because it depends on a second object or a reference frame.

This is a pure data record. It performs no inference.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from functools import cached_property


@dataclass
class GridObject:
    id: int
    cells: frozenset[tuple[int, int]]      # (row, col) members
    colors: frozenset[int]                 # colour(s) present in the object
    grouping: str                          # which segmentation rule produced it
    # ---- semantic slots (filled by later layers; deterministic code leaves blank)
    role_distribution: dict[str, float] = field(default_factory=dict)
    confidence: float = 0.0

    # ---- A2 measurement: pure functions of the cell mask ---------------------

    @cached_property
    def area(self) -> int:
        """Number of cells (size)."""
        return len(self.cells)

    @cached_property
    def bbox(self) -> tuple[int, int, int, int]:
        """(min_row, min_col, max_row, max_col)."""
        rs = [r for r, _ in self.cells]
        cs = [c for _, c in self.cells]
        return (min(rs), min(cs), max(rs), max(cs))

    @cached_property
    def height(self) -> int:
        r0, _, r1, _ = self.bbox
        return r1 - r0 + 1

    @cached_property
    def width(self) -> int:
        _, c0, _, c1 = self.bbox
        return c1 - c0 + 1

    @cached_property
    def centroid(self) -> tuple[float, float]:
        """(row, col) centre of mass."""
        n = len(self.cells)
        sr = sum(r for r, _ in self.cells)
        sc = sum(c for _, c in self.cells)
        return (sr / n, sc / n)

    @cached_property
    def is_rectangular_filled(self) -> bool:
        """True if the object exactly fills its bounding box (a solid rect)."""
        return self.area == self.height * self.width

    @cached_property
    def normalized_shape(self) -> frozenset[tuple[int, int]]:
        """Translation-invariant shape: cells shifted so bbox corner is (0,0).
        This is the CANONICALIZATION used to recognize 'the same shape
        elsewhere'. (Rotation/reflection/colour invariance is added later, only
        when the game shows those invariances.)"""
        r0, c0, _, _ = self.bbox
        return frozenset((r - r0, c - c0) for r, c in self.cells)

    @property
    def primary_color(self) -> int:
        """Most-representative colour (smallest index if multiple, stable)."""
        return min(self.colors)

    def __repr__(self) -> str:
        r0, c0, r1, c1 = self.bbox
        return (
            f"GridObject(id={self.id}, colors={sorted(self.colors)}, "
            f"area={self.area}, bbox=({r0},{c0})-({r1},{c1}), "
            f"grouping={self.grouping!r})"
        )
