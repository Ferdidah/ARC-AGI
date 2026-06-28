"""
play.py — type a game name, see its frames labelled.

This connects to the LIVE game (needs the SDK + an API key), plays a few
random actions to surface different frames, and visualizes each one with the
full topology overlay.

Setup once:
    pip install arc-agi-3
    export ARC_API_KEY=your_key      # get it at https://three.arcprize.org/user

Then just:
    python play.py ls20
    python play.py vc33 --steps 25 --full
    python play.py as66 --report      # also print the full text inspection
"""

import argparse

from arc3.loaders import play_random_and_record
from arc3.viz import show_scene, show_scene_full


def main():
    p = argparse.ArgumentParser()
    p.add_argument("game", help="public game id: ls20, as66, ft09, lp85, sp80, vc33")
    p.add_argument("--steps", type=int, default=15, help="how many actions to play")
    p.add_argument("--bg", default="auto", help="'auto' | 'none' | <int colour>")
    p.add_argument("--full", action="store_true", help="draw adjacency edges + areas")
    p.add_argument("--report", action="store_true", help="also print full text inspection")
    args = p.parse_args()

    bg = "auto" if args.bg == "auto" else (None if args.bg == "none" else int(args.bg))

    for i, obs in enumerate(play_random_and_record(game=args.game, max_steps=args.steps)):
        g = obs.settled
        print(f"\n=== {args.game} frame {i}  (state={obs.state.value}, score={obs.score}) ===")
        if args.report:
            from inspect_frame import report          # reuse your text dumper
            report(g, bg=bg)
        if args.full:
            show_scene_full(g, background=bg, save=f"{args.game}_{i:03d}.png")
        else:
            show_scene(g, background=bg, save=f"{args.game}_{i:03d}.png")
        print(f"  wrote {args.game}_{i:03d}.png")


if __name__ == "__main__":
    main()