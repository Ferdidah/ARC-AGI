"""
visualize_frame.py — visualize ANY ARC-AGI-3 frame.

Point it at a real recording, a live game, or a frame you paste in.
Put this file in the PROJECT ROOT (next to demo_viz.py / README.md).

Usage:
    # 1) visualize every frame in a recording (JSONL the SDK saved)
    python visualize_frame.py --recording path/to/game.jsonl

    #    ...just one frame from it (e.g. frame index 10):
    python visualize_frame.py --recording path/to/game.jsonl --index 10

    # 2) pull frames live from a game (needs SDK + API key)
    python visualize_frame.py --game ls20 --steps 40

    # 3) visualize a frame you paste into this file (see paste_frame below)
    python visualize_frame.py --paste

Options that apply to all modes:
    --bg auto      background colour: 'auto' (most common), 'none', or an int
    --rule connectivity-4 | connectivity-8 | color-class
    --compare      show all three segmentation hypotheses side by side
    --no-save      try to show interactively instead of writing PNGs
"""

import argparse
import numpy as np

from arc3.substrate.grid import Grid
from arc3.viz import show_scene, compare_segmentations, show_delta


# --------------------------------------------------------------------------- #
# OPTION 3: paste a frame here and run `python visualize_frame.py --paste`
# Replace this with any grid you want — a list of rows of ints 0..15.
# --------------------------------------------------------------------------- #
def paste_frame() -> Grid:
    rows = [
        [0, 0, 0, 0, 0],
        [0, 3, 0, 0, 0],
        [5, 5, 5, 5, 5],
        [7, 0, 0, 0, 0],
        [7, 1, 0, 0, 0],
    ]
    return Grid.from_nested(rows)


# --------------------------------------------------------------------------- #
# Background parsing: 'auto' -> most common (a prior), 'none' -> keep all, or int
# --------------------------------------------------------------------------- #
def parse_bg(bg_arg: str):
    if bg_arg == "auto":
        return "auto"
    if bg_arg == "none":
        return None
    return int(bg_arg)


def visualize_one(grid: Grid, args, tag: str = "frame"):
    """Render a single grid with the chosen settings."""
    bg = parse_bg(args.bg)
    save = None if args.no_save else f"{tag}.png"
    if args.compare:
        # compare_segmentations resolves 'auto' bg per panel; pass an int/None.
        bg_resolved = grid.most_common_color() if bg == "auto" else bg
        out = compare_segmentations(grid, background=bg_resolved, save=save)
    else:
        out = show_scene(grid, background=bg, segmentation_rule=args.rule, save=save)
    if save:
        print(f"  wrote {save}")
    return out


# --------------------------------------------------------------------------- #
# Mode 1: a recording file
# --------------------------------------------------------------------------- #
def run_recording(args):
    from arc3.loaders import grids_from_recording
    grids = grids_from_recording(args.recording)
    if not grids:
        print("No frames found in that recording. Is the path/JSONL right?")
        return
    print(f"Loaded {len(grids)} frames from {args.recording}")

    if args.index is not None:
        g = grids[args.index]
        print(f"\n--- frame {args.index} ---  {g}")
        visualize_one(g, args, tag=f"frame_{args.index}")
    else:
        # visualize all (writes one PNG per frame); also show deltas between them
        for i, g in enumerate(grids):
            print(f"\n--- frame {i} ---  {g}")
            visualize_one(g, args, tag=f"frame_{i:03d}")
        # bonus: a delta panel for each consecutive pair
        if len(grids) > 1 and not args.no_save:
            for i in range(len(grids) - 1):
                if grids[i].shape == grids[i + 1].shape:
                    show_delta(grids[i], grids[i + 1], save=f"delta_{i:03d}_{i+1:03d}.png")
            print(f"\n  wrote delta_*.png for {len(grids)-1} consecutive pairs")


# --------------------------------------------------------------------------- #
# Mode 2: live game
# --------------------------------------------------------------------------- #
def run_live(args):
    from arc3.loaders import play_random_and_record
    grids = []
    for i, obs in enumerate(play_random_and_record(game=args.game, max_steps=args.steps)):
        grids.append(obs.settled)
        print(f"step {i}: {obs.settled}  state={obs.state.value} score={obs.score}")
    if not grids:
        print("No frames captured.")
        return
    print(f"\nVisualizing {len(grids)} captured frames...")
    for i, g in enumerate(grids):
        visualize_one(g, args, tag=f"{args.game}_{i:03d}")


# --------------------------------------------------------------------------- #
# Mode 3: pasted frame
# --------------------------------------------------------------------------- #
def run_paste(args):
    g = paste_frame()
    print(f"Pasted frame: {g}")
    visualize_one(g, args, tag="pasted")


def main():
    p = argparse.ArgumentParser(description="Visualize any ARC-AGI-3 frame.")
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument("--recording", help="path to an SDK JSONL recording")
    src.add_argument("--game", help="live game id, e.g. ls20 (needs SDK + key)")
    src.add_argument("--paste", action="store_true", help="use paste_frame() in this file")

    p.add_argument("--index", type=int, default=None, help="single frame index (recording mode)")
    p.add_argument("--steps", type=int, default=40, help="steps to play (live mode)")
    p.add_argument("--bg", default="auto", help="'auto' | 'none' | <int colour>")
    p.add_argument("--rule", default="connectivity-4",
                   choices=["connectivity-4", "connectivity-8", "color-class"])
    p.add_argument("--compare", action="store_true", help="show 3 segmentation hypotheses")
    p.add_argument("--no-save", action="store_true", help="show interactively instead of saving PNGs")

    args = p.parse_args()
    if args.recording:
        run_recording(args)
    elif args.game:
        run_live(args)
    else:
        run_paste(args)


if __name__ == "__main__":
    main()