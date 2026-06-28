"""
Snapshot — the single contract between the agent and the GUI.

A Snapshot captures EVERYTHING the system currently believes at one instant. The
GUI is a pure passive renderer of this object; it never computes model state
itself. The agent produces one Snapshot per step; a recorded game is just a list
of Snapshots you can scrub through.

DESIGN PRINCIPLE — anticipate the whole system now:
The schema includes fields for layers that DON'T EXIST YET (interaction graph,
goal hypotheses, action hypotheses, simulation/divergence). They are present but
empty. This lets the GUI show a complete map of the agent from day one — most
panels say "not computed yet" and light up one by one as you build each module,
WITHOUT ever changing this schema or the GUI core.

Everything here is plain data + a to_dict() that yields JSON-safe primitives.
No numpy, no agent objects leak across the boundary.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


# --------------------------------------------------------------------------- #
# Per-object view (L1) — a flattened, serializable copy of a GridObject's facts
# --------------------------------------------------------------------------- #
@dataclass
class ObjectView:
    id: int
    cells: list[list[int]]                 # [[row, col], ...]
    colors: list[int]
    primary_color: int
    area: int
    bbox: list[int]                        # [r0, c0, r1, c1]
    height: int
    width: int
    centroid: list[float]                  # [row, col]
    is_rectangular_filled: bool
    normalized_shape: list[list[int]]      # canonical (translation-invariant) shape
    grouping: str
    # type-equivalence (which "kind" this object is an instance of)
    type_id: Optional[int] = None
    # semantic slots (filled by later ML/inference; empty for now)
    role_distribution: dict[str, float] = field(default_factory=dict)
    confidence: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return self.__dict__


# --------------------------------------------------------------------------- #
# Relations (L1/L2 boundary)
# --------------------------------------------------------------------------- #
@dataclass
class RelationView:
    adjacency: list[list[int]] = field(default_factory=list)        # [[a, b], ...]
    directions: list[dict] = field(default_factory=list)            # {a,b,dir} b relative to a
    alignment: list[dict] = field(default_factory=list)            # {a,b,kinds:[...]}
    containment: list[dict] = field(default_factory=list)          # {outer,inner,kind}

    def to_dict(self) -> dict[str, Any]:
        return {
            "adjacency": self.adjacency,
            "directions": self.directions,
            "alignment": self.alignment,
            "containment": self.containment,
        }


# --------------------------------------------------------------------------- #
# Placeholder views for LATER layers (present but empty now)
# --------------------------------------------------------------------------- #
@dataclass
class GraphView:
    """Generic node-link graph; reused for interaction graph, goal tree, DAG."""
    nodes: list[dict] = field(default_factory=list)   # {id, label, type, confidence}
    edges: list[dict] = field(default_factory=list)   # {src, dst, kind, condition, confidence}

    def to_dict(self) -> dict[str, Any]:
        return {"nodes": self.nodes, "edges": self.edges}


# --------------------------------------------------------------------------- #
# The Snapshot — one complete view of the system at one step
# --------------------------------------------------------------------------- #
@dataclass
class Snapshot:
    step: int
    # --- L0 substrate ---
    grid: list[list[int]]                  # the raw frame, [row][col]
    palette: list[str]                     # 16 hex colours the GUI renders with
    background: Optional[int]
    segmentation_rule: str
    grid_symmetries: dict[str, bool] = field(default_factory=dict)

    # --- L1 objects + relations ---
    objects: list[ObjectView] = field(default_factory=list)
    relations: RelationView = field(default_factory=RelationView)
    types: list[dict] = field(default_factory=list)   # {type_id, members:[ids], signature}

    # --- environment meta (filled when from a real game; None for pasted) ---
    game_id: Optional[str] = None
    state: Optional[str] = None
    score: Optional[int] = None
    available_actions: list[int] = field(default_factory=list)

    # --- LATER LAYERS: present but empty until those modules exist ---
    interaction_graph: GraphView = field(default_factory=GraphView)  # L2 (module 3)
    goal_tree: GraphView = field(default_factory=GraphView)          # C2 (module 3)
    goal_hypotheses: list[dict] = field(default_factory=list)        # ranked guesses
    action_hypotheses: list[dict] = field(default_factory=list)      # what a button does
    predicted_grid: Optional[list[list[int]]] = None                 # simulator output (module 5)
    divergence_cells: list[list[int]] = field(default_factory=list)  # predicted vs real (module 7)
    notes: list[str] = field(default_factory=list)                   # free-text agent commentary

    def to_dict(self) -> dict[str, Any]:
        return {
            "step": self.step,
            "grid": self.grid,
            "palette": self.palette,
            "background": self.background,
            "segmentation_rule": self.segmentation_rule,
            "grid_symmetries": self.grid_symmetries,
            "objects": [o.to_dict() for o in self.objects],
            "relations": self.relations.to_dict(),
            "types": self.types,
            "game_id": self.game_id,
            "state": self.state,
            "score": self.score,
            "available_actions": self.available_actions,
            "interaction_graph": self.interaction_graph.to_dict(),
            "goal_tree": self.goal_tree.to_dict(),
            "goal_hypotheses": self.goal_hypotheses,
            "action_hypotheses": self.action_hypotheses,
            "predicted_grid": self.predicted_grid,
            "divergence_cells": self.divergence_cells,
            "notes": self.notes,
        }
