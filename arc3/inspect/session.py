"""
session — a persistent, step-at-a-time live game, plus the ActionSource seam.

The static inspector was stateless: one frame in, one snapshot out. Playing is a
SEQUENCE — action -> new frame -> action -> ... — over a game session that stays
OPEN on ARC's server between your actions. So the server must hold ONE live
session and step it.

The key abstraction is ActionSource: "the thing that chooses the next action
given the current snapshot." Human-play and agent-play become the SAME loop with
a different source:
    - HumanSource  : the action comes from a GUI click (server waits for it)
    - RandomSource : picks any available action (the dumb agent for wiring up)
    - AgentSource  : later — your planner picks, reading the same Snapshot

This module imports the SDK lazily, so the inspector still runs offline (you just
can't start a live game without the SDK + key).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Protocol

from ..raw.grid import Grid
from ..raw.observation import Observation


# --------------------------------------------------------------------------- #
# Action representation (decoupled from the SDK enum)
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class Action:
    """A chosen action. `id` is 1..6 (ACTION1..6); ACTION6 needs x,y (a click)."""
    id: int
    x: Optional[int] = None
    y: Optional[int] = None

    @property
    def is_click(self) -> bool:
        return self.id == 6


# --------------------------------------------------------------------------- #
# LiveGame — the persistent session the server holds
# --------------------------------------------------------------------------- #
class LiveGame:
    """Wraps an SDK env. Opens once; step() advances one action and keeps the
    session open. Holds the latest Observation so the server can build snapshots
    without re-fetching."""

    def __init__(self, game: str):
        self.game = game
        self._env = None
        self._GameAction = None
        self._GameState = None
        self.latest: Optional[Observation] = None
        self.last_action: Optional[Action] = None
        self.action_count: int = 0

    def _ensure_env(self):
        if self._env is not None:
            return
        try:
            import arc_agi
            from arcengine import GameAction, GameState
        except ImportError as e:
            raise ImportError(
                "live play needs the SDK: pip install arc-agi-3 (and set your API key)"
            ) from e
        self._GameAction = GameAction
        self._GameState = GameState
        arc = arc_agi.Arcade()
        env = arc.make(self.game)
        if env is None:
            raise RuntimeError(f"failed to create env for game {self.game!r}")
        self._env = env

    def reset(self) -> Observation:
        self._ensure_env()
        raw = self._env.reset()
        self.latest = Observation.from_sdk(raw)
        self.last_action = None
        self.action_count = 0
        return self.latest

    def available_action_ids(self) -> list[int]:
        if self.latest is None:
            return []
        return list(self.latest.available_actions)

    def _to_sdk_action(self, action: Action):
        """Map our Action.id (1..6) onto the SDK's GameAction enum members."""
        GA = self._GameAction
        # SDK exposes ACTION1..ACTION6; pick by name to avoid ordinal guessing.
        name = f"ACTION{action.id}"
        member = getattr(GA, name, None)
        if member is None:
            raise ValueError(f"SDK has no {name}")
        return member

    def step(self, action: Action) -> Observation:
        """Advance the live session by one action; return the new Observation."""
        self._ensure_env()
        sdk_action = self._to_sdk_action(action)
        data = {}
        if action.is_click:
            if action.x is None or action.y is None:
                raise ValueError("ACTION6 (click) requires x and y")
            data = {"x": int(action.x), "y": int(action.y)}
        raw = self._env.step(sdk_action, data=data)
        if raw is None:
            raise RuntimeError("env.step returned None")
        self.latest = Observation.from_sdk(raw)
        self.last_action = action
        self.action_count += 1
        # auto-reset on terminal so the session keeps playing levels
        if self.latest.is_terminal:
            # leave terminal observation visible; caller decides whether to reset
            pass
        return self.latest


# --------------------------------------------------------------------------- #
# ActionSource seam — human vs agent, same loop
# --------------------------------------------------------------------------- #
class ActionSource(Protocol):
    def choose(self, snapshot: dict, available: list[int]) -> Optional[Action]:
        """Return the next Action, or None to wait (human) / stop (agent)."""
        ...


class RandomSource:
    """The dumb agent: pick any available action (ACTION6 gets random coords).
    Lets the whole agent-play pipeline run before any real planning exists."""

    def __init__(self, seed: int | None = None):
        import random
        self._r = random.Random(seed)

    def choose(self, snapshot: dict, available: list[int]) -> Optional[Action]:
        if not available:
            return None
        aid = self._r.choice(available)
        if aid == 6:
            H = len(snapshot["grid"])
            W = len(snapshot["grid"][0])
            return Action(6, x=self._r.randrange(W), y=self._r.randrange(H))
        return Action(aid)


# AgentSource will be added later: same .choose() signature, but it reads the
# snapshot's objects/relations/graph and returns a planned action. Because it
# obeys this Protocol, it drops into the exact same server loop as RandomSource.
