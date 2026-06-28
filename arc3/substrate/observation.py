"""
Observation — adapter from the ARC-AGI-3 environment to our substrate.

The SDK hands the agent a `FrameData`-like object per turn. Per the docs:
    - `frame` is a SEQUENCE of one or more 64x64 grids. Multiple grids encode a
      non-interactive animation that plays out before the world SETTLES.
    - `state` is one of NOT_FINISHED / NOT_STARTED / WIN / GAME_OVER.
    - `score` is the cumulative score; `win_score` (a.k.a. score-to-win) is the
      threshold; `available_actions` lists the currently-legal action ids.

For the world-model loop, what matters is:
    - the SETTLED frame (the last grid in the sequence) — this is the state the
      next action acts upon, and the thing the simulator must predict;
    - the FULL sequence — because the in-between frames ARE evidence about
      dynamics (e.g. an object's motion path), which the delta-interpreter
      (module 2) will later use.

This adapter deliberately depends on NOTHING from the SDK at import time, so the
substrate stays testable offline. `from_sdk` accepts either a real FrameData
(duck-typed) or a plain dict (e.g. a recorded JSONL frame).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Sequence

from .grid import Grid


class State(str, Enum):
    NOT_STARTED = "NOT_STARTED"
    NOT_FINISHED = "NOT_FINISHED"
    WIN = "WIN"
    GAME_OVER = "GAME_OVER"

    @classmethod
    def coerce(cls, v: Any) -> "State":
        if isinstance(v, cls):
            return v
        s = getattr(v, "value", v)
        s = getattr(v, "name", s)  # tolerate enum-likes
        try:
            return cls(str(s).upper())
        except ValueError:
            return cls.NOT_FINISHED


@dataclass(frozen=True)
class Observation:
    """One turn's worth of environment feedback, normalized."""

    frames: tuple[Grid, ...]          # full animation sequence (>=1 grid)
    state: State                      # game state after this turn
    score: int                        # cumulative score
    win_score: int | None             # score threshold to win (may be unknown)
    available_actions: tuple[int, ...]  # legal action ids right now
    raw: Any = field(default=None, repr=False)  # original object, for escape hatches

    @property
    def settled(self) -> Grid:
        """The final, stable frame — what the next action acts upon."""
        return self.frames[-1]

    @property
    def is_animated(self) -> bool:
        """True if this turn returned an in-between animation sequence."""
        return len(self.frames) > 1

    @property
    def is_terminal(self) -> bool:
        return self.state in (State.WIN, State.GAME_OVER)

    @property
    def won(self) -> bool:
        return self.state is State.WIN

    # ---- construction --------------------------------------------------------

    @staticmethod
    def _grids_from_frame_field(frame: Any) -> tuple[Grid, ...]:
        """The `frame` field is a sequence of grids. Each grid may be a nested
        list OR a numpy array. Normalize each element via numpy, and decide
        'sequence of grids' vs 'single grid' by the resulting dimensionality.
        """
        import numpy as np

        arr = np.asarray(frame)
        if arr.ndim == 3:
            # (n_frames, H, W): a sequence of grids
            return tuple(Grid(arr[i]) for i in range(arr.shape[0]))
        elif arr.ndim == 2:
            # (H, W): a single bare grid
            return (Grid(arr),)
        elif arr.ndim == 1 and arr.dtype == object:
            # ragged: a list of grids of differing/again-nested form
            return tuple(Grid(np.asarray(g)) for g in frame)
        else:
            raise ValueError(
                f"can't interpret frame field with shape {arr.shape}, ndim {arr.ndim}"
            )

    @classmethod
    def from_sdk(cls, frame_data: Any) -> "Observation":
        """Build from an SDK FrameData object or an equivalent dict."""
        get = (lambda k, d=None: frame_data.get(k, d)) if isinstance(frame_data, dict) \
            else (lambda k, d=None: getattr(frame_data, k, d))

        frame = get("frame")
        if frame is None:
            raise ValueError("frame_data has no 'frame' field")
        grids = cls._grids_from_frame_field(frame)

        actions = get("available_actions", []) or []
        action_ids = tuple(
            int(getattr(a, "value", getattr(a, "id", a))) for a in actions
        )

        return cls(
            frames=grids,
            state=State.coerce(get("state", State.NOT_FINISHED)),
            score=int(get("score", 0) or 0),
            win_score=(int(get("win_score")) if get("win_score") is not None else None),
            available_actions=action_ids,
            raw=frame_data,
        )
