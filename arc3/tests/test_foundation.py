"""
Tests for the foundational slice. These pin down the EXACT, deterministic parts
hard — they are the bedrock everything fuzzy is built on, so they get strict,
hand-checked assertions.

Run with: pytest -q   (from the arc3 project root)
"""

import numpy as np
import pytest

from arc3.substrate import Grid, Observation, State, diff, grids_equal
from arc3.primitives import build_scene
from arc3.primitives.descriptive import measurement, topology
from arc3.model import GridObject


# --------------------------------------------------------------------------- #
# Substrate: Grid
# --------------------------------------------------------------------------- #

def test_grid_basic_shape_and_access():
    g = Grid.from_nested([[0, 1, 2], [3, 4, 5]])
    assert g.shape == (2, 3)
    assert g.height == 2 and g.width == 3
    assert g.at(0, 1) == 1
    # (0,1) as (row,col) must equal click (x=1, y=0)
    assert g.at_xy(x=1, y=0) == g.at(row=0, col=1)


def test_grid_is_immutable():
    g = Grid.from_nested([[0, 1], [2, 3]])
    with pytest.raises(ValueError):
        g.array[0, 0] = 5  # underlying buffer is read-only


def test_grid_rejects_out_of_palette():
    with pytest.raises(ValueError):
        Grid.from_nested([[0, 16]])  # 16 is out of [0,15]


def test_grid_equality_and_hash_enable_sets():
    g1 = Grid.from_nested([[1, 1], [2, 2]])
    g2 = Grid.from_nested([[1, 1], [2, 2]])
    g3 = Grid.from_nested([[1, 1], [2, 3]])
    assert g1 == g2 and hash(g1) == hash(g2)
    assert g1 != g3
    # usable as set members (needed for visited-sets later)
    assert len({g1, g2, g3}) == 2


def test_color_stats():
    g = Grid.from_nested([[0, 0, 0], [0, 1, 2]])
    assert g.most_common_color() == 0
    assert g.colors() == {0, 1, 2}
    assert g.color_counts()[0] == 4


# --------------------------------------------------------------------------- #
# Substrate: Observation (SDK adapter)
# --------------------------------------------------------------------------- #

def test_observation_single_frame_from_dict():
    fd = {
        "frame": [[[0, 1], [2, 3]]],          # sequence with ONE grid
        "state": "NOT_FINISHED",
        "score": 3,
        "win_score": 254,
        "available_actions": [1, 2, 3, 4],
    }
    obs = Observation.from_sdk(fd)
    assert obs.settled.shape == (2, 2)
    assert obs.state is State.NOT_FINISHED
    assert obs.score == 3 and obs.win_score == 254
    assert obs.available_actions == (1, 2, 3, 4)
    assert not obs.is_animated
    assert not obs.is_terminal


def test_observation_animation_sequence_settles_on_last():
    # two-frame animation: a cell 'moves' right between turns
    fd = {
        "frame": [
            [[1, 0, 0]],     # frame A
            [[0, 1, 0]],     # frame B
            [[0, 0, 1]],     # settled frame C
        ],
        "state": "NOT_FINISHED",
        "score": 0,
        "available_actions": [1],
    }
    obs = Observation.from_sdk(fd)
    assert obs.is_animated
    assert len(obs.frames) == 3
    assert obs.settled == Grid.from_nested([[0, 0, 1]])


def test_observation_win_state():
    fd = {"frame": [[[0]]], "state": "WIN", "score": 1, "available_actions": []}
    obs = Observation.from_sdk(fd)
    assert obs.won and obs.is_terminal


# --------------------------------------------------------------------------- #
# Substrate: Delta (exact diff = the evidence atom + divergence primitive)
# --------------------------------------------------------------------------- #

def test_delta_empty_means_no_change():
    g = Grid.from_nested([[0, 1], [2, 3]])
    d = diff(g, g)
    assert d.empty and d.n_changed == 0
    assert grids_equal(g, g)


def test_delta_reports_exact_cell_changes():
    a = Grid.from_nested([[0, 0], [0, 0]])
    b = Grid.from_nested([[0, 5], [0, 0]])
    d = diff(a, b)
    assert d.n_changed == 1
    ch = d.changes[0]
    assert (ch.row, ch.col, ch.old, ch.new) == (0, 1, 0, 5)
    assert d.bbox == (0, 1, 0, 1)
    assert d.gained(5) == 1 and d.lost(0) == 1


def test_delta_move_signature_is_conservation_neutral():
    # a single '1' cell moves right: net colour change should be zero for 1
    a = Grid.from_nested([[1, 0, 0]])
    b = Grid.from_nested([[0, 1, 0]])
    d = diff(a, b)
    net = d.net_color_change()
    assert net.get(1, 0) == 0          # gained one, lost one -> conserved
    assert d.n_changed == 2


def test_delta_requires_same_shape():
    a = Grid.from_nested([[0]])
    b = Grid.from_nested([[0, 0]])
    with pytest.raises(ValueError):
        diff(a, b)


# --------------------------------------------------------------------------- #
# Descriptive: Segmentation hypotheses
# --------------------------------------------------------------------------- #

def test_connectivity_4_vs_8_diagonal():
    # two cells touching only diagonally:
    g = Grid.from_nested([[1, 0], [0, 1]])
    s4 = build_scene(g, "connectivity-4", background=0)
    s8 = build_scene(g, "connectivity-8", background=0)
    assert len(s4.objects) == 2   # diagonal NOT connected under 4
    assert len(s8.objects) == 1   # diagonal connected under 8


def test_color_class_groups_noncontiguous():
    g = Grid.from_nested([[1, 0, 1], [0, 0, 0]])
    s = build_scene(g, "color-class", background=0)
    ones = [o for o in s.objects if 1 in o.colors]
    assert len(ones) == 1
    assert ones[0].area == 2          # both 1s, though not touching


def test_background_excluded():
    g = Grid.from_nested([[0, 0, 0], [0, 2, 0]])
    s = build_scene(g, "connectivity-4", background=0)
    assert len(s.objects) == 1
    assert s.objects[0].colors == {2}
    assert s.objects[0].area == 1


# --------------------------------------------------------------------------- #
# Descriptive: Measurement on GridObject + relational
# --------------------------------------------------------------------------- #

def test_object_geometry():
    # an L-shaped object
    cells = frozenset({(1, 1), (2, 1), (2, 2)})
    o = GridObject(id=0, cells=cells, colors=frozenset({3}), grouping="test")
    assert o.area == 3
    assert o.bbox == (1, 1, 2, 2)
    assert o.height == 2 and o.width == 2
    assert not o.is_rectangular_filled       # 3 cells in a 2x2 bbox
    # canonical (translation-invariant) shape
    assert o.normalized_shape == frozenset({(0, 0), (1, 0), (1, 1)})


def test_relational_distance_and_offset():
    a = GridObject(id=0, cells=frozenset({(0, 0)}), colors=frozenset({1}), grouping="t")
    b = GridObject(id=1, cells=frozenset({(0, 3)}), colors=frozenset({2}), grouping="t")
    assert measurement.min_cell_distance(a, b, "manhattan") == 3
    assert measurement.centroid_offset(a, b) == (0.0, 3.0)


def test_distance_to_edges():
    g = Grid.from_nested([[0, 0, 0, 0]] * 4)  # 4x4
    o = GridObject(id=0, cells=frozenset({(1, 1)}), colors=frozenset({0}), grouping="t")
    d = measurement.distance_to_edges(o, g)
    assert d == {"top": 1, "left": 1, "bottom": 2, "right": 2}


# --------------------------------------------------------------------------- #
# Descriptive: Topology + symmetry
# --------------------------------------------------------------------------- #

def test_adjacency():
    a = GridObject(id=0, cells=frozenset({(0, 0)}), colors=frozenset({1}), grouping="t")
    b = GridObject(id=1, cells=frozenset({(0, 1)}), colors=frozenset({2}), grouping="t")
    c = GridObject(id=2, cells=frozenset({(2, 2)}), colors=frozenset({3}), grouping="t")
    assert topology.adjacent(a, b, 4)
    assert not topology.adjacent(a, c, 8)


def test_grid_symmetry_detection():
    g = Grid.from_nested([[1, 2, 1], [3, 4, 3]])  # left-right mirror
    sym = topology.symmetries(g)
    assert sym["mirror_horizontal"] is True
    assert sym["mirror_vertical"] is False


# --------------------------------------------------------------------------- #
# End-to-end: a synthetic 'liquid game' frame
# --------------------------------------------------------------------------- #

def test_end_to_end_liquidlike_scene():
    """A tiny stand-in for the vc33 liquid game: grey background (0), a black
    separator wall (5), white liquid (7) below it, a blue button (4), and a
    green target band (3). We just check the deterministic perception recovers
    the right objects, measurements and topology — NO semantics asserted."""
    frame = [
        [0, 0, 0, 0, 0],
        [0, 0, 0, 3, 0],   # green target band at (1,3)
        [5, 5, 5, 5, 5],   # black separator wall (row 2)
        [7, 0, 0, 0, 0],   # white liquid surface
        [7, 4, 0, 0, 0],   # white liquid + blue button (4,1)
    ]
    g = Grid.from_nested(frame)
    scene = build_scene(g, "connectivity-4", background=0)

    colors = {c for o in scene.objects for c in o.colors}
    assert colors == {3, 4, 5, 7}            # background 0 excluded

    wall = next(o for o in scene.objects if 5 in o.colors)
    liquid = next(o for o in scene.objects if 7 in o.colors)
    button = next(o for o in scene.objects if 4 in o.colors)

    assert wall.width == 5 and wall.height == 1      # a horizontal bar
    assert wall.is_rectangular_filled
    assert liquid.area == 2                            # two white cells
    # the button sits adjacent to the liquid (shares an edge)
    assert topology.adjacent(button, liquid, 4)
    # the wall sits directly above the liquid column (same column band)
    assert topology.same_col_band(wall, liquid)
