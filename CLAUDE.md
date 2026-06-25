# ARC-AGI-3

Solving [ARC-AGI-3](https://arcprize.org/arc-agi/3) — a benchmark of visual reasoning puzzles presented as grid-based environments.

## Repo layout

```
arc-agi/        # scratch/exploration scripts
approaches/     # distinct solver approaches, each self-contained
  pap/          # Perception → Abstraction → Planning pipeline
```

## Running an approach

Each approach folder contains a `run.py` entry point and its own `CLAUDE.md` with details.

## Environment

The `arc_agi` package exposes an OpenAI Gym-style interface:

```python
import arc_agi
from arcengine import GameAction

arc = arc_agi.Arcade()
env = arc.make("<level_id>", render_mode="terminal")
obs, reward, done, info = env.step(GameAction.ACTION1)
```

Actions: `ACTION1`–`ACTION4` (exact semantics are unknown and must be inferred per level).
