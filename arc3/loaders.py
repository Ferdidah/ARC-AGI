"""
loaders — get REAL ARC-AGI-3 frames into the pipeline.

Two sources, neither required to test the synthetic path:

  1) JSONL recordings. The arc_agi toolkit can save game recordings as JSONL
     (one record per step). `load_jsonl_frames` reads those into Observations
     so you can replay a real game offline and eyeball the segmentation on every
     frame — no API key needed.

  2) Live environment. `play_random_and_record` drives the real env with the
     official SDK and yields an Observation per step. Requires `pip install
     arc-agi-3` and an API key in your env. Use this to capture fresh frames.

If you don't have recordings yet, the fastest way to get some:
    pip install arc-agi-3
    arc-agi-3 --agent=random --game=ls20    # records to JSONL by default
then point load_jsonl_frames at the recording directory.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterator

from .substrate.observation import Observation
from .substrate.grid import Grid


def load_jsonl_frames(path: str | Path) -> list[Observation]:
    """Load a recorded game (JSONL, one step per line) into Observations.

    Tolerant of schema drift: each line is a dict; we look for a 'frame' field
    (the grid sequence) and the usual state/score fields. Lines without a frame
    are skipped (some recordings interleave metadata lines)."""
    path = Path(path)
    obs: list[Observation] = []
    with path.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            # the frame may be nested under a 'data'/'frame_data' wrapper
            payload = rec.get("frame_data", rec.get("data", rec))
            if not isinstance(payload, dict) or "frame" not in payload:
                continue
            try:
                obs.append(Observation.from_sdk(payload))
            except Exception:
                continue
    return obs


def grids_from_recording(path: str | Path) -> list[Grid]:
    """Just the settled grids from a recording — handy for batch-visualizing."""
    return [o.settled for o in load_jsonl_frames(path)]


def play_random_and_record(game: str = "ls20", max_steps: int = 60) -> Iterator[Observation]:
    """Drive the LIVE environment with random actions, yielding an Observation
    per step. Requires the arc-agi-3 SDK and an API key. Imported lazily so this
    module loads fine without the SDK installed."""
    try:
        import random
        import arc_agi
        from arcengine import GameAction, GameState
    except ImportError as e:
        raise ImportError(
            "live play needs the SDK: pip install arc-agi-3  (and set your API key)"
        ) from e

    arc = arc_agi.Arcade()
    env = arc.make(game)
    if env is None:
        raise RuntimeError(f"failed to create env for game {game!r}")

    for _ in range(max_steps):
        action = random.choice(env.action_space)
        data = {}
        if action.is_complex():  # ACTION6 needs coordinates
            data = {"x": random.randint(0, 63), "y": random.randint(0, 63)}
        raw = env.step(action, data=data)
        if raw is None:
            break
        raw = env.step(action, data=data)
        if raw is None:
            break
        yield Observation.from_sdk(raw)
        if raw.state in (GameState.WIN, GameState.GAME_OVER):
            env.reset()
