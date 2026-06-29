"""
GridObject represents one detected object on the grid — for example, a
single contiguous red block.

It stores only what can be directly observed from the cells themselves:
which cells belong to it, what color(s) it has, and geometric measurements
(area, bounding box, center, width, height) that are derived automatically
from those cells. It also records which segmentation method was used to
find it, since there may be more than one valid way to group cells into
objects.

Two fields are intentionally left empty at this stage:
    role_distribution -> a guess at what the object DOES in the game
                         (e.g. {"wall": 0.6, "pushable": 0.3}), to be filled
                         in later by watching how it behaves across actions
    confidence        -> how sure we are that this object's current
                         description is correct

This class makes no guesses and does no reasoning — it only describes what
is visible. Anything that requires comparing this object to ANOTHER object
(distance, containment, alignment) does not belong here, since it requires
more than one object to make sense. That logic lives elsewhere (in a
topology/relations module).
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

    # ---- geometric measurements, computed directly from the cell positions ----
    
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
