"""
describe_frame.py — dump EVERYTHING the perception layer currently finds.

Shows the full descriptive picture (L0->L1): substrate facts, per-object
measurements, objectness, and ALL relational/topology primitives (adjacency,
neighbours, alignment, distances, containment) + grid symmetry.

What it does NOT show — because these layers don't exist yet:
  - roles (wall/avatar/...) : the ML role-prior isn't built (role_distribution is empty)
  - dynamics / interactions : need two frames + an action (delta-interpreter, later)
  - the interaction graph   : L2, later

Put this in the PROJECT ROOT (next to explore.py). Run:
    python describe_frame.py --paste
    python describe_frame.py --recording game.jsonl --index 5
    python describe_frame.py --paste --connectivity 8
"""

import argparse
import numpy as np

from arc3.substrate.grid import Grid
from arc3.primitives.scene import build_scene
from arc3.primitives.descriptive import topology, measurement


# ---- paste your frame here -------------------------------------------------
def paste_frame() -> Grid:
    from arc3.my_frame import get
    return get()

def parse_bg(bg_arg: str):
    if bg_arg == "auto":
        return "auto"
    if bg_arg == "none":
        return None
    return int(bg_arg)


def report(grid: Grid, bg="auto", connectivity: int = 4,
           rule: str = "connectivity-4"):
    scene = build_scene(grid, rule, background=bg)
    objs = scene.objects

    line = "=" * 72
    print(line)
    print("SUBSTRATE (L0)")
    print(line)
    print(f"  shape (HxW)        : {grid.height} x {grid.width}")
    print(f"  colours present    : {sorted(grid.colors())}")
    print(f"  colour counts      : {dict(grid.color_counts())}")
    print(f"  most-common (bg?)  : {grid.most_common_color()}  "
          f"(prior for background, NOT a fact)")
    print(f"  background used    : {scene.background}")

    print("\n" + line)
    print(f"GRID SYMMETRY (A3)")
    print(line)
    for k, v in topology.symmetries(grid).items():
        print(f"  {k:<18}: {v}")

    print("\n" + line)
    print(f"OBJECTS (L1)  —  segmentation: {scene.segmentation_rule}, "
          f"{len(objs)} objects")
    print(line)
    for o in sorted(objs, key=lambda o: o.id):
        r0, c0, r1, c1 = o.bbox
        cr, cc = o.centroid
        edges = measurement.distance_to_edges(o, grid)
        print(f"\n  ── object #{o.id} ──────────────────────────────")
        print(f"    colours          : {sorted(o.colors)}  (primary {o.primary_color})")
        print(f"    area (cells)     : {o.area}")
        print(f"    bbox             : ({r0},{c0}) -> ({r1},{c1})")
        print(f"    size (HxW)       : {o.height} x {o.width}")
        print(f"    centroid (r,c)   : ({cr:.1f}, {cc:.1f})")
        print(f"    solid rectangle? : {o.is_rectangular_filled}")
        print(f"    normalized shape : {sorted(o.normalized_shape)}")
        print(f"    dist to edges    : {edges}  (touches edge: {measurement.touches_edge(o, grid)})")
        print(f"    role             : {o.role_distribution or '(unknown — ML layer not built)'}")

    print("\n" + line)
    print(f"TOPOLOGY / RELATIONS (A3)  —  connectivity-{connectivity}")
    print(line)

    # adjacency: who neighbours whom
    pairs = topology.touching_pairs(objs, connectivity)
    print(f"\n  ADJACENCY (touching pairs): {len(pairs)} edges")
    # build a neighbour map for readability
    neigh = {o.id: [] for o in objs}
    for a, b in pairs:
        neigh[a].append(b)
        neigh[b].append(a)
    for oid in sorted(neigh):
        ns = sorted(neigh[oid])
        cols = sorted(scene.by_id(oid).colors)
        print(f"    object #{oid} {cols} neighbours: "
              f"{['#' + str(n) for n in ns] if ns else '(none)'}")

    # alignment bands
    print(f"\n  ALIGNMENT (same row/col band):")
    for i in range(len(objs)):
        for j in range(i + 1, len(objs)):
            a, b = objs[i], objs[j]
            row = topology.same_row_band(a, b)
            col = topology.same_col_band(a, b)
            if row or col:
                tags = []
                if row: tags.append("same-row-band")
                if col: tags.append("same-col-band")
                print(f"    #{a.id} & #{b.id}: {', '.join(tags)}")

    # pairwise distances + offsets + containment
    print(f"\n  PAIRWISE DISTANCE / OFFSET / CONTAINMENT:")
    for i in range(len(objs)):
        for j in range(i + 1, len(objs)):
            a, b = objs[i], objs[j]
            dmin = measurement.min_cell_distance(a, b, "chebyshev")
            off = measurement.centroid_offset(a, b)
            contains = ""
            if measurement.bbox_contains(a, b):
                contains = f"  (#{a.id} bbox contains #{b.id})"
            elif measurement.bbox_contains(b, a):
                contains = f"  (#{b.id} bbox contains #{a.id})"
            print(f"    #{a.id}->#{b.id}: min-gap={dmin}, "
                  f"centroid-offset=({off[0]:+.1f},{off[1]:+.1f}){contains}")

    print("\n" + line + "\n")
    return scene


def get_grid(args) -> Grid:
    if args.recording:
        from arc3.loaders import grids_from_recording
        grids = grids_from_recording(args.recording)
        idx = args.index if args.index is not None else 0
        print(f"(loaded {len(grids)} frames; showing index {idx})")
        return grids[idx]
    return paste_frame()


def main():
    p = argparse.ArgumentParser()
    src = p.add_mutually_exclusive_group()
    src.add_argument("--recording", help="SDK JSONL recording path")
    src.add_argument("--paste", action="store_true", help="use paste_frame()")
    p.add_argument("--index", type=int, default=None)
    p.add_argument("--bg", default="auto", help="'auto' | 'none' | <int>")
    p.add_argument("--connectivity", type=int, default=4, choices=[4, 8])
    p.add_argument("--rule", default="connectivity-4",
                   choices=["connectivity-4", "connectivity-8", "color-class"])
    args = p.parse_args()

    grid = get_grid(args)
    report(grid, bg=parse_bg(args.bg), connectivity=args.connectivity, rule=args.rule)


if __name__ == "__main__":
    main()