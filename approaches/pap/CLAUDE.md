# PAP — Perception, Abstraction, Planning

See `explanations.txt` for a full description of the approach.

## Files

| File | Role |
|---|---|
| `perception.py` | Connected-component analysis; converts a raw grid into a list of `Object` instances |
| `abstraction.py` | Diffs two object lists and infers symbolic action-effect rules |
| `planner.py` | BFS/A* search over the symbolic state space toward a recognised goal |
| `run.py` | Entry point — wires the three stages together against a live `arc_agi` environment |

## Running

```bash
python approaches/pap/run.py
```

## Key data structures

- `Object` — `{id, color, cells: set[tuple[int,int]], bbox, centroid}`
- `WorldModel` — maps `action → list[SymbolicEffect]`
- `SymbolicEffect` — `{object_selector, effect_type, params}`  e.g. `{color==RED, TRANSLATE, (0, -1)}`
