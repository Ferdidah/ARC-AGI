ARC-AGI-3 Generative Grammar


A deterministic 2D grid game is a state machine: a state space, a
transition function, an initial state, and terminal states. This grammar
parameterises that state machine in a way that is (a) complete — any
deterministic 2D grid game is expressible, (b) closed — no new sections
are needed for new games, only new parameter values, and (c) learnable —
each section corresponds to something an agent must infer from observation.

The grammar has five sections because a state machine has five things:


§A — OBJECTS     What exists (the state space structure)
§B — RULES       How state changes (the transition function)
§C — CONTROL     What the player controls (the action space)
§D — GOALS       What terminal states look like (win/lose predicates)
§E — WORLD       Background constraints on the state machine itself


Variety lives in parameter values within these five sections.
New games never require new sections. Rarely require new fields.
Almost always just require new values in existing fields.




§A — OBJECTS

A0. What an object is

An object is a set of cells that change together — they share a
transition rule. The agent must segment the raw pixel grid into objects
before it can reason about rules or goals. The segmentation principles are:

Priority  Principle            When it applies
────────  ─────────────────    ──────────────────────────────────────────
1st       common-fate          Cells moving identically are one object.
                               (Definitive when motion is observed.)
2nd       synchronised-motion  Non-contiguous cells moving identically
                               are one object. (Extends common-fate to
                               objects whose parts are spatially separate.)
3rd       same-color+connected Contiguous cells of the same color are
                               one object instance.
4th       same-shape           Identical pixel patterns across positions
                               are instances of the same object type.
5th       enclosure            A ring of cells bounds a region; the ring
                               and its interior may be one object (slot,
                               container, frame).
6th       layer                When two objects occupy the same cells,
                               the higher-layer one is "on top."

These principles are not game-specific. They follow from Gestalt perception
applied to grid cells. The agent applies them in priority order.

A1. Color roles (what a color encodes)

Before segmenting objects, the agent must know what each color means.
Color is the primary information carrier in a grid game, and its meaning
is typed. A single color can carry more than one role simultaneously.

yamlcolor_roles:
  # For each color active in this game, one or more of:

  identity:       # This color IS one specific named object. Exactly one instance.
  type:           # This color marks a KIND of thing. All instances are equivalent.
  state:          # This color encodes a discrete flag that flips in place.
                  # The cell doesn't move; it recolors to signal state change.
  ownership:      # This color marks team/player membership.
  terrain:        # This color encodes a permanent floor/wall/hazard role.
  scalar:         # This color encodes a position on an ordered scale.
  relational:     # This color's meaning is only defined relative to neighbors.
                  # (e.g. "same color as adjacent cell" is the entire predicate.)
  categorical:    # A distinguishing label with no further semantic content.
                  # Used for matching without implying role.

  # A color may have multiple roles, e.g.:
  #   blue: [identity, type]   — "the avatar is the unique blue object"
  #   red:  [state, terrain]   — "red = lava (terrain) that can be extinguished (state)"

A2. Object schema

Every object is described by exactly five orthogonal dimensions.
These five are exhaustive — every property an object can have reduces to one.

yamlObjectSpec:
  id:  string    # unique label in this game-spec

  # DIMENSION 1: MOBILITY — how does this object's position change?
  mobility:
    value: fixed | player-driven | physics-driven | autonomous | rigidly-coupled | carried

    # fixed          — position never changes. Walls, terrain, markers, slots.

    # player-driven  — position changes in response to player arrow input.
    #                  Parameters:
    step_size:       N        # cells per button press (default 1)
    resolution:      immediate | animation-then-commit
    #   immediate           — lands exactly where input says
    #   animation-then-commit — slides through intermediate cells

    # physics-driven — position changes under a world force until stable.
    #                  Defined by a RuleSpec with trigger:turn-end and
    #                  resolution:iterated-until-stable. Not a separate mobility type —
    #                  this is a RuleSpec applied to a player-driven object.
    #                  (Listed here for clarity; the rule is in §B.)

    # autonomous     — position changes on the world's clock by an internal rule.
    #                  Parameters:
    pattern:         patrol-reflect | patrol-wrap | approach(target) |
                     flee(target)  | random | follow-path(path_id)
    speed:           N        # cells per player-turn

    # rigidly-coupled — always moves with its partner(s) via a fixed transform.
    #                   No exceptions; this is a property of the object, not a rule.
    #                   Parameters:
    coupled_to:      [object_id, ...]
    transform:       identity | mirror-x | mirror-y | mirror-xy |
                     rotate-90  | rotate-180 | rotate-270 | offset(dx, dy)
    gain:            integer   # 1 = same distance, -1 = reflected, 2 = double, etc.
    constraint_propagation: bool
    #   true → a blocker on one partner clips the other's reachable range

    # carried        — moves only when held by a carrier object; otherwise fixed.
    carried_by:      object_id

  # DIMENSION 2: PERSISTENCE — how long does this object exist?
  persistence:
    value: permanent | consumable | toggleable | ephemeral

    # permanent     — exists for the whole level.
    # consumable    — disappears on a trigger.
    #                 Parameters:
    consumed_by:     trigger_type   # contact | click | condition(expr)
    # toggleable    — alternates present/absent on a trigger.
    #                 Parameters:
    toggle_trigger:  contact | click | condition(expr)
    # ephemeral     — exists for N turns then disappears automatically.
    #                 Parameters:
    duration:        N

  # DIMENSION 3: SOLIDITY — how does this object interact with space?
  solidity:
    value: solid | passable | intangible | conditional

    # solid         — blocks movement; participates in collision detection.
    # passable      — walked through freely; no collision. (Floor, background.)
    # intangible    — overlappable; no collision. (Markers, fog, solved-state.)
    # conditional   — solid under some conditions, passable under others.
    #                 Parameters:
    solid_when:      GoalExpr   # predicate from §D that evaluates to bool

  # DIMENSION 4: APPEARANCE — what does it look like?
  appearance:
    display_color:   color_id         # integer 0–15 (see §A1 for what it encodes)
    shape:           pixel_mask       # the sprite's pixel array (any shape)
    size:            [w, h]           # bounding box in cells
    layer:           integer          # z-order; higher = drawn on top
    visible_when:    always | selected | proximity(R) | condition(GoalExpr)
    #   visible_when implements partial observability at the per-object level.
    #   selected    — only visible when this object is the "active" selection
    #   proximity(R)— only visible when the avatar is within R cells
    #   condition   — visible only when some predicate holds

  # DIMENSION 5: ATTRIBUTES — what mutable values does this object carry?
  attributes:
    # Any subset of the following. These are what rules test and modify.
    # Goals are predicates over these attributes.
    color_attr:      color_id         # a mutable semantic colour (may differ from display_color)
    shape_attr:      shape_id         # a mutable shape index
    rotation_attr:   0 | 90 | 180 | 270
    state_attr:      enum(values)     # arbitrary discrete state label(s)
    value_attr:      integer          # a numeric quantity (health, charge, counter)
    held:            set[object_id]   # inventory: objects this object is carrying


These five dimensions are orthogonal (none implies another) and
exhaustive (every observable property of an object in any grid game
reduces to one of these five). New games do not require new dimensions.




§B — RULES

B0. What a rule is

A rule is an atomic entry in the transition function:

when TRIGGER fires on SUBJECT acting on OBJECT,
  if CONDITION holds,
  apply EFFECT to SCOPE,
  with RESOLUTION mode,
  at PRIORITY within the turn.

The complete behavior of a game is its list of rules.
Rules are not named interactions — "Sokoban push" is a filled-in rule,
not a primitive. The primitive is the schema itself.

B1. Rule schema

yamlRuleSpec:

  # ── TRIGGER ─────────────────────────────────────────────────────────────
  # What causes this rule to fire?
  trigger:
    type:    contact | click | proximity(R) | condition(GoalExpr) |
             turn-start | turn-end | timer(N)

    #  contact         — subject and object occupy the same cell or adjacent cells
    #  click           — player sends ACTION6 (x,y); object at that cell matches filter
    #  proximity(R)    — subject enters within R cells of object
    #  condition(expr) — a GoalExpr (from §D) transitions from false to true
    #  turn-start      — fires once at the start of every turn, before player input
    #  turn-end        — fires once at the end of every turn, after player input
    #  timer(N)        — fires every N turns automatically

    subject:  object_filter   # A: the object that does the triggering
    object:   object_filter   # B: the object being triggered on
    #  object_filter = id | display_color | type | mobility_value | "any" | class(tag)

  # ── CONDITION (GUARD) ────────────────────────────────────────────────────
  # Optional: rule only fires if this is true at the moment of triggering.
  condition:
    expr:        GoalExpr    # any predicate expression from §D

  # ── ACTIVE-WHEN ──────────────────────────────────────────────────────────
  # Optional: rule only exists in the ruleset under some global condition.
  # This subsumes mode-switching, phase-gating, and level-progression.
  active_when:   GoalExpr | always
  #  e.g. active_when: state(mode_object) == mode_2
  #  In a two-mode game, some rules have active_when:mode_1, others active_when:mode_2

  # ── SCOPE ────────────────────────────────────────────────────────────────
  # Who/what does the effect apply to?
  scope:
    value: subject | object | self | neighbours(shape) | class(tag) |
           region(R) | all-of-type(filter) | chain

    #  subject              — the triggering object (A)
    #  object               — the triggered object (B)
    #  self                 — whichever object "owns" this rule
    #  neighbours(shape)    — cells in a shaped neighbourhood of the trigger point
    #                         shape: cross | 3x3 | stencil(mask) | ring(R) | custom
    #  class(tag)           — every object sharing a tag (group effect)
    #  region(R)            — every object within radius R of trigger point
    #  all-of-type(filter)  — every object matching filter anywhere on the board
    #  chain                — effect propagates recursively: each affected object
    #                         triggers this same rule on its own neighbours until blocked
    #                         (requires revert_if to be well-defined — see §B3)

  # ── EFFECTS ──────────────────────────────────────────────────────────────
  # What happens? A list — effects execute in order on the scoped objects.
  effects:
    - type: [EventType from §B2]
      # ... event-specific parameters from §B2

  # ── RESOLUTION ───────────────────────────────────────────────────────────
  # HOW the effects play out temporally.
  resolution:
    value: instantaneous | iterated-until-stable | animated | autonomous-tick

    #  instantaneous         — resolves in one logical step, immediately
    #  iterated-until-stable — repeats until a stopping condition holds
    stop_when:     blocked | stable | count(N)   # for iterated-until-stable
    #  animated              — plays a visual sequence; game state commits after
    anim_frames:   N
    anim_style:    expand | flash | fill-sweep | slide | custom
    #  autonomous-tick       — fires on the world's clock, not triggered by player
    period:        N    # every N turns (for autonomous-tick)

  # ── REVERSIBILITY ────────────────────────────────────────────────────────
  reversible:
    value: yes | no | rollback(GoalExpr)

    #  yes                     — ACTION7 (undo) reverses this effect
    #  no                      — permanent; cannot be undone
    #  rollback(condition)     — the entire move reverts if condition holds
    #                           after the effect is applied
    #  Examples:
    #    rollback(scope==chain AND chain-hit-wall) — Sokoban push revert
    #    rollback(subject.position==void)          — falling-off-edge revert with penalty

  # ── PRIORITY ─────────────────────────────────────────────────────────────
  # When multiple rules fire in the same turn, this determines order.
  priority:
    phase:   input | pre-input | post-input | win-check | lose-check
    #  pre-input   — fires before player action is processed (e.g. autonomous moves)
    #  input       — fires as part of processing player action (movement, interaction)
    #  post-input  — fires after player action (e.g. gravity settle, chain effects)
    #  win-check   — fires to test terminal conditions (after all other phases)
    #  lose-check  — fires to test failure conditions (after all other phases)
    order:   integer  # tiebreak within phase; lower = fires first

B2. Event types (the closed set of things that can happen)

There are 8 event types. This set is closed.
Any effect in any grid game is one of these, possibly composed in sequence.

yamlEventType:

  move:
    # Object translates to a new grid position.
    delta:     (dx,dy) | direction-of-travel | toward(object_id) |
               away-from(object_id) | random-direction
    distance:  N | until-blocked | until-stable(force_dir)
    revert_if: blocked | out-of-bounds | chain-blocked | condition(GoalExpr)
    # revert_if causes the whole move (and any chain) to be undone if condition
    # holds after the move. Essential for Sokoban-style mechanics.

  recolor:
    # Object changes a color attribute in place. Position unchanged.
    target:    color_attr | display_color | both
    to:        color_id | cycle-next(ring) | cycle-prev(ring) | match(object_id) |
               set-by-rule(GoalExpr)

  reshape:
    # Object's shape, size, or orientation changes in place. Position unchanged.
    op:        grow(direction, N) | shrink(direction, N) |
               rotate(90 | 180 | 270) | reflect(x | y | diagonal) |
               scale(factor) | set-shape(shape_id) | cycle-shape(ring)

  appear:
    # Object comes into existence at a location.
    location:  (x,y) | at(object_id) | offset(object_id, dx, dy) | random

  disappear:
    # Object is removed from the board.
    # No parameters — the object simply ceases to exist.

  set-attr:
    # Object's attribute(s) change. The object itself does not move.
    attr:      state_attr | value_attr | held | rotation_attr | shape_attr
    op:        set(value) | increment(N) | decrement(N) | toggle |
               cycle-next(ring) | add-item(id) | remove-item(id)

  split:
    # One object becomes two objects at adjacent positions.
    axis:      horizontal | vertical | diagonal
    policy:    equal | proportion(p) | by-attribute(attr)

  merge:
    # Two objects become one object.
    result:    union-shape | intersection-shape | sum-value | replace(id)


Note on composition: a single rule can have multiple effects (§B1 effects
is a list). Effects execute in order. This handles "blast → push → recheck"
sequences. No separate "composite event" type is needed.



B3. The chain scope constraint

When scope: chain is used, the rule must have:


effect.type: move with a well-defined delta
effect.revert_if defined (otherwise chain is unbounded and the game is ill-formed)


Chain resolution: the effect fires on scope, then each affected object triggers
the same rule on its own neighbours in the same direction, recursively.
If any step in the chain hits a revert_if condition, the entire chain reverts.


§C — CONTROL

C0. What control is

Control maps player input (button presses, clicks) to rule triggers.
A game may have multiple control schemes active simultaneously
(e.g. arrows drive avatar, clicks drive a cursor).

yamlControlSpec:
  available_actions: list[1|2|3|4|5|6|7|RESET]
  #  Explicitly states which action IDs exist in this game.
  #  The agent must not waste exploration budget on unavailable actions.
  #  Default: [1,2,3,4,5,6,7,RESET] (all available)

  schemes: list[SchemeSpec]

SchemeSpec:
  actor:          object_filter   # which object this scheme controls

  arrow_input:    # optional — present if arrows do something
    maps_to:      translate(actor) | select-from(set) | global-transform
    #  translate(actor)  — arrows move the actor object directly
    #    step_size:      N     (cells per press; default 1)
    #    resolution:     immediate | animation-then-commit | physics-settled
    #      physics-settled: input fires a nudge; then gravity/force settles position
    #  select-from(set)  — arrows cycle through a set of selectable objects
    #  global-transform  — arrows transform the whole board (rotate, shift, flip)

  click_input:    # optional — present if ACTION6 does something
    maps_to:      act-on-cell | select-object | cycle-attr | pick-place | free-draw
    #  act-on-cell    — click triggers a rule at cell (x,y)
    #  select-object  — click makes the clicked object "active"
    #                   (subsequent arrows then move the active object)
    #  cycle-attr     — click cycles the clicked object's attribute
    #  pick-place     — first click picks up; second click places
    #  free-draw      — click + drag recolors cells (painting game)

  action5_input:  # optional — what ACTION5 (space/interact) does
    maps_to:      rotate-active | confirm | mode-switch | custom-rule(rule_id)

  coupling:       # optional — this scheme drives multiple objects
    type:         none | mirror-x | mirror-y | mirror-xy |
                  identity | offset(dx,dy) | rotate-90
    partners:     list[object_filter]
    constraint_propagation: bool

  mode_system:    # optional — input can switch between rule-subsets
    n_modes:      N
    switch_trigger: click | action5 | condition(GoalExpr) | automatic(N_turns)
    indicator:    object_filter   # whose appearance signals current mode
    reversible:   bool
    # Modes are implemented via active_when fields on RuleSpecs (§B1).
    # The mode_system here declares the switching mechanism.


§D — GOALS AND PREDICATES

D1. What a predicate is

A predicate is a function from game-state to bool.
Goals are predicates. Rule conditions are predicates. They share the same grammar.

Predicates are built from atomic relations (listed below)
composed with logical combinators (also listed below).
This set is derived from what grid geometry and object attributes
can express — it is not derived from observed games.

D2. Atomic relations (the closed predicate vocabulary)

── POSITIONAL (where things are) ────────────────────────────────────────────

  at(obj, cell)                    obj occupies specific grid cell (x,y)
  adjacent(a, b [, dir])           a and b are grid-neighbours
                                   dir ∈ {N, S, E, W, NE, NW, SE, SW} optional
  coincident(a, b)                 a and b occupy exactly the same cell(s)
  inside(outer, inner)             inner's bounding box is contained in outer's
  inset(outer, inner, N)           inner is inside outer with uniform border of N
  above(a,b) / below / left / right  directional relative position
  aligned(a, b, axis)              same row (axis=H) or same column (axis=V)
  distance(a, b, metric) OP N      distance test; metric ∈ {manhattan, euclidean}

── TOPOLOGICAL (how the grid is connected) ──────────────────────────────────

  connected(set, connectivity)     cells form one connected component
                                   connectivity ∈ {4-neighbor, 8-neighbor}
  enclosed(region, boundary)       region is fully surrounded by boundary cells
  path-exists(a, b [, passable])   a can reach b through passable cells

── ATTRIBUTE (what values objects have) ─────────────────────────────────────

  equal(x, y)                      x == y  (any two values: positions, colors, integers)
  same(attr, a, b)                 a.attr == b.attr
  differ(attr, a, b)               a.attr ≠ b.attr
  value(obj, attr) OP N            numeric comparison (>, <, ==, ≥, ≤)
  state(obj, attr) == S            discrete state test
  holds(obj, item_id)              obj has item_id in its `held` set

── AGGREGATE (over sets of objects or cells) ─────────────────────────────────

  count(set [, filter]) OP N       cardinality, optionally filtered by predicate
  all-same(attr, set)              all objects in set share one attribute value
  any-differ(attr, set)            at least two objects in set differ on attribute
  occupied(cell)                   any solid object is present at cell
  empty(cell)                      no solid object is present at cell

── STRUCTURAL (shape/symmetry of regions) ────────────────────────────────────

  symmetric(region, axis)          region has mirror symmetry on given axis
                                   axis ∈ {horizontal, vertical, diagonal, rotational}
  matches-template(region, ref)    every cell in region equals the reference value
  sorted(set, attr, order)         objects in set are ordered by attr
                                   order ∈ {ascending, descending}

D3. Combinators (closed — derived from propositional + first-order logic)

PROPOSITIONAL:
  AND(p, q)           both p and q
  OR(p, q)            at least one of p, q
  NOT(p)              negation
  IMPLIES(p, q)       if p then q  (equivalent to OR(NOT(p), q))
  XOR(p, q)           exactly one of p, q

QUANTIFIERS (over sets of objects):
  FORALL x∈S: P(x)          all objects in S satisfy P
  EXISTS x∈S: P(x)          some object in S satisfies P
  EXACTLY-N x∈S: P(x)       exactly N objects in S satisfy P
  AT-LEAST-N x∈S: P(x)      at least N objects in S satisfy P
  THE-UNIQUE x∈S: P(x)      the unique object satisfying P (ill-formed if 0 or 2+)
  ARGMIN x∈S: f(x)          object minimising f (e.g. nearest, lowest)
  ARGMAX x∈S: f(x)          object maximising f

MAPPING (over correspondences between two sets):
  BIJECTIVE(f, A, B)         f is a 1-to-1 onto map from A to B
  INJECTIVE(f, A, B)         f maps every a∈A to a distinct b∈B
  SURJECTIVE(f, A, B)        every b∈B is covered by some a∈A


This combinator set is derived from standard logic, not from games.
It does not grow. Any predicate expressible in first-order logic over
the atomic relations above is expressible with these combinators.



D4. Goal specification

yamlGoalSpec:
  win_condition:    GoalExpr    # the board-state predicate that, when true, wins

  progress_signal:  GoalExpr    # optional; evaluates to a value in [0,1]
  #  Represents partial completion. The planning agent uses this as a heuristic.
  #  e.g. count(satisfied_slots) / count(total_slots)
  #  Not used for win/lose logic — only for search guidance.

  composition:
    quantifier:   single | all | any | exactly-N
    #  single    — one specific condition must hold
    #  all       — all of a set of sub-conditions must hold (most common)
    #  any       — at least one of a set of sub-conditions must hold
    #  exactly-N — exactly N of a set of sub-conditions must hold

    ordering:     independent | ordered | interleaved
    #  independent  — subgoals can be achieved in any order
    #  ordered      — subgoal G2 must be achieved strictly before G1 is reachable
    #                 (the key must exist before the door can open)
    #  interleaved  — optimal order depends on current state (Sussman anomaly)
    #                 The agent cannot pre-commit to a subgoal order.

    coupling:     none | shared-resource | constraint-propagation | conservation
    #  none                   — subgoals are independent
    #  shared-resource        — solving one subgoal uses something another needs
    #                           (one key, two doors — the key choice matters)
    #  constraint-propagation — solving one subgoal constrains what's possible
    #                           for another without consuming a resource
    #  conservation           — a quantity is conserved; the puzzle is its
    #                           distribution across containers

    gating: list[{guard: GoalExpr, unlocks: GoalExpr}]
    #  Subgoal `unlocks` is only reachable after `guard` holds.
    #  Gating is the primary source of plan ordering in grid games.
    #  Multiple gating relations can form a dependency DAG.

D5. Failure specification

yamlFailureSpec:
  conditions: list[FailureCondition]   # any of these → game over (loss)

FailureCondition:
  type:    predicate | budget | timer

  predicate:    # lose when some board-state holds
    expr:       GoalExpr
    result:     lose-level | lose-life(then: respawn | game-over)

  budget:       # lose when a step counter exhausts
    total:      N
    refillable: bool              # can collectibles restore it?
    penalty:    N_steps           # steps lost per specific bad action
    display:    object_filter     # the resource-meter object on the board

  timer:        # lose after N turns regardless of state
    turns:      N


§E — WORLD

E0. What the world is

The world specifies constraints that apply globally to the state machine —
not to individual objects or rules, but to the grid itself and how it behaves.

yamlWorldSpec:
  grid:
    size:         [W, H]          # width × height in cells; W,H ∈ [1,64]
    background:   color_id        # color of cells with no object
    topology:
      wrap_x:     bool            # grid wraps horizontally (toroidal in x)
      wrap_y:     bool            # grid wraps vertically (toroidal in y)
      #  wrap_x = wrap_y = true → torus topology
      #  wrap_x = wrap_y = false → bounded rectangle (most common)

  physics:
    # Global forces that act on objects every turn.
    # Each force is implemented as a RuleSpec with trigger:turn-end
    # and resolution:iterated-until-stable, but declared here for clarity.
    forces: list[ForceSpec]

  ForceSpec:
    direction:    N | S | E | W   # direction of the force
    magnitude:    N               # cells per tick (usually 1)
    affected:     object_filter   # which objects this force acts on
    flippable:    bool            # can a rule reverse this force direction?
    flip_trigger: object_filter   # the object whose activation flips it

  observability:
    type:         full | spatial-fog | attribute-mask | multi-layer

    # full          — agent sees the complete board state every frame

    # spatial-fog   — cells beyond radius R of the avatar are hidden
    fog_radius:     R
    fog_color:      color_id      # what hidden cells look like

    # attribute-mask — a specific attribute of non-selected objects is hidden
    masked_attr:    color_attr | shape_attr | state_attr | held
    revealed_when:  selected | proximity(R) | condition(GoalExpr)

    # multi-layer   — different objects are visible under different conditions
    #                 (implemented via ObjectSpec.visible_when fields)

  undo:
    available:    bool            # is ACTION7 (undo) available?
    scope:        last-move | full-history
    #  last-move  — only the most recent action can be undone (most common)
    #  full-history — any prior state can be restored

  turn_structure:
    # Declares the phases within a single turn and their order.
    # Rules with priority.phase fields fire in this order.
    phases: [pre-input, input, post-input, win-check, lose-check]
    #  pre-input   — autonomous moves, timers, forces fire here
    #  input       — player action and its immediate effects fire here
    #  post-input  — chained effects, gravity settle, state checks fire here
    #  win-check   — win predicates evaluated here
    #  lose-check  — fail predicates evaluated here
    # New phases can be inserted if needed; the names above are the defaults.


§F — COMPATIBILITY CONSTRAINTS

The schemas above define what is expressible. This section defines what
is plausible — what combinations actually occur in well-formed games.
This section grows as games are observed. The schemas above do not grow.

F1. Mechanic → Goal enablement

# A goal type requires certain mechanics to be achievable.
# Format: mechanic  →  enables  goal_pattern

rule.move + goal.reach                           → trivially achievable
rule.move(scope:chain, revert_if:chain-blocked)  → enables register/arrange
rule.set-attr(op:cycle) + trigger:contact        → enables attribute-key
rule.coincident-check                            → enables pair-up / mate-ports
rule.recolor(scope:region) + trigger:contact     → enables match-pattern
world.physics.force + rule.toggle-solid          → enables reach-via-fall
control.click(cycle-attr) + obj.constraint-clue  → enables satisfy-csp
rule.adjust-quantity(conserved)                  → enables equalize/conservation
control.coupling(mirror) + rule.move             → enables pair-up / reach

F2. Co-occurrence (observed in decoded games — becomes sampling weights)

# Format: A  WITH  B  [game source(s)]

control.coupling              WITH  world.turn.constraint-propagation
failure.budget                WITH  obj.resource-meter-display
world.physics.force           WITH  obj.hazard + obj.goal
world.undo                    WITH  failure.contact-hazard
control.click(cycle-attr)     WITH  obj.constraint-clue
control.select-active         WITH  world.attribute-mask
rule.move(scope:chain)        WITH  rule.move(revert_if:blocked)
failure.budget.penalty        WITH  rule.move(revert_if:void)
goal.ordering(ordered)        WITH  rule.active_when(condition)
goal.coupling(conservation)   WITH  rule.adjust-quantity(conserved:true)

F3. Implausible or forbidden combinations

world.physics.force(dir:down) + control.coupling(mirror-y)
  → IMPLAUSIBLE: gravity + vertical mirror gives contradictory y-motion

rule.scope(chain) WITHOUT rule.effect.move.revert_if
  → ILL-FORMED: chain without revert is unbounded; never well-defined

goal.ordering(ordered) + goal.coupling(none)
  → CONTRADICTION: ordered subgoals must be coupled by gating

control.click(cycle-attr) + goal.reach
  → LOW-PRIOR: CSP-click control rarely pairs with navigation goals

failure.budget(refillable) + failure.budget(penalty)
  → LOW-PRIOR: rarely both; choose one budget sub-mechanic

F4. Parameter ranges (observed bounds; expand with evidence only)

yamlgrid:             {W: [10,64], H: [10,64]}
colors_active:    [2, 12]       # distinct color roles in one game

objects:
  total:          [2, 50]
  avatars:        [1, 4]
  autonomous:     [0, 10]
  slots:          [0, 20]       # register / pair-up type goals
  clue_objects:   [0, 40]       # CSP type goals

rules_per_game:   [1, 15]
effects_per_rule: [1, 4]
goal_conjuncts:   [1, 20]       # conjuncts in win predicate
solution_depth:   [3, 500]      # steps in shortest solution

control:
  step_size:      [1, 6]
  n_modes:        [2, 4]
  coupling_n:     [2, 6]

failure:
  budget:         [50, 1024]
  penalty:        [0, 30]
  lives:          [1, 5]

F5. Level-delta grammar

# What changes between levels in a sequence.
# Format: game → delta-type{specifics}

DELTA TYPES (closed):
  SCALE-UP{x}          — more instances; larger grid; longer solution
  NEW-MECHANIC{x}      — add a RuleSpec absent from L1
  NEW-CONSTRAINT{x}    — tighten budget; add hazard; add fog; add mode
  HARDER-PARAMS{x}     — more slots/clues; tighter palette; less budget slack
  REVEAL-COMPLEXITY{x} — fog or attribute-mask introduced in later level only
