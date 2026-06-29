"""
build_snapshot — turn a Grid (and optional env meta) into a Snapshot.

This is the ONLY place that reads the agent's real structures (Scene,
GridObject, topology, measurement) and flattens them into the serializable
Snapshot the GUI consumes. Keeping the translation in one place means the GUI
never touches agent internals, and adding a later layer = adding a few lines
here, not changing the GUI.

It also computes the two cheap descriptive wins we identified as missing:
  - type-equivalence groups (objects sharing canonical shape + primary colour)
  - directional relations (N/S/E/W) between adjacent objects
both of which make the inspector immediately more insightful.
"""

from __future__ import annotations

from typing import Optional

from ..substrate.grid import Grid
from ..primitives.scene import build_scene
from ..primitives.descriptive import topology, measurement
from .palette import ARC_COLORS  # self-contained palette (not coupled to viz)
from .snapshot import Snapshot, ObjectView, RelationView


def _direction(off_row: float, off_col: float) -> str:
    """Dominant compass direction of an offset vector (b relative to a).
    Rows increase downward, so +row = South."""
    if abs(off_row) >= abs(off_col):
        return "S" if off_row > 0 else "N"
    return "E" if off_col > 0 else "W"


def _type_signature(obj_view: ObjectView) -> tuple:
    """What makes two objects 'the same kind': identical canonical shape and
    primary colour. (Later this can relax to colour-invariant when the game
    shows colour permutation invariance.)"""
    shape = frozenset(tuple(c) for c in obj_view.normalized_shape)
    return (obj_view.primary_color, shape)


def build_snapshot(
    grid: Grid,
    step: int = 0,
    segmentation_rule: str = "connectivity-4",
    background="auto",
    connectivity: int = 4,
    *,
    game_id: Optional[str] = None,
    state: Optional[str] = None,
    score: Optional[int] = None,
    available_actions: Optional[list[int]] = None,
) -> Snapshot:
    scene = build_scene(grid, segmentation_rule, background=background)

    # ---- objects (flatten GridObject -> ObjectView) -------------------------
    obj_views: list[ObjectView] = []
    for o in scene.objects:
        r0, c0, r1, c1 = o.bbox
        cr, cc = o.centroid
        obj_views.append(
            ObjectView(
                id=o.id,
                cells=[[r, c] for (r, c) in sorted(o.cells)],
                colors=sorted(o.colors),
                primary_color=o.primary_color,
                area=o.area,
                bbox=[r0, c0, r1, c1],
                height=o.height,
                width=o.width,
                centroid=[round(cr, 2), round(cc, 2)],
                is_rectangular_filled=o.is_rectangular_filled,
                normalized_shape=[[r, c] for (r, c) in sorted(o.normalized_shape)],
                grouping=o.grouping,
                role_distribution=dict(o.role_distribution),
                confidence=o.confidence,
            )
        )

    # ---- type-equivalence grouping -----------------------------------------
    sig_to_type: dict[tuple, int] = {}
    types: list[dict] = []
    for ov in obj_views:
        sig = _type_signature(ov)
        if sig not in sig_to_type:
            tid = len(types)
            sig_to_type[sig] = tid
            types.append({
                "type_id": tid,
                "members": [],
                "primary_color": ov.primary_color,
                "shape_cells": ov.normalized_shape,
            })
        tid = sig_to_type[sig]
        ov.type_id = tid
        types[tid]["members"].append(ov.id)

    # ---- relations ----------------------------------------------------------
    by_id = {o.id: o for o in scene.objects}
    rel = RelationView()

    adj_pairs = topology.touching_pairs(scene.objects, connectivity)
    rel.adjacency = [[a, b] for (a, b) in adj_pairs]

    # directional relation for each adjacent pair (b relative to a)
    for a, b in adj_pairs:
        off = measurement.centroid_offset(by_id[a], by_id[b])
        rel.directions.append({"a": a, "b": b, "dir": _direction(off[0], off[1])})

    # alignment bands (only between objects that aren't trivially far — keep all
    # for now; a relevance filter can come later)
    objs = scene.objects
    for i in range(len(objs)):
        for j in range(i + 1, len(objs)):
            kinds = []
            if topology.same_row_band(objs[i], objs[j]):
                kinds.append("row")
            if topology.same_col_band(objs[i], objs[j]):
                kinds.append("col")
            if kinds:
                rel.alignment.append({"a": objs[i].id, "b": objs[j].id, "kinds": kinds})

    # bbox containment (cheap appearance-level; not true enclosure — flagged)
    for i in range(len(objs)):
        for j in range(len(objs)):
            if i == j:
                continue
            if measurement.bbox_contains(objs[i], objs[j]):
                rel.containment.append(
                    {"outer": objs[i].id, "inner": objs[j].id, "kind": "bbox"}
                )

    return Snapshot(
        step=step,
        grid=grid.array.tolist(),
        palette=list(ARC_COLORS),
        background=scene.background,
        segmentation_rule=scene.segmentation_rule,
        grid_symmetries=topology.symmetries(grid),
        objects=obj_views,
        relations=rel,
        types=types,
        game_id=game_id,
        state=state,
        score=score,
        available_actions=available_actions or [],
    )
