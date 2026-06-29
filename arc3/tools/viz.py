from __future__ import annotations

from collections.abc import Iterable

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import ListedColormap
from matplotlib.patches import Rectangle

from .primitives import build_scene
from .substrate import Grid, diff


ARC_COLORS = (
    "#000000",  # 0 black
    "#0074D9",  # 1 blue
    "#FF4136",  # 2 red
    "#2ECC40",  # 3 green
    "#FFDC00",  # 4 yellow
    "#AAAAAA",  # 5 grey
    "#F012BE",  # 6 magenta
    "#FF851B",  # 7 orange
    "#7FDBFF",  # 8 cyan
    "#870C25",  # 9 maroon
    "#FFFFFF",  # 10 white
    "#39CCCC",  # 11 teal
    "#B10DC9",  # 12 purple
    "#85144B",  # 13 plum
    "#3D9970",  # 14 olive
    "#111111",  # 15 near-black
)

_CMAP = ListedColormap(ARC_COLORS)


def _draw_grid(ax: plt.Axes, grid: Grid, title: str) -> None:
    ax.imshow(grid.array, cmap=_CMAP, vmin=0, vmax=15, interpolation="nearest")
    ax.set_title(title)
    ax.set_xticks(np.arange(-0.5, grid.width, 1), minor=True)
    ax.set_yticks(np.arange(-0.5, grid.height, 1), minor=True)
    ax.grid(which="minor", color="#222222", linewidth=0.3, alpha=0.35)
    ax.tick_params(left=False, bottom=False, labelleft=False, labelbottom=False)


def _outline_objects(ax: plt.Axes, objects: Iterable) -> None:
    for obj in objects:
        r0, c0, r1, c1 = obj.bbox
        ax.add_patch(
            Rectangle(
                (c0 - 0.5, r0 - 0.5),
                obj.width,
                obj.height,
                fill=False,
                edgecolor="#ff2d55",
                linewidth=1.8,
            )
        )
        ax.text(
            c0,
            r0,
            str(obj.id),
            color="#ff2d55",
            fontsize=8,
            fontweight="bold",
            ha="left",
            va="top",
            bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.75, "pad": 1},
        )


def show_scene(
    grid: Grid,
    background: int | None = "auto",
    segmentation_rule: str = "connectivity-4",
    save: str | None = None,
) -> None:
    scene = build_scene(grid, segmentation_rule, background=background)
    fig, ax = plt.subplots(figsize=(7, 7))
    _draw_grid(ax, grid, f"{scene.segmentation_rule}: {len(scene.objects)} objects")
    _outline_objects(ax, scene.objects)
    fig.tight_layout()
    if save:
        fig.savefig(save, dpi=160)
    else:
        plt.show()
    plt.close(fig)


def compare_segmentations(grid: Grid, background: int | None = "auto", save: str | None = None) -> None:
    rules = ("connectivity-4", "connectivity-8", "color-class")
    fig, axes = plt.subplots(1, len(rules), figsize=(15, 5))
    for ax, rule in zip(axes, rules, strict=True):
        scene = build_scene(grid, rule, background=background)
        _draw_grid(ax, grid, f"{rule}: {len(scene.objects)} objects")
        _outline_objects(ax, scene.objects)
    fig.tight_layout()
    if save:
        fig.savefig(save, dpi=160)
    else:
        plt.show()
    plt.close(fig)


def show_delta(before: Grid, after: Grid, save: str | None = None) -> None:
    d = diff(before, after)
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    _draw_grid(axes[0], before, "before")
    _draw_grid(axes[1], after, "after")
    _draw_grid(axes[2], after, f"changed cells: {d.n_changed}")
    for change in d.changes:
        axes[2].add_patch(
            Rectangle(
                (change.col - 0.5, change.row - 0.5),
                1,
                1,
                fill=False,
                edgecolor="#ff2d55",
                linewidth=2.2,
            )
        )
    fig.tight_layout()
    if save:
        fig.savefig(save, dpi=160)
    else:
        plt.show()
    plt.close(fig)
    
def show_scene_full(grid, background="auto", segmentation_rule="connectivity-4",
                    connectivity=4, save=None):
    """Like show_scene, but also draws ADJACENCY EDGES between object centroids
    and annotates each box with area. The visual form of the topology layer."""
    from .primitives.descriptive import topology
    scene = build_scene(grid, segmentation_rule, background=background)

    fig, ax = plt.subplots(figsize=(8, 8))
    _draw_grid(ax, grid, f"{scene.segmentation_rule}: {len(scene.objects)} objects "
                         f"[adjacency-{connectivity}]")
    _outline_objects(ax, scene.objects)          # <-- your file's helper name

    # draw a line between the centroids of every adjacent pair
    by_id = {o.id: o for o in scene.objects}
    for a_id, b_id in topology.touching_pairs(scene.objects, connectivity):
        ar, ac = by_id[a_id].centroid
        br, bc = by_id[b_id].centroid
        ax.plot([ac, bc], [ar, br], color="#FF00FF", linewidth=1.4, alpha=0.9)
        ax.plot([ac, bc], [ar, br], "o", color="#FF00FF", markersize=3)

    # annotate area at each object's centroid
    for o in scene.objects:
        cr, cc = o.centroid
        ax.text(cc, cr, str(o.area), color="white", fontsize=7,
                ha="center", va="center",
                bbox=dict(boxstyle="circle,pad=0.1", fc="black", ec="#FF00FF", alpha=0.7))

    fig.tight_layout()
    if save:
        fig.savefig(save, dpi=160)
    else:
        plt.show()
    plt.close(fig)