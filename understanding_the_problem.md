# ARC-AGI-3: Where the Core Problem Actually Lies
 
A precise statement of *what* makes ARC-AGI-3 hard, *why* standard approaches fail, and — crucially — *where in the pipeline the difficulty is concentrated*. The goal of this document is to prevent the most common mistake: misplacing the difficulty.
 
---
 
## TL;DR
 
ARC-AGI-3 is hard not because any single sub-task is impossible, but because it forces an agent to **bootstrap a world model and a goal from scratch, through interaction, efficiently, in environments engineered to defeat prior knowledge.** It lands precisely in the intersection of the blind spots of all three dominant paradigms — LLMs, reinforcement learning, and classical planning — each of which is built to *skip* exactly the step ARC-AGI-3 makes mandatory.
 
The single most important and counterintuitive fact: **the difficulty is front-loaded into perception and rule-induction, not back-loaded into search.** Once you have a correct deterministic model and a goal, solving is mostly ordinary graph search and is usually easy. Almost all the real difficulty lives in *getting a correct model in the first place*.
 
Reference baselines: humans solve ~100% of environments; frontier AI scored below ~1% as of March 2026. This is currently the only unsaturated general agentic-intelligence benchmark in the ARC series.
 
---
 
## 1. What the benchmark actually is
 
Each task is a **turn-based grid game**, not a static puzzle:
 
- The agent sees a frame: a grid up to **64×64**, each cell an integer **0–15** (16 "colors").
- The action set is **small and fixed** — typically directional moves (ACTION1–4), a general interaction (ACTION5: select/rotate/execute), a coordinate click (ACTION6), plus reset and sometimes undo. The controls are deliberately trivial so that *all* difficulty lives in the environment's logic, not in input complexity.
- There are **no instructions, no stated rules, and no stated goal.** There is no reward signal beyond the grid changing.
- The agent acts, observes the new frame, and must infer everything — mechanics, objects, and win-condition — from the visual feedback alone.
- Each game has **8–10 levels, and each successive level introduces new mechanics.** Progress is therefore a transfer problem, not a repetition.
- Scoring is **efficiency-based and per-level**: success is completing levels, with the number of actions used as the decisive measure against a human baseline. Wandering, backtracking, and brute force are explicitly penalized.
This format is the whole point. It converts "infer a static pattern" (ARC-AGI-1/2) into "learn a novel game by playing it," which requires exploration, memory, goal acquisition, world-modeling, and planning — together.
 
---
 
## 2. The core problem: five coupled sub-problems, not one
 
The fatal feature is **mutual dependence**. Success requires doing five things, each of which depends on the outputs of the others:
 
1. **Explore** to gather observations — but good exploration requires knowing what is worth probing, which requires a model.
2. **Build a world model** (the transition function) — but learning dynamics requires informative observations, which requires good exploration.
3. **Infer the goal** — but the goal can only be recognized after enough dynamics are known to know what states are reachable.
4. **Plan** a sequence to the goal — but planning requires both the model and the goal you don't yet have.
5. **Transfer knowledge across levels** — but each new level can partially invalidate the model you built, because each level adds mechanics.
This is a **chicken-and-egg cycle**. Classical planning is handed the model and goal and jumps straight to step 4. Standard RL is handed the goal (as reward) and only learns the model/policy. ARC-AGI-3 withholds *both* the model and the goal and forces simultaneous bootstrapping — under a tight action budget, in environments built to be unlike anything seen before.
 
---
 
## 3. Why each standard paradigm fails
 
ARC-AGI-3 is, by design, the intersection of three blind spots.
 
| Paradigm | What it normally skips | Why that is fatal here |
|---|---|---|
| **LLMs** | Genuine inference — they retrieve and interpolate over training coverage | Environments use procedurally novel rules with no training analog, so pattern-matching gives no advantage. LLMs also explore poorly (they favor *plausible* actions over *informative* ones), and struggle to maintain a consistent world model across hundreds of sequential steps. |
| **Reinforcement learning** | Goal inference (reward is given) and sample-efficiency (it grinds millions of episodes) | The goal is hidden, reward is sparse over long horizons, every environment is novel (no pre-training on it), and the efficiency metric forbids grinding. Random exploration cannot find precise long action sequences (e.g. one early level has a by-chance win probability of ~1 in 355). |
| **Classical planning** | Model-building and goal inference (both given as input) | Both are hidden. The planner has nothing to operate on until perception and induction have already produced a model and a goal. |
 
The empirical signature of this is stark: in the preview competition, **the top systems were not language models** — explicit graph search, systematic exploration, and state-tracking (e.g. an RL+CNN agent reaching ~12.6% in the preview) outperformed every frontier LLM. And a harness hand-tuned to known environments that scored ~97% on a *seen* environment scored ~0% on an *unseen* one — direct evidence that environment-specific engineering does not generalize, which is the entire thing being measured.
 
---
 
## 4. The difficulty is front-loaded into perception and induction — not search
 
This is the most important section, because it is the most common place people misallocate effort.
 
**Given a correct, deterministic model and a goal, ARC-AGI-3 reduces to classical single-agent planning** — finding a path in a graph — which is one of the most solved problems in computer science. On grids this small, with 4–6 actions and human solutions only tens of moves long, that step is usually *easy*.
 
The solve cost, given a correct model, is governed by only three dials:
 
- **State-space size**, which is dominated by *how many things move at once*. Pure `a→b` navigation has at most ~4,000 states (trivial). Each additional independently-moving entity *multiplies* the joint state space. Difficulty is exponential in the number of moving parts, **not** in grid size.
- **Solution depth × branching factor.** Branching is small (a gift). A 10-move solution is instant even by brute force; a long, precise, 40+-move solution over a large state space is where exhaustive search dies — which is exactly where exhaustive methods are observed to break on late levels.
- **Heuristic quality.** A good heuristic (typically from *relaxation* — solve the version with the obstacle removed or passable) makes even large spaces tractable. Moving obstacles degrade naive distance heuristics, because the true cost may include *waiting*.
**A key clarification on moving obstacles.** If an obstacle moves by a *deterministic rule* — even one coupled to the agent's own moves — the problem is still **deterministic single-agent planning**, just over a larger joint state `(agent, obstacle, …)`. It is **not** game theory. You enter adversarial search (minimax / pursuit-evasion) only if the obstacle *actively chooses moves to defeat the agent*. The diagnostic: *does the obstacle follow a fixed rule, or does it strategize against me?* The former is "bigger search"; the latter is "different, harder problem."
 
**The free-lunch property.** Because the model is deterministic, candidate plans can be **simulated forward for free** before spending any real (scored) action. Search, plan validation, and trying thousands of candidates are all free; only *execution* costs budget. The rational loop is: plan in the model, verify by simulation, execute, and **watch for divergence** — any mismatch between predicted and observed frames is a free, maximally-informative signal that the model is wrong *there*.
 
**The real caveat: the model is probable, not certain.** In practice you hold a *distribution* over object identities and mechanics, not a confirmed model. This is where pure planning becomes planning-under-uncertainty:
 
- A confident plan built on a *wrong* model is worse than no plan — it burns scarce budget marching toward a goal that isn't there.
- Therefore, prefer **robust and recoverable** plans (work across all plausible models, reversible early steps) over **brittle-optimal** ones, *when the model is uncertain*.
- When uncertainty sits on the path, prefer plans whose early actions also **resolve** that uncertainty (a probe that's on the way).
- On a *confident* model, skip all of this and plan greedily.
**Bottom line:** solving is mostly easy graph search, made interesting only by how many things move at once. The genuine difficulty almost always lives in the word *correct* — a plan is exactly as good as the model it was built on.
 
---
 
## 5. Where the hard part actually is: perception as active inference
 
Because the difficulty is front-loaded, the leverage is in building the model. The decisive insight:
 
> **Perception here is not a feedforward pass over a single frame — it is active, interactive inference where motion disambiguates structure.**
 
A static frame is genuinely *underdetermined*: the same pixels are consistent with many object decompositions, and you cannot tell them apart by looking. One action collapses the ambiguity. Concretely, the model has layers, and lower layers gate the upper ones:
 
- **Substrate (color + topology).** Color is an arbitrary symbol, not a meaning. The same value plays a different role in every game — object identity, type, on/off state, ownership, terrain, or a position on an ordered scale. Inferring *which role color plays here* (often several at once) is an early task. Default to color-permutation invariance — but drop it when the game uses color as an **ordered hierarchy or scalar**, where the absolute relationship carries meaning.
- **Object ontology (segmentation + roles).** An object is a set of cells with persistent identity across frames. Static cues (connectivity, color-class, shape-template) only propose *candidate* groupings; the reliable binder is **common fate** — cells that move together under an action are one object, regardless of color or contiguity. Object permanence (a Core Knowledge prior) makes tracking tractable: prefer "the object moved" over "it vanished and a new one appeared." The right ontology is the one under which **the dynamics have the shortest description** (an MDL / Occam criterion) — good objects are *defined* as the decomposition that makes the rules simple.
- **Roles are latent and assigned by behavioral test**, not appearance: the avatar is "what moves when I press a direction"; a wall is "what stops me"; a hazard is "what costs a life"; a goal is "the relation that became true on the frame the level ended." Goal discovery is therefore fundamentally **retrospective** — there is no signal to seek beforehand; you recognize it after a win and confirm it on the next level.
**The contamination dynamic** (the documented dominant failure): every learned rule is conditioned on the object set. If the ontology is wrong, the true rules become *unstateable*, the rule-learner sees noise, and the natural-but-fatal response is to add complexity to the *rules* rather than question the *objects*. The agent then elaborates an ever-more-wrong model and burns its budget. The antidote: **maintain several ontologies in parallel; when rules get complicated, suspect the segmentation first; let description-length adjudicate.**
 
---
 
## 6. The structural features that cause the difficulty
 
These are deliberate design choices, each closing a shortcut:
 
- **No instructions / no stated goal** → forces goal inference; removes the most common scaffold.
- **Procedural novelty** → defeats memorization and retrieval; pattern-matching gives no edge.
- **Sparse feedback** (only the grid changes) → defeats reward-driven RL and credit assignment.
- **Efficiency metric** → forecloses brute force *as a strategy*, not just as inefficiency. Careful exhaustive mapping scores far worse than a human's fast, well-chosen probes. This is the design choice that most directly forces fluid, data-efficient reasoning.
- **Per-level mechanic deltas** → forces transfer + delta-detection, not fresh re-solving.
- **Carryover constraints** (in harder variants) → couple levels so early inefficiency damages later capability, preventing levels from being treated independently.
- **Public/private split** → the public set deliberately does *not* represent all private mechanics, penalizing any vocabulary tuned only to seen primitives.
---
 
## 7. What a serious solver must contain
 
A faithful architecture has four coupled modules, mapped to where the effort should go (most of it upstream):
 
1. **Perception / abstraction** — segment raw cells into objects, attributes, and relations (a *scene graph*). Get this wrong and nothing downstream can recover.
2. **Hypothesis engine** — propose candidate dynamics *and* candidate goals, and maintain **several at once** rather than committing early.
3. **Information-greedy explorer** — choose the action that best discriminates between live hypotheses for the fewest budget points. This is *active learning / experiment design*, not reward-seeking. (A no-op is a valid, often high-value measurement: it detects autonomous dynamics.)
4. **Planner** — once a provisional model and goal exist, this is ordinary search (Section 4), re-running and revising as reality contradicts prediction.
The intelligence is in the **coupling and the revision loop** (plan → execute → detect divergence → repair model → replan), not in any one module.
 
---
 
## 8. Common misconceptions (the difficulty, misplaced)
 
- **"It's a harder puzzle."** No — it's a *different kind* of problem (interactive rule-discovery), not a harder static one.
- **"The bottleneck is search/planning."** Usually false. The bottleneck is perception and model-induction. Given a correct model, the search is typically easy.
- **"Better perception of the frame will fix it."** Frame *perception* is not the limiting factor — handcrafted harnesses prove frontier models can perceive and act fine when told the rules. The limit is inferring *unstated, novel* rules and goals.
- **"Just explore exhaustively."** The efficiency metric and combinatorial state spaces make this a losing strategy by design.
- **"Moving obstacles make it adversarial / game-theoretic."** Only if the obstacle *strategizes against you*. A deterministic rule — even coupled to your moves — is still single-agent planning over a larger state.
- **"Scale/more data will solve it."** The benchmark is built specifically to resist coverage-based scaling; novelty is the point.
- **"A harness that wins these games shows progress."** Environment-specific harnesses that win seen games and fail unseen ones measure overfitting, not generalization.
---
 
## 9. Key facts and numbers
 
- Grid: up to **64×64**, **16** colors. Turn-based (synchronous); animations may return multi-frame sequences per turn.
- Games have **8–10 levels**, each adding mechanics. Scoring is **per-level, efficiency-based**, against a human baseline.
- **Humans ≈ 100%**; **frontier AI < ~1%** as of March 2026. The human–AI gap here is larger than on ARC-AGI-1 or 2.
- In the preview, **top systems were non-LLM**; an RL+CNN agent reached ~**12.6%**. After difficulty increases (e.g. added autonomous "pushers"/sprites, lives, carryover constraints), scores collapsed further.
- A harness hand-tuned to a known environment: ~**97%** on seen, ~**0%** on unseen — the generalization gap that defines the challenge.
- One early level's by-chance win probability: **~1 in 355** — illustrating why undirected exploration fails.
---
 
## 10. The one-sentence framing
 
> ARC-AGI-3 is hard because it is engineered to be the exact place where "have a model," "have a goal," "memorize," and "search exhaustively" all fail at once — so the difficulty lives in *building a correct model and goal from interaction, efficiently*, after which the actual planning is usually easy.
 
---
 
## References and further reading
 
- ARC-AGI-3 Technical Report — *A New Challenge for Frontier Agentic Intelligence* (arXiv:2603.24621).
- ARC Prize 2025 Technical Report (arXiv:2601.10904).
- ARC-AGI-3 launch announcement and docs — `arcprize.org/blog/arc-agi-3-launch`, `docs.arcprize.org`.
- *Graph-Based Exploration for ARC-AGI-3 Interactive Reasoning Tasks* (arXiv:2512.24156).
- *Executable World Models for ARC-AGI-3 in the Era of Coding Agents* (arXiv:2605.05138).
- Background on the design philosophy: Chollet, *On the Measure of Intelligence* (2019); Core Knowledge priors (Spelke & Kinzler, 2007).
- Supporting method lineages: Go-Explore (hard-exploration); MuZero (model-based planning without given rules); active learning / optimal experiment design; program synthesis and inductive logic programming.
