# PAP (Perception-Abstraction-Planning)

Symbolic, non-neural approach. Goal: interpretability and sample-efficiency,
not raw performance.

## Pipeline
1. `perception.py` — connected components, object detection on grid
2. `abstraction.py` — diff between state before/after action, rule hypotheses
3. `planner.py` — search (BFS/A*) toward identified goal state

## Principles
- No ML/neural networks in this folder — the whole point is interpretability
- Prefer explicit rule templates over free-form pattern recognition
- Status/progress: see README.md in this folder
