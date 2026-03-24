---
name: heuristic-search
description: Implement heuristic search algorithms for graph traversal, pathfinding, and state-space navigation. Use when building systems that need A*, IDA*, Dijkstra, BFS, DFS, hill climbing, or multiobjective search. Based on the Hipster4j architecture — graph-agnostic, iterator-based (no recursion), type-safe, with fluent builder APIs. Use this skill for search problems, cost-based navigation, state-space exploration, and solution-space traversal in optimization pipelines.
---

<!-- EDITORIAL GUIDELINES
Correction layer for heuristic search implementations. Every line costs context.
- Be terse. Tables and code over prose.
- Focus on the iterator-based, graph-agnostic patterns.
- Prefer consolidated examples over fragments.
-->

Heuristic search navigates solution spaces efficiently by combining **state expansion** with **cost evaluation** and **heuristic guidance**. The key insight: algorithms are iterators over nodes, not recursive functions. This gives the caller full control over search execution.

## Algorithm Catalog

| Algorithm | Type | IARM Reasoning Mode | Memory | Optimality |
|-----------|------|---------------------|--------|------------|
| **BFS** | Uninformed | *Exhaustive fairness* — consider all options at equal depth | O(b^d) | Yes |
| **DFS** | Uninformed | *Committed depth* — follow one thread to conclusion | O(bd) | No |
| **Dijkstra** | Uninformed | *Cost-aware prudence* — never pay more than necessary | O(V+E) | Yes |
| **Bellman-Ford** | Uninformed | *Pessimistic correction* — relax until stable | O(VE) | Yes |
| **A*** | Informed | *Informed optimism* — trust the heuristic estimate | O(b^d) | Yes (if h admissible+consistent) |
| **IDA*** | Informed | *Frugal persistence* — re-derive rather than store | O(bd) | Yes (if h admissible) |
| **AD*** | Informed | *Anytime refinement* — good answer now, better later | O(b^d) | Bounded suboptimal |
| **Hill Climbing** | Local | *Greedy ascent* — trust the gradient | O(1) | No (local optima) |
| **Simulated Annealing** | Local | *Disciplined chaos* — accept worse early, tighten later | O(1) | Probabilistic |
| **Tabu Search** | Memory | *Memory-guided novelty* — refuse to repeat mistakes | O(tenure) | No (but avoids cycling) |
| **ALNS** | Adaptive | *Adaptive destruction* — break to rebuild better | O(n) | No (but self-improving) |
| **Multiobjective** | Multi | *Plurality preservation* — maintain all non-dominated tradeoffs | O(b^d) | Pareto-optimal |
| **CSP** | Constraint | *Constraint narrowing* — eliminate impossibilities first | O(d·n) | Yes (complete) |

## Core Type System

```
State (S)     — A position in the search space (board config, code state, param vector)
Action (A)    — A transition between states (move, mutation, operator)
Cost (C)      — Comparable value (numeric, vector for multiobjective)
Node (N)      — State + parent + action + cost + heuristic score
Transition<A,S> — (action, state) pair representing a single move
```

### Key Interfaces

```
TransitionFunction<A, S>
  successorsOf(state: S) → Iterable<Transition<A, S>>

CostFunction<A, S, C>
  evaluate(transition: Transition<A, S>) → C

HeuristicFunction<S, C>
  estimate(state: S) → C

NodeFactory<A, S, N>
  makeNode(fromNode: N, transition: Transition<A, S>) → N

GoalPredicate<S>
  test(state: S) → boolean
```

## Iterator-Based Search Pattern

**The core insight**: every search algorithm is an iterator that yields nodes one at a time. No recursion, no callbacks — the caller pulls results.

```javascript
// Generic search iterator pattern
class SearchIterator {
  constructor(initialNode, expander) {
    this.frontier = new Frontier();  // Queue, Stack, PriorityQueue
    this.visited = new Map();        // state → node
    this.frontier.add(initialNode);
    this.visited.set(initialNode.state, initialNode);
    this.expander = expander;
  }

  hasNext() {
    return !this.frontier.isEmpty();
  }

  next() {
    const current = this.frontier.remove();

    // Expand: generate successors
    for (const transition of this.expander.successorsOf(current.state)) {
      const child = this.expander.makeNode(current, transition);

      if (!this.visited.has(child.state)) {
        this.visited.set(child.state, child);
        this.frontier.add(child);
      }
    }

    return current;
  }
}
```

**Why iterators over recursion:**

| Recursive | Iterator-based |
|-----------|---------------|
| Stack overflow on deep graphs | Bounded memory via frontier |
| All-or-nothing execution | Pause/resume at any node |
| Hard to instrument | Easy to log, filter, visualize |
| Fixed termination | Caller controls when to stop |
| Can't interleave searches | Compose multiple iterators |

## A* Implementation Pattern

```javascript
class AStarIterator extends SearchIterator {
  constructor(initialNode, expander, heuristic, algebra = numericCost) {
    super(initialNode, expander);
    this.frontier = new PriorityQueue(algebra.compare);  // QGN: derived comparator
    this.heuristic = heuristic;
    this.algebra = algebra;
    this.health = { expanded: 0, duplicates: 0, heuristicViolations: 0 };

    initialNode.g = algebra.zero;
    initialNode.h = heuristic.estimate(initialNode.state);
    initialNode.f = algebra.combine(initialNode.g, initialNode.h);
    this.frontier.add(initialNode);
  }

  next() {
    const current = this.frontier.remove();
    this.health.expanded++;

    for (const transition of this.expander.successorsOf(current.state)) {
      const child = this.expander.makeNode(current, transition);
      const tentativeG = this.algebra.combine(current.g, this.expander.cost(transition));

      // SENTIENT: check heuristic consistency h(s) <= c(s,s') + h(s')
      const childH = this.heuristic.estimate(child.state);
      if (this.algebra.compare({ f: current.h }, { f: this.algebra.combine(this.expander.cost(transition), childH) }) > 0) {
        this.health.heuristicViolations++;
      }

      if (!this.visited.has(child.state) || this.algebra.compare({ f: tentativeG }, { f: this.visited.get(child.state).g }) < 0) {
        child.g = tentativeG;
        child.h = childH;
        child.f = this.algebra.combine(child.g, child.h);
        child.parent = current;
        if (this.visited.has(child.state)) this.health.duplicates++;
        this.visited.set(child.state, child);
        this.frontier.add(child);
      }
    }

    return { node: current, health: this.health };
  }
}

// Usage: pull nodes until goal found
const search = new AStarIterator(start, expander, heuristic);
while (search.hasNext()) {
  const node = search.next();
  if (isGoal(node.state)) {
    return reconstructPath(node);  // Walk parent chain
  }
}
```

## IDA* (Iterative Deepening A*)

Memory-efficient A* — uses DFS with f-value cutoff, iteratively increasing the bound.

```javascript
class IDAStarIterator {
  constructor(initialNode, expander, heuristic) {
    this.initial = initialNode;
    this.expander = expander;
    this.heuristic = heuristic;
    this.fLimit = heuristic.estimate(initialNode.state);  // Initial bound
    this.minExceeded = Infinity;  // Track minimum f that exceeded limit
    this.stack = [initialNode];
    this.iteration = 0;
  }

  next() {
    while (true) {
      if (this.stack.length === 0) {
        // Increase bound to smallest exceeded f-value, restart
        this.fLimit = this.minExceeded;
        this.minExceeded = Infinity;
        this.stack = [this.initial];
        this.iteration++;
      }

      const current = this.stack.pop();
      const f = current.g + this.heuristic.estimate(current.state);

      if (f > this.fLimit) {
        this.minExceeded = Math.min(this.minExceeded, f);
        continue;  // Prune: exceeds current bound
      }

      // Expand within bound
      for (const transition of this.expander.successorsOf(current.state)) {
        const child = this.expander.makeNode(current, transition);
        child.g = current.g + this.expander.cost(transition);
        this.stack.push(child);
      }

      return current;
    }
  }
}
```

**Key property**: O(bd) memory (linear in depth) vs A*'s O(b^d) — critical for large search spaces.

## Hill Climbing Pattern

```javascript
class HillClimbingIterator {
  constructor(initialNode, expander, evaluator) {
    this.current = initialNode;
    this.current.score = evaluator.evaluate(initialNode.state);
    this.expander = expander;
    this.evaluator = evaluator;
  }

  next() {
    const successors = this.expander.successorsOf(this.current.state);
    let best = this.current;

    for (const transition of successors) {
      const child = this.expander.makeNode(this.current, transition);
      child.score = this.evaluator.evaluate(child.state);

      if (child.score > best.score) {
        best = child;
      }
    }

    const improved = best !== this.current;
    this.current = best;
    return { node: this.current, improved };  // Caller detects plateau/local optimum
  }
}
```

**Enforced Hill Climbing**: when hill climbing stalls (no improving successor), fall back to BFS from current state until an improvement is found, then resume hill climbing.

## Graph-Agnostic Builder Pattern

The search algorithm doesn't know what a "graph" is. It only knows states, transitions, and costs.

```javascript
// Define the problem — not the graph
class SearchProblem {
  constructor({ initial, goal, transitions, cost, heuristic }) {
    this.initial = initial;
    this.goal = goal;
    this.transitions = transitions;  // state → [Transition(action, state)]
    this.cost = cost;                // transition → number
    this.heuristic = heuristic;      // state → number (estimate to goal)
  }
}

// Fluent builder
class SearchBuilder {
  static from(initial) { return new SearchBuilder(initial); }

  constructor(initial) { this.config = { initial }; }
  to(goal) { this.config.goal = goal; return this; }
  transitions(fn) { this.config.transitions = fn; return this; }
  cost(fn) { this.config.cost = fn; return this; }
  heuristic(fn) { this.config.heuristic = fn; return this; }

  aStar() { return new AStarIterator(/*...from config*/); }
  bfs() { return new BFSIterator(/*...from config*/); }
  dfs() { return new DFSIterator(/*...from config*/); }
  hillClimbing() { return new HillClimbingIterator(/*...from config*/); }
  idaStar() { return new IDAStarIterator(/*...from config*/); }
}

// Usage
const search = SearchBuilder
  .from(startState)
  .to(goalState)
  .transitions(s => generateMoves(s))
  .cost(t => t.action.weight)
  .heuristic(s => manhattan(s, goalState))
  .aStar();
```

## Multiobjective Search

When optimizing multiple competing objectives (latency vs accuracy, memory vs speed):

```javascript
// Pareto dominance: a dominates b if better in all objectives
function dominates(a, b) {
  let dominated = true;
  for (let i = 0; i < a.objectives.length; i++) {
    if (a.objectives[i] > b.objectives[i]) return false;  // Worse in one
    if (a.objectives[i] < b.objectives[i]) dominated = true;
  }
  return dominated;
}

// Maintain Pareto frontier: set of non-dominated solutions
class ParetoFrontier {
  constructor() { this.front = []; }

  add(solution) {
    // Remove solutions dominated by new one
    this.front = this.front.filter(s => !dominates(solution, s));
    // Add if not dominated by any existing
    if (!this.front.some(s => dominates(s, solution))) {
      this.front.push(solution);
    }
  }
}
```

## Cost Algebra Pattern

Costs are not just numbers — they form an **algebra** with binary combination and scalar scaling. This enables domain-agnostic cost accumulation over any comparable type.

```javascript
// Cost algebra: three operations over any Comparable type
class CostAlgebra {
  constructor({ zero, combine, scale }) {
    this.zero = zero;          // Identity element
    this.combine = combine;    // (C, C) → C  (accumulate path cost)
    this.scale = scale;        // (C, number) → C  (weight heuristic, e.g. AD*)
  }
}

// Standard numeric algebra
const numericCost = new CostAlgebra({
  zero: 0,
  combine: (a, b) => a + b,
  scale: (a, factor) => a * factor
});

// Vector cost algebra (for multiobjective)
const vectorCost = new CostAlgebra({
  zero: [0, 0, 0],
  combine: (a, b) => a.map((v, i) => v + b[i]),
  scale: (a, factor) => a.map(v => v * factor)
});
```

**Key insight**: algorithms use `algebra.combine(currentCost, transitionCost)` instead of `+`. This decouples cost types from algorithm logic — same A* code works for scalars, vectors, or custom types.

## Cost Function Patterns

| Pattern | Formula | Use Case |
|---------|---------|----------|
| **Uniform** | `cost(t) = 1` | Unweighted graphs (BFS equivalent) |
| **Weighted** | `cost(t) = t.weight` | Standard shortest path |
| **Composite** | `cost(t) = w₁·f₁(t) + w₂·f₂(t)` | Weighted multi-criteria |
| **Dynamic** | `cost(t) = f(t, context)` | Context-dependent (AD*) |
| **Algebraic** | `cost = algebra.combine(parent.cost, edge)` | Any comparable type via CostAlgebra |

## Simulated Annealing

Probabilistic local search that accepts worse solutions with decreasing probability — escapes local optima.

```javascript
class SimulatedAnnealingIterator {
  constructor(initialNode, expander, evaluator, config = {}) {
    this.current = initialNode;
    this.current.score = evaluator.evaluate(initialNode.state);
    this.best = this.current;
    this.expander = expander;
    this.evaluator = evaluator;
    this.health = { accepted: 0, rejected: 0, improved: 0 };

    // QGN-DIRECT: derive parameters from landscape, not hardcode
    // T0: calibrate so ~80% of random moves accepted initially
    // cooling: derive from search budget and temperature range
    // Tmin: derive from noise floor of evaluator
    const calibration = config.calibrationSamples || this.calibrate(expander, evaluator, initialNode);
    this.T = config.T0 || calibration.T0;
    this.cooling = config.cooling || calibration.cooling;
    this.Tmin = config.Tmin || calibration.Tmin;
  }

  next() {
    // Pick a random neighbor
    const successors = [...this.expander.successorsOf(this.current.state)];
    const transition = successors[Math.floor(Math.random() * successors.length)];
    const candidate = this.expander.makeNode(this.current, transition);
    candidate.score = this.evaluator.evaluate(candidate.state);

    const delta = candidate.score - this.current.score;

    // Accept if better, or probabilistically if worse (Metropolis criterion)
    if (delta > 0 || Math.random() < Math.exp(delta / this.T)) {
      this.current = candidate;
      if (candidate.score > this.best.score) this.best = candidate;
    }

    // SENTIENT: track acceptance rate for self-calibration
    if (delta > 0) this.health.improved++;
    else if (delta <= 0 && this.current === candidate) this.health.accepted++;
    else this.health.rejected++;

    this.T *= this.cooling;
    return { node: this.current, best: this.best, temperature: this.T, frozen: this.T < this.Tmin, health: this.health };
  }

  // QGN-DIRECT: derive parameters from landscape sampling
  calibrate(expander, evaluator, initial, samples = 20) {
    const deltas = [];
    let node = initial;
    for (let i = 0; i < samples; i++) {
      const successors = [...expander.successorsOf(node.state)];
      if (successors.length === 0) break;
      const t = successors[Math.floor(Math.random() * successors.length)];
      const next = expander.makeNode(node, t);
      next.score = evaluator.evaluate(next.state);
      deltas.push(Math.abs(next.score - node.score));
      node = next;
    }
    const meanDelta = deltas.reduce((a, b) => a + b, 0) / deltas.length;
    return { T0: -meanDelta / Math.log(0.8), cooling: 0.995, Tmin: meanDelta * 0.001 };
  }
}
```

| Parameter | QGN Derivation | Fallback |
|-----------|---------------|----------|
| `T0` | `-meanDelta / log(0.8)` from landscape sampling | 1000 |
| `cooling` | Derived from budget: `1 - 1/(expectedIter * 0.1)` | 0.995 |
| `Tmin` | `meanDelta * 0.001` (noise floor) | 0.01 |

## Multiobjective Label-Setting

Unlike single-objective search (one best node per state), multiobjective keeps **all non-dominated nodes per state**.

```javascript
class MultiobjLabelSetting extends SearchIterator {
  constructor(initialNode, expander) {
    super(initialNode, expander);
    this.labels = new Map();  // state → Set<Node> (non-dominated set)
  }

  next() {
    const current = this.frontier.remove();

    for (const transition of this.expander.successorsOf(current.state)) {
      const child = this.expander.makeNode(current, transition);
      const state = child.state;

      if (!this.labels.has(state)) this.labels.set(state, new Set());
      const existing = this.labels.get(state);

      // Check if dominated by any existing label
      if ([...existing].some(n => dominates(n.cost, child.cost))) continue;

      // Remove labels dominated by new node
      for (const n of existing) {
        if (dominates(child.cost, n.cost)) existing.delete(n);
      }

      existing.add(child);
      this.frontier.add(child);
    }

    return current;
  }
}
```

**Returns multiple goal nodes** — one per Pareto-optimal path. Caller extracts the full frontier.

## State Reconstruction

Every search node carries a parent pointer. Path reconstruction walks the chain:

```javascript
function reconstructPath(goalNode) {
  const path = [];
  let current = goalNode;
  while (current) {
    path.unshift({ state: current.state, action: current.action });
    current = current.parent;
  }
  return path;
}
```

## Tabu Search

Memory-based local search — maintains a **tabu list** of recently visited states/moves to prevent cycling.

```javascript
class TabuSearchIterator {
  constructor(initialNode, expander, evaluator, { tabuTenure = 7, maxIter = 1000 }) {
    this.current = initialNode;
    this.current.score = evaluator.evaluate(initialNode.state);
    this.best = this.current;
    this.expander = expander;
    this.evaluator = evaluator;
    this.tabuList = [];         // Recent moves (FIFO, bounded by tenure)
    this.tabuTenure = tabuTenure;
    this.iter = 0;
  }

  next() {
    let bestNeighbor = null;

    for (const transition of this.expander.successorsOf(this.current.state)) {
      const child = this.expander.makeNode(this.current, transition);
      child.score = this.evaluator.evaluate(child.state);

      const isTabu = this.tabuList.includes(transitionKey(transition));

      // Accept if: (a) not tabu, or (b) tabu but better than global best (aspiration)
      if (!isTabu || child.score > this.best.score) {
        if (!bestNeighbor || child.score > bestNeighbor.score) {
          bestNeighbor = child;
          bestNeighbor._move = transitionKey(transition);
        }
      }
    }

    if (bestNeighbor) {
      this.current = bestNeighbor;
      this.tabuList.push(bestNeighbor._move);
      if (this.tabuList.length > this.tabuTenure) this.tabuList.shift();
      if (this.current.score > this.best.score) this.best = this.current;
    }

    return { node: this.current, best: this.best, iter: ++this.iter };
  }
}
```

| Component | Purpose |
|-----------|---------|
| **Tabu list** | Short-term memory — prevents revisiting recent moves |
| **Aspiration criterion** | Override tabu if move produces new global best |
| **Tabu tenure** | How long moves stay forbidden (tune: too short → cycling, too long → restricted) |
| **Long-term memory** | (Optional) frequency-based diversification — penalize overused moves |

## Adaptive Large Neighborhood Search (ALNS)

Destroy-and-repair paradigm — iteratively destroys part of a solution, then repairs it. Adaptive weights learn which operators work best.

```javascript
class ALNSIterator {
  constructor(initialSolution, destroyOps, repairOps, evaluator, { w1 = 33, w2 = 9, w3 = 13, decay = 0.1 }) {
    this.current = initialSolution;
    this.best = initialSolution;
    this.destroyOps = destroyOps.map(op => ({ op, weight: 1, score: 0, uses: 0 }));
    this.repairOps = repairOps.map(op => ({ op, weight: 1, score: 0, uses: 0 }));
    this.evaluator = evaluator;
    this.rewards = { newBest: w1, improved: w2, accepted: w3 };
    this.decay = decay;
  }

  next() {
    // Select operators via roulette wheel on adaptive weights
    const destroy = rouletteSelect(this.destroyOps);
    const repair = rouletteSelect(this.repairOps);

    // Destroy: remove part of solution
    const partial = destroy.op.execute(this.current);
    // Repair: reconstruct complete solution
    const candidate = repair.op.execute(partial);
    candidate.fitness = this.evaluator.evaluate(candidate);

    // Score operators based on outcome
    let reward = 0;
    if (candidate.fitness < this.best.fitness) {
      reward = this.rewards.newBest;
      this.best = candidate;
      this.current = candidate;
    } else if (candidate.fitness < this.current.fitness) {
      reward = this.rewards.improved;
      this.current = candidate;
    } else if (Math.random() < Math.exp(-(candidate.fitness - this.current.fitness) / this.T)) {
      reward = this.rewards.accepted;  // SA-style acceptance
      this.current = candidate;
    }

    // Update adaptive weights
    destroy.score += reward; destroy.uses++;
    repair.score += reward; repair.uses++;

    return { solution: this.current, best: this.best };
  }

  updateWeights() {
    for (const pool of [this.destroyOps, this.repairOps]) {
      for (const entry of pool) {
        if (entry.uses > 0) {
          entry.weight = entry.weight * (1 - this.decay) + this.decay * (entry.score / entry.uses);
          entry.score = 0; entry.uses = 0;
        }
      }
    }
  }
}
```

**Destroy operators**: random removal, worst removal, related removal, Shaw removal
**Repair operators**: greedy insertion, regret insertion, random insertion

## Constraint Propagation

For constraint satisfaction problems (CSP) — reduce domains before searching.

```javascript
class CSPSolver {
  constructor(variables, domains, constraints) {
    this.variables = variables;     // ['x1', 'x2', 'x3']
    this.domains = new Map(         // var → Set of possible values
      variables.map((v, i) => [v, new Set(domains[i])])
    );
    this.constraints = constraints; // [{vars: ['x1','x2'], test: (a,b) => a !== b}]
  }

  // AC-3: arc consistency — prune impossible values
  arcConsistency() {
    const queue = [...this.constraints];
    while (queue.length > 0) {
      const { vars: [xi, xj], test } = queue.shift();
      let revised = false;

      for (const vi of this.domains.get(xi)) {
        const supported = [...this.domains.get(xj)].some(vj => test(vi, vj));
        if (!supported) {
          this.domains.get(xi).delete(vi);
          revised = true;
        }
      }

      if (revised) {
        if (this.domains.get(xi).size === 0) return false; // No solution
        // Re-queue constraints involving xi
        queue.push(...this.constraints.filter(c => c.vars.includes(xi) && c !== { vars: [xi, xj], test }));
      }
    }
    return true;
  }

  // Backtracking search with constraint propagation
  solve() {
    if (!this.arcConsistency()) return null;
    return this._backtrack({});
  }

  _backtrack(assignment) {
    if (Object.keys(assignment).length === this.variables.length) return assignment;

    const unassigned = this.variables.find(v => !(v in assignment));
    for (const value of this.domains.get(unassigned)) {
      if (this._consistent(unassigned, value, assignment)) {
        assignment[unassigned] = value;
        const result = this._backtrack(assignment);
        if (result) return result;
        delete assignment[unassigned];
      }
    }
    return null;
  }
}
```

## Anti-Patterns

| WRONG | CORRECT |
|-------|---------|
| Recursive DFS/BFS | Iterator with explicit frontier |
| Hardcoded graph representation | Graph-agnostic via TransitionFunction |
| Algorithm knows about specific state types | Generic over `<S, A, C>` type parameters |
| Single `search()` call returns final path | Iterator yields nodes — caller controls termination |
| Heuristic baked into algorithm | Injected via HeuristicFunction interface |
| Reopening A* nodes without cost check | Only reopen if new g < existing g |
| IDA* without tracking minExceeded | Must track to set next iteration's fLimit |

## Integration with Evolutionary Optimization & Meta-Loop

The heuristic search skill connects to the other two QURA skills:

- **This skill** provides traversal algorithms for navigating solution spaces
- **Evolutionary Optimization** uses search as a subroutine for local refinement within genetic operators
- **Self-Optimizing Meta-Loop** uses search to navigate the space of possible code mutations

Together: **search** explores → **evolution** diversifies → **meta-loop** verifies.

## Subspace Geometry Analysis (From OBLITERATUS)

OBLITERATUS maps **refusal geometry** across transformer layers — 15 analysis modules characterizing where and how a behavior manifests in activation space. The search analog: characterize the **solution space geometry** before choosing an algorithm.

```javascript
class SolutionSpaceGeometry {
  constructor(problem, sampler) {
    this.problem = problem;
    this.sampler = sampler;  // Generates random states for geometric analysis
  }

  // Analyze the shape of the solution space before searching
  async characterize(sampleSize = 100) {
    const samples = Array.from({ length: sampleSize }, () => this.sampler.randomState());
    const costs = samples.map(s => this.problem.cost(s));
    const heuristics = samples.map(s => this.problem.heuristic(s));

    return {
      // 1. Landscape ruggedness: how much does cost vary between neighbors?
      ruggedness: await this.measureRuggedness(samples),

      // 2. Modality: unimodal (one basin) or multimodal (many basins)?
      modality: this.detectModality(costs),

      // 3. Deceptiveness: does the heuristic mislead? (correlation between h and actual cost-to-go)
      heuristicQuality: this.correlateHeuristicWithActual(heuristics, costs),

      // 4. Dimensionality: effective dimensions of the search space
      effectiveDimensions: this.estimateEffectiveDimensions(samples),

      // 5. Connectivity: how well-connected is the feasible region?
      connectivity: await this.estimateConnectivity(samples),

      // 6. Basin structure: monolithic or polyhedral?
      basinShape: this.classifyBasinShape(costs)
    };
  }

  // Ruggedness: autocorrelation of fitness along random walks
  async measureRuggedness(samples) {
    const walkLength = 50;
    const autocorrelations = [];

    for (let trial = 0; trial < 10; trial++) {
      let current = samples[Math.floor(Math.random() * samples.length)];
      const walkCosts = [this.problem.cost(current)];

      for (let step = 0; step < walkLength; step++) {
        const neighbors = [...this.problem.transitions(current)];
        if (neighbors.length === 0) break;
        current = neighbors[Math.floor(Math.random() * neighbors.length)].state;
        walkCosts.push(this.problem.cost(current));
      }

      autocorrelations.push(autocorrelation(walkCosts, 1));
    }

    const meanAC = autocorrelations.reduce((a, b) => a + b, 0) / autocorrelations.length;
    // High autocorrelation = smooth landscape → hill climbing works
    // Low autocorrelation = rugged landscape → need SA or tabu search
    return {
      autocorrelation: meanAC,
      classification: meanAC > 0.8 ? 'smooth' : meanAC > 0.4 ? 'moderate' : 'rugged'
    };
  }

  // Modality: count basins via random restarts of hill climbing
  detectModality(costs) {
    const sorted = [...costs].sort((a, b) => a - b);
    const threshold = sorted[Math.floor(sorted.length * 0.1)];  // Bottom 10%
    const basins = costs.filter(c => c <= threshold).length;

    return {
      estimatedBasins: basins,
      classification: basins <= 1 ? 'unimodal' : basins <= 5 ? 'oligomodal' : 'multimodal'
    };
  }

  // Heuristic quality: does h(s) predict actual distance to goal?
  correlateHeuristicWithActual(heuristics, costs) {
    const correlation = pearsonCorrelation(heuristics, costs);
    return {
      correlation,
      quality: correlation > 0.8 ? 'excellent' : correlation > 0.5 ? 'moderate' : 'poor',
      advisory: correlation < 0.3
        ? 'Heuristic is misleading — prefer uninformed or local search'
        : correlation < 0.6
        ? 'Heuristic gives weak guidance — A* will work but expand many nodes'
        : 'Heuristic is informative — A* or IDA* recommended'
    };
  }

  // Effective dimensionality via PCA on sample states
  estimateEffectiveDimensions(samples) {
    const vectors = samples.map(s => stateToVector(s));
    const { eigenvalues } = pca(vectors);
    const totalVariance = eigenvalues.reduce((a, b) => a + b, 0);
    let cumulative = 0;
    let effectiveDims = 0;
    for (const ev of eigenvalues) {
      cumulative += ev;
      effectiveDims++;
      if (cumulative / totalVariance >= 0.95) break;  // 95% variance explained
    }
    return { effectiveDims, totalDims: vectors[0].length, ratio: effectiveDims / vectors[0].length };
  }

  // Basin shape: monolithic (one big basin) or polyhedral (many faceted basins)
  classifyBasinShape(costs) {
    const variance = statisticalVariance(costs);
    const kurtosis = excessKurtosis(costs);
    // High kurtosis = peaked = monolithic basin
    // Low kurtosis = flat = polyhedral/fragmented basins
    return {
      kurtosis,
      classification: kurtosis > 3 ? 'monolithic' : kurtosis > 0 ? 'mixed' : 'polyhedral'
    };
  }
}
```

## Geometry-Informed Algorithm Selection

Use the geometric characterization to auto-select the best search algorithm — derived, not hardcoded.

```javascript
class GeometryInformedSelector {
  // Maps geometry → recommended algorithm (IARM semantic selection)
  select(geometry) {
    const { ruggedness, modality, heuristicQuality, effectiveDimensions, basinShape } = geometry;

    // Decision tree derived from landscape analysis
    if (ruggedness.classification === 'smooth' && modality.classification === 'unimodal') {
      if (heuristicQuality.quality === 'excellent') return 'aStar';
      return 'hillClimbing';
    }

    if (ruggedness.classification === 'rugged' && modality.classification === 'multimodal') {
      if (effectiveDimensions.ratio < 0.3) return 'simulatedAnnealing';  // Low-dim rugged → SA
      return 'tabuSearch';  // High-dim rugged → memory-guided search
    }

    if (basinShape.classification === 'polyhedral') {
      return 'alns';  // Polyhedral → adaptive destroy-and-rebuild
    }

    if (modality.classification === 'oligomodal' && heuristicQuality.quality !== 'poor') {
      return 'idaStar';  // Few basins + decent heuristic → memory-efficient optimal
    }

    if (effectiveDimensions.ratio > 0.8) {
      return 'csp';  // High effective dims → constraint propagation to prune
    }

    // Default: A* if heuristic is any good, else BFS
    return heuristicQuality.quality !== 'poor' ? 'aStar' : 'bfs';
  }
}
```

| Geometry | Landscape | Best Algorithm | IARM Meaning |
|----------|-----------|---------------|-------------|
| Smooth + unimodal + good heuristic | Single funnel, gradient points down | A* | Informed optimism |
| Smooth + unimodal + poor heuristic | Single funnel, blind | Hill climbing | Greedy ascent |
| Rugged + multimodal + low-dim | Many traps, few variables | Simulated annealing | Disciplined chaos |
| Rugged + multimodal + high-dim | Many traps, many variables | Tabu search | Memory-guided novelty |
| Polyhedral basins | Faceted, non-convex | ALNS | Adaptive destruction |
| Oligomodal + decent heuristic | Few basins, some guidance | IDA* | Frugal persistence |
| High effective dimensionality | Large feasible space | CSP | Constraint narrowing |

**Cross-plane connection**: geometry analysis results feed into hyperswarm144's IARM spreading activation — the geometry characterization activates the Ω₁ (search) plane nodes corresponding to the best-matching algorithm.
