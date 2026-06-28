"""
Scene — the L1 product of the deterministic perception pipeline.

This is the foundational, NON-fuzzy part of module 1 (perception). It turns a
raw grid (L0) into a typed set of objects with measurements and topology (L1),
EXCEPT for the one genuinely fuzzy step — role assignment — which is left blank
(every object gets an empty role_distribution). A later ML role-prior fills it.

Because segmentation is a hypothesis, a Scene is built under ONE named
segmentation choice; the system can build several Scenes from the same grid
(connectivity-4, connectivity-8, color-class) and let evidence/MDL choose. That
parallel-hypothesis management is a higher layer; here we just make it cheap to
produce any single hypothesis cleanly.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ..substrate.grid import Grid
from ..model.object import GridObject
from .descriptive import segmentation, topology


@dataclass
class Scene:
    grid: Grid
    objects: list[GridObject]
    background: int | None
    segmentation_rule: str
    grid_symmetries: dict[str, bool] = field(default_factory=dict)

    def by_id(self, oid: int) -> GridObject:
        for o in self.objects:
            if o.id == oid:
                return o
        raise KeyError(oid)

    def objects_of_color(self, color: int) -> list[GridObject]:
        return [o for o in self.objects if color in o.colors]

    def adjacency_pairs(self, connectivity: int = 4) -> list[tuple[int, int]]:
        return topology.touching_pairs(self.objects, connectivity)

    def __repr__(self) -> str:
        return (
            f"Scene({len(self.objects)} objects via {self.segmentation_rule!r}, "
            f"bg={self.background}, sym={[k for k,v in self.grid_symmetries.items() if v]})"
        )


def build_scene(
    grid: Grid,
    segmentation_rule: str = "connectivity-4",
    background: int | None = "auto",
) -> Scene:
    """Run the deterministic L0->L1 pipeline under one segmentation hypothesis.

    Args:
        segmentation_rule: 'connectivity-4' | 'connectivity-8' | 'color-class'.
        background: an int colour to treat as background, None to keep all
            colours, or 'auto' to use the most-common-colour PRIOR.
    """
    if background == "auto":
        bg = segmentation.guess_background(grid)
    else:
        bg = background  # int or None

    if segmentation_rule == "connectivity-4":
        objs = segmentation.connected_components(grid, connectivity=4, background=bg)
    elif segmentation_rule == "connectivity-8":
        objs = segmentation.connected_components(grid, connectivity=8, background=bg)
    elif segmentation_rule == "color-class":
        objs = segmentation.color_classes(grid, background=bg)
    else:
        raise ValueError(f"unknown segmentation_rule {segmentation_rule!r}")

    return Scene(
        grid=grid,
        objects=objs,
        background=bg,
        segmentation_rule=segmentation_rule,
        grid_symmetries=topology.symmetries(grid),
    )
