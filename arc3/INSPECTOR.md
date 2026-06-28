# arc3 inspector (Slices 1–2)

A live, clickable view of what the system believes about a game — and now you
can PLAY the game through it, or let a (random for now) agent play, and watch
the model update per action. Zero extra dependencies (stdlib server + one page).

## Run
    python -m arc3.inspect.server
    # open http://localhost:8000

## Slice 1 — inspect (static)
- Load a frame: pasted grid (JSON rows) or the demo.
- Click any object → full attribute panel (colours, area, bbox, size, centroid,
  canonical shape, grouping, role[blank], confidence).
- Relations of the selected object: directional neighbours (N/S/E/W), alignment
  bands, bbox-containment.
- Object types (same canonical shape + primary colour) grouped as T0, T1, …
- Switch segmentation (4/8/colour-class) and background live.

## Slice 2 — play (live)  ← NEW
- Type a game id (e.g. `vc33`) → **load game** opens a LIVE session (needs the
  SDK + API key).
- **Me mode**: action buttons appear for exactly the game's available actions
  (A1–A4 as arrows, A5 interact, A6 = click mode → click a grid cell to send
  ACTION6 at x=col,y=row), plus reset. Each action steps the live game and the
  whole model re-renders.
- **Agent mode**: a random agent plays on its own (polling loop) — proves the
  agent pipeline runs end to end. Swap the RandomSource for a real planner later
  with zero plumbing changes.
- Every step is recorded (`GET /api/history`) — groundwork for the timeline.

### The architecture that makes play = agent-play
`session.py` defines `LiveGame` (a persistent session you step one action at a
time) and the **ActionSource** seam:
    HumanSource  — action from a GUI click
    RandomSource — picks any available action (the dumb agent, built now)
    AgentSource  — LATER: your planner, reading the SAME Snapshot the GUI reads
Human-play and agent-play are the identical loop with a different chooser, so
the inspector is also the agent's runtime AND its eyes.

## Endpoints
    GET  /api/snapshot           current Snapshot
    POST /api/load               static frame (demo/paste/recording)
    POST /api/config             segmentation / background
    POST /api/start_game {game}  open + reset a live session
    POST /api/action {id,x,y}    step the live session by one action
    POST /api/reset              reset the level
    POST /api/agent_step         random agent plays one action
    GET  /api/history            recorded snapshots (timeline groundwork)

## Next slices
- **3 Timeline**: scrub `/api/history`, diff between steps (watch the model
  evolve; data already recorded).
- **4 Graphs**: render `interaction_graph` / `goal_tree` (fields already in the
  Snapshot) as node-link diagrams.
- **5 Real agent + simulation**: replace RandomSource with the planner; add the
  predicted-vs-actual panel.
