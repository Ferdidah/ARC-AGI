*Organizing principle: **Descriptive** (what's true) → **Dynamic** (what happens) → **Structural** (how it wires) → **Agent-side** (how you interface). Everything is a thing to **infer by interaction**, held at the abstract→concrete zoom level your evidence supports.*

### PART A — DESCRIPTIVE primitives (what is *true* of the world)

#### A1. Substrate (the cell)

- A cell does exactly two things across frames: **stay** or **change color**.
- **Color-as-meaning** (what a color predicts): identity (which thing) · type (what kind) · state (on/off/charged) · ownership (whose) · terrain (wall/floor/hazard) · scalar (position on a scale).
- *Traps:* background = the functional pass-through color (not just the commonest); color-permutation invariance by default, **dropped** when color is scalar/ordered.

#### A2. Measurement (**NEW — the major gap Perplexity caught**)

Quantitative facts about objects and regions. These are the *substance* of most conditions and goals.

- **count** (how many objects / cells)
- **size / area** (cell count of an object)
- **extent**: width, height, **bounding box**
- **anchor**: centroid / corner / reference point
- **distance** (object-to-object, object-to-edge)
- **offset / relative vector** (B's position relative to A)
- **value** (a cell/object's position on a scalar color-scale)

#### A3. Topology & spatial relations

- adjacency · connectivity (4 vs 8) · connected regions · holes / enclosure (ring vs blob vs container) · boundary · alignment (same row/col) · containment / overlap · **symmetry** (mirror, rotation, translation).

#### A4. Objectness (how cells group into a unit)

- Grouping cues: same-color (similarity) · touching (proximity) · same-shape (stamp) · **moving-together (common fate — strongest)**.
- Object identity across frames (object permanence; the correspondence/tracking problem).
- **Canonicalization**: store shape normalized so "same object elsewhere" is recognized.

#### A5. Frame-of-reference (**NEW — Perplexity caught this**)

Almost all meaning is *relative*. The available reference frames:

- relative to the grid · to the largest/marked object · to an anchor cell · to a symmetry axis · to a reference region.
- *Why it's its own primitive:* a condition like "to the left of the key" is meaningless without a declared frame.

### PART B — DYNAMIC primitives (what the world *does*)

#### B1. Events — what can happen to a group of cells (the closed ~7)

- **Appear** · **Disappear** · **Move** · **Recolor** · **Reshape** (grow/shrink/rotate/reflect — *this absorbs Perplexity's "parameterized transforms"*) · **Split** · **Merge**.
- *Everything complex is a pattern of these* (slide = move-until-blocked; flood = recolor-spreading).

#### B2. Conditions — the grammar that gates every event (**NEW — the single biggest missing piece**)

Every rule has the form **WHEN ⟨condition⟩, IF ⟨trigger⟩, THEN ⟨event⟩**. Condition *shapes* (bounded; assembled from Parts A):

- **spatial** ("when A adjacent to B") · **state** ("when door=closed") · **count** ("when all 3 switches on") · **relational** ("when region X symmetric") · **possession** ("when avatar holds key") · **temporal** ("when it's the mover's phase").
- **Quantifiers / selection** (*Perplexity's set-ops, recategorized here*): conditions range over sets — *all* / *any* / *the largest* / *the nearest* / *exactly N*.
- *Bounded vs unbounded:* condition **shapes** are listable (catalogue offline); specific condition **instances** are infinite (**discover online via deltas**).

#### B3. Resolution / process dynamics (**NEW — from Perplexity's "until-stable"**)

How a single action's effects play out:

- **instantaneous** (one step) vs **iterated-until-stable** (slide, fall, flood, chain-reaction resolve over multiple internal steps) · **animated** (a multi-frame sequence; parse the settled end-state) · **autonomous tick** (the world advances on its own, detected via no-op).

#### B4. Interactions — one object's event caused/gated by another

- A **blocks** B's move · A **pushes** B (motion transfer) · A **consumes** B · A **toggles** B's state · A **spawns** B · A **enables** B's event under a condition (key→door).
- *Form:* every interaction = (condition involving A) → (one of the 7 events on B). Generated, not brainstormed.

### PART C — STRUCTURAL primitives (how it all *wires together*)

#### C1. The interaction graph (**your causal-graph instinct + Perplexity's dependency-graph**)

- **Nodes** = objects, carrying a *role-distribution* and *confidence*.
- **Edges** = interactions, carrying their *condition* and *confidence*.
- **Multi-resolution**: collapse a subgraph into one abstract node (global view) / expand a node into its wiring (local view). This *is* the abstract↔granular mechanism.
- Doubles as the **uncertainty ledger** (what's hypothesized vs confirmed) *and* the **dependency structure the planner walks**.

#### C2. Goal structure (goals are *trees built from goal-primitives*)

- **Goal-primitive types** (each a "make relation R hold"): **reach · match · symmetrize · cover · order/sort · collect · equalize · survive/avoid · transform-all**.
- **Composition**: the win-condition is the **root**; subgoals are **internal nodes drawn from the same goal-primitive set**; subgoals are gated by the **same conditions as mechanics** (B2).
- ⇒ **The goal tree and the interaction graph are one graph.** Goals and mechanics are the same stuff.

#### C3. Ordering & dependency (**Perplexity's event-ordering, placed correctly**)

- before/after · prerequisite chains · the gating structure **forces** an action order — and sometimes **forces interleaving** (Sussman non-serializability). The DAG *is* the ordering constraint.

#### C4. Constraints / economy (irreversibility layer)

- lives/health · action budget · carryover (early waste hurts later) · consumables (one-use keys) · **dead-ends / irreversibility** (a push that loses the level).

#### C5. Meta-structure (rules that change)

- **level-deltas** (each level *adds* a mechanic → transfer + delta-detection) · **rules-as-state** (rules are objects; transition function is part of state) · **distractors** (irrelevant by design; don't label prematurely).

### PART D — AGENT-SIDE primitives (how *you* interface and reason)

*Not part of the world-model — these are about you, the solver. Perplexity's "control" layer belongs **here**, reframed: not code you write, but how you choose to act and learn.*

#### D1. Control coupling (what your button does)

- direct (move avatar) · cursor-then-act (click → effect) · global operator (whole-board) · indirect chain (cursor→switch→door). *Discovering the indirection depth is a sub-problem.*

#### D2. The inference/planning loop (**the descriptive/operational/control distinction, realized**)

- **Descriptive inference**: segment scene → build/refine the Part-C graph from deltas.
- **Active probing** (information-greedy): pick the action that most cheaply discriminates live hypotheses (the value-of-information core).
- **Hypothesis management**: hold several ontologies in parallel; descend/retract on the abstract→concrete hierarchy; **MDL** as tiebreak; **behavior always outranks appearance.**
- **Planning**: once the graph + goal are provisional, walk the dependency DAG (ordinary search; the easy part *given* a correct model).
- **Divergence handling**: predicted ≠ actual ⇒ locate and repair the wrong node/edge/condition.
- **All engines / modules**
    
    ### A. Offline — built once, before any game
    
    | Engine | Job | Type |
    | --- | --- | --- |
    | **Primitive taxonomy** | The vocabulary/grammar the world-model is expressed in (substrate, measurement, topology, objectness, events, conditions, interactions, goals) | Symbolic resource |
    | **Abstract→concrete hierarchy** | Type lattice that lets every hypothesis be held at the zoom level evidence supports (graceful fallback on novelty) | Symbolic resource |
    | **Compatibility map** | Which mechanics *enable* vs *forbid* which goal-types — gates the goal-space the moment a mechanic is found | Symbolic resource |
    | **Synthetic game generator** | Produces many novel games (from primitive recombination) to train the ML modules; goals *derived from structure*, surface cues broken on purpose | LLM (offline, verified) |
    | **Trained specialist models** | Probe-selector, hypothesis-ranker, goal-prior — learn *prioritization* over the synthetic distribution | ML (specialized) |
    
    ### B. Online — the per-game runtime loop
    
    | # | Engine | Job | Type |
    | --- | --- | --- | --- |
    | 1 | **Perception / scene-builder** | Raw grid → typed scene graph (objects, roles, relations, measurements) | ML-leaning |
    | 2 | **Delta-interpreter** | Diff consecutive scenes → *typed* change-events ("object moved, gated by adjacency") | Hybrid (exact diff + ML classify) |
    | 3 | **Hypothesis engine** | Maintains the world-model (interaction graph + goal tree); contains the **repair logic** (divergence → minimal model-edit) and an **ML ranker** (which hypothesis/repair is most plausible) | Symbolic core, ML-ranked |
    | 4 | **Active explorer** | When uncertain, picks the action that most cheaply resolves uncertainty (value-of-information probing) | ML-leaning |
    | 5 | **Internal simulator** | Runs the current model forward — free, exact plan-testing | **Purely symbolic** |
    | 6 | **Planner** | Searches inside the simulator for an action-sequence reaching the goal (walks the dependency DAG) | Symbolic, optionally ML-guided |
    | 7 | **Executor + divergence-detector** | Runs the plan in the real game, compares each actual frame to prediction; mismatch → routes back to #3 | **Purely symbolic** |
    | 8 | **Meta-controller** | Decides explore-vs-execute, and how much budget to spend repairing vs. acting | ML-leaning |
    | + | **LLM fallback proposer** | Called *rarely* — at cold-start or impasse, when specialists have no hypothesis; proposes, never decides | LLM (online, leashed) |
    
    ### C. Shared data structures — the model itself
    
    | Structure | What it holds |
    | --- | --- |
    | **Scene graph** | Current frame as objects + attributes + relations (output of #1) |
    | **Interaction graph + goal tree** | *The world model* — nodes (objects, role-confidence), edges (interactions, conditions, confidence), goal as the root; viewable at abstract↔granular zoom. Read/written by #3, #5, #6 |
    
    ### How they interact — the cycle
    
    The runtime is one loop; each module's output feeds the next:
    
    **perceive (1) → interpret delta (2) → update model (3) → [meta-controller (8) decides] → if uncertain: probe (4); if confident: plan (6) inside the simulator (5) → execute (7) → on divergence, route back to repair (3) → repeat.**
    
    Three structural facts tie it together:
    
    - **The model (C) is the spine.** Modules 3, 5, 6 all read/write the same interaction-graph-+-goal-tree. The simulator runs it; the planner searches it; the hypothesis engine repairs it.
    - **Determinism makes two modules sacred.** The simulator (5) and divergence-detector (7) stay *purely symbolic* — they're what give you free exact plan-testing and a crisp error signal. ML never touches them.
    - **ML proposes, symbolic verifies, reality judges.** Every ML-leaning module (1, 4, 8, the ranker in 3, the LLM) only *suggests*; the symbolic core *tests the suggestion in the simulator*; the *divergence from the real game* is the final truth that corrects everything — including retraining signal for the ML.
    
    And the offline/online bridge: **A trains and equips B.** The taxonomy/hierarchy/compatibility-map give B its vocabulary and its goal-gating; the synthetic generator + specialist models give B its learned prioritization. B never learns *games* — it learns to *figure out* games, which is what transfers.
    
    The one-line version: **a symbolic world-model at the center (built in your primitive vocabulary), grown by acting; ML at the edges to prioritize the guessing; a deterministic simulator and divergence-detector to keep every guess honest.**