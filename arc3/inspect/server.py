"""
server — the inspector backend (standard library only, no pip installs).

Slice 2 adds LIVE PLAY: the server holds one persistent LiveGame session and
steps it one action at a time. Human-play and agent-play are the SAME loop with
a different ActionSource.

Run:
    python -m arc3.inspect.server
then open http://localhost:8000

Routes:
    GET  /                      -> the single-page GUI
    GET  /api/snapshot          -> current Snapshot as JSON
    POST /api/load              -> load a STATIC frame (demo / paste / recording)
    POST /api/config            -> change segmentation_rule / background
    --- live play (Slice 2) ---
    POST /api/start_game {game} -> open + reset a live session; first snapshot
    POST /api/action {id,x,y}   -> step the live session by one action
    POST /api/reset             -> reset the current live session
    POST /api/agent_step        -> let the (random) agent choose+play one action
    GET  /api/history           -> list of recorded snapshots (for the timeline)
"""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Optional

import numpy as np

from ..raw.grid import Grid
from .snapshot_builder import build_snapshot
from .session import LiveGame, Action, RandomSource

STATIC_DIR = Path(__file__).parent / "static"


class Session:
    """Single source of truth held by the server: either a STATIC frame
    (demo/paste/recording) or a LIVE game session."""

    def __init__(self):
        self.grid: Optional[Grid] = None
        self.step: int = 0
        self.segmentation_rule: str = "connectivity-4"
        self.background = "auto"
        self.connectivity: int = 4
        self.live: Optional[LiveGame] = None      # set when a game is started
        self.history: list[dict] = []             # recorded snapshots (timeline)
        self._random_agent = RandomSource()
        self.load_demo()

    # ---- static sources -----------------------------------------------------
    def load_demo(self):
        rows = [
            [5, 5, 4, 1, 5, 5, 5, 5],
            [6, 6, 5, 5, 5, 5, 5, 5],
            [6, 6, 0, 5, 0, 3, 5, 5],
            [5, 5, 0, 5, 5, 5, 5, 5],
            [5, 5, 0, 5, 5, 5, 5, 5],
            [10, 10, 0, 5, 5, 5, 4, 5],
            [10, 10, 0, 5, 5, 5, 5, 5],
            [10, 1, 0, 5, 5, 5, 5, 5],
        ]
        self.live = None
        self.grid = Grid.from_nested(rows)
        self.step = 0
        self.history = []

    def load_paste(self, rows):
        self.live = None
        self.grid = Grid.from_nested(rows)
        self.step = 0
        self.history = []

    def load_recording(self, path: str, index: int = 0):
        from ..loaders import grids_from_recording
        grids = grids_from_recording(path)
        if not grids:
            raise ValueError(f"no frames in recording {path!r}")
        index = max(0, min(index, len(grids) - 1))
        self.live = None
        self.grid = grids[index]
        self.step = index
        self.history = []

    # ---- live game ----------------------------------------------------------
    def start_game(self, game: str):
        self.live = LiveGame(game)
        obs = self.live.reset()
        self.grid = obs.settled
        self.step = 0
        self.history = []
        self._record()

    def do_action(self, action: Action):
        if self.live is None:
            raise RuntimeError("no live game — start one first")
        obs = self.live.step(action)
        self.grid = obs.settled
        self.step = self.live.action_count
        self._record()

    def reset_live(self):
        if self.live is None:
            raise RuntimeError("no live game to reset")
        obs = self.live.reset()
        self.grid = obs.settled
        self.step = 0
        self.history = []
        self._record()

    def agent_step(self):
        """Let the (random) agent choose one action from the current snapshot
        and play it. This is the SAME path the real planner will use later."""
        if self.live is None:
            raise RuntimeError("agent play needs a live game")
        snap = self.snapshot()
        available = self.live.available_action_ids()
        action = self._random_agent.choose(snap, available)
        if action is None:
            return  # nothing to do
        self.do_action(action)

    # ---- snapshot -----------------------------------------------------------
    def bg_value(self):
        if self.background in ("auto", "none"):
            return None if self.background == "none" else "auto"
        return int(self.background)

    def _meta(self) -> dict:
        if self.live is None or self.live.latest is None:
            return {}
        o = self.live.latest
        return {
            "game_id": self.live.game,
            "state": o.state.value,
            "score": o.score,
            "available_actions": list(o.available_actions),
        }

    def snapshot(self) -> dict:
        m = self._meta()
        snap = build_snapshot(
            self.grid,
            step=self.step,
            segmentation_rule=self.segmentation_rule,
            background=self.bg_value(),
            connectivity=self.connectivity,
            game_id=m.get("game_id"),
            state=m.get("state"),
            score=m.get("score"),
            available_actions=m.get("available_actions"),
        )
        d = snap.to_dict()
        # annotate live-play info for the GUI
        d["is_live"] = self.live is not None
        if self.live is not None:
            la = self.live.last_action
            d["last_action"] = None if la is None else {"id": la.id, "x": la.x, "y": la.y}
            d["action_count"] = self.live.action_count
        return d

    def _record(self):
        self.history.append(self.snapshot())


SESSION = Session()


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body, ctype):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, obj, code=200):
        self._send(code, json.dumps(obj).encode(), "application/json")

    def _read_body(self) -> dict:
        n = int(self.headers.get("Content-Length", 0))
        return json.loads(self.rfile.read(n).decode() or "{}") if n else {}

    def log_message(self, *a):
        pass

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            return self._send(200, (STATIC_DIR / "index.html").read_bytes(),
                              "text/html; charset=utf-8")
        if self.path.startswith("/api/snapshot"):
            try:
                return self._json(SESSION.snapshot())
            except Exception as e:
                return self._json({"error": str(e)}, 500)
        if self.path.startswith("/api/history"):
            return self._json({"steps": len(SESSION.history), "history": SESSION.history})
        return self._send(404, b"not found", "text/plain")

    def do_POST(self):
        try:
            body = self._read_body()
        except Exception as e:
            return self._json({"error": f"bad body: {e}"}, 400)

        try:
            if self.path == "/api/load":
                src = body.get("source", "demo")
                if src == "demo":
                    SESSION.load_demo()
                elif src == "paste":
                    SESSION.load_paste(body["rows"])
                elif src == "recording":
                    SESSION.load_recording(body["path"], int(body.get("index", 0)))
                else:
                    return self._json({"error": f"unknown source {src!r}"}, 400)
                return self._json(SESSION.snapshot())

            if self.path == "/api/config":
                if "segmentation_rule" in body:
                    SESSION.segmentation_rule = body["segmentation_rule"]
                    SESSION.connectivity = 8 if "8" in body["segmentation_rule"] else 4
                if "background" in body:
                    SESSION.background = body["background"]
                return self._json(SESSION.snapshot())

            if self.path == "/api/start_game":
                SESSION.start_game(body["game"])
                return self._json(SESSION.snapshot())

            if self.path == "/api/action":
                act = Action(int(body["id"]), body.get("x"), body.get("y"))
                SESSION.do_action(act)
                return self._json(SESSION.snapshot())

            if self.path == "/api/reset":
                SESSION.reset_live()
                return self._json(SESSION.snapshot())

            if self.path == "/api/agent_step":
                SESSION.agent_step()
                return self._json(SESSION.snapshot())

        except Exception as e:
            return self._json({"error": str(e)}, 500)

        return self._send(404, b"not found", "text/plain")


def main(host="127.0.0.1", port=8000):
    srv = ThreadingHTTPServer((host, port), Handler)
    print(f"\n  arc3 inspector running -> http://{host}:{port}\n  (Ctrl+C to stop)\n")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\n  stopped.")
        srv.shutdown()


if __name__ == "__main__":
    main()
