arc3/
├── substrate/        # L0: grid, frame, diff. Pure, deterministic.
│   ├── grid.py
│   └── delta.py
├── primitives/       # The vocabulary (Part A/B/C as TYPES, not mechanics)
│   ├── descriptive/  #   A: extractors (segmentation, measurement, topology)
│   ├── events.py     #   B1: the ~7 event types (enums/schemas)
│   ├── conditions.py #   B2: condition grammar (schemas)
│   └── goals.py      #   C2: goal-predicate types
├── model/            # L1+L2: the world-model data structures
│   ├── object.py     #   Object = bundle of primitives + role-dist + confidence
│   ├── types.py      #   Type system + instance inheritance
│   ├── graph.py      #   interaction graph (causal + constraint edges)
│   └── confidence.py #   the two-level confidence arithmetic
├── core/             # The PURE-SYMBOLIC engines (sacred — no ML here)
│   ├── simulator.py  #   #5: run model forward → predicted grid
│   ├── divergence.py #   #7: exact predicted-vs-real comparison
│   └── planner.py    #   #6: search inside the simulator
├── inference/        # The reasoning engines (hypothesis + repair)
│   ├── hypothesis.py #   #3: build/grow the graph from deltas
│   └── repair.py     #   #3: divergence → minimal model-edit (HARD CORE)
├── control/          # The decision engines (ML-leaning)
│   ├── explorer.py   #   #4: value-of-information probing
│   └── meta.py       #   #8: explore-vs-exploit (HARD CORE)
├── ml/               # Quarantined fuzzy stuff — behind clean interfaces
│   ├── role_prior.py #   the role-distribution model (stub first)
│   └── ranker.py     #   hypothesis/repair ranker
├── llm/              # The leashed proposer + offline game generator
├── harness/          # ARC-AGI-3 environment connection, action loop
└── tests/            # Mirror the structure; test the exact parts hard