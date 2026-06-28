# arc3 inspector (Slice 1)

A live, clickable view of what the perception layer actually believes about a
frame. Zero extra dependencies — pure standard-library server + one HTML page.

## Run
    python -m arc3.inspect.server
    # then open http://localhost:8000

## What you can do now
- **Load a frame**: a live game (type its id, e.g. `vc33`, → "load game";
  needs the SDK + API key), a pasted grid (JSON rows of ints 0–15), or the demo.
- **Click any object** in the grid → full attribute panel (colours, area, bbox,
  size, centroid, canonical shape, grouping, role[blank], confidence).
- **See relations** of the selected object: directional neighbours (N/S/E/W),
  alignment bands, bbox-containment.
- **Object types**: objects sharing canonical shape + primary colour are grouped
  (T0, T1, …) — the "learn once, generalize across instances" foundation.
- **Switch segmentation** (4-conn / 8-conn / colour-class) and **background**
  live, and watch the objects change.
- Toggle adjacency edges and id labels on the canvas.

## The architecture (why it will grow cleanly)
- `snapshot.py` — the **contract**: one serializable object holding EVERYTHING
  the system believes, including empty placeholder fields for every later layer
  (interaction graph, goal/action hypotheses, simulation/divergence).
- `build.py` — the ONLY place that reads the agent's real structures and
  flattens them into a Snapshot. Adding a later layer = a few lines here.
- `server.py` — stdlib http.server holding one Session; serves the page + a
  JSON snapshot API. The GUI is a **pure passive renderer** — it never computes
  model state, so it can never disagree with the real system.
- `static/index.html` — the single-page GUI. Future panels already have labelled
  placeholders ("not computed yet") that light up as you build each module.

## Growing it (the slices)
- **Slice 1 (this)**: static inspector — load a frame, click objects, see L1.
- **Slice 2**: play mode — controls + live game loop; watch L1 update per action.
- **Slice 3**: timeline — record a Snapshot per step, scrub & diff.
- **Slice 4**: graphs — render interaction graph / goal tree / DAG (the
  `interaction_graph` / `goal_tree` fields are already in the Snapshot).
- **Slice 5**: auto mode + simulation panel — predicted vs actual frame.

Each slice = add a field to the Snapshot + a panel that renders it. The GUI
core never changes.
