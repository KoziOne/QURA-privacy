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

| Algorithm | Type | Use Case | Memory | Optimality |
|-----------|------|----------|--------|------------|
| **BFS** | Uninformed | Shortest path (unweighted) | O(b^d) | Yes |
| **DFS** | Uninformed | Exhaustive exploration | O(bd) | No |
| **Dijkstra** | Uninformed | Shortest path (weighted) | O(V+E) | Yes |
| **Bellman-Ford** | Uninformed | Negative weights | O(VE) | Yes |
| **A*** | Informed | Best-first with heuristic | O(b^d) | Yes (admissible h) |
| **IDA*** | Informed | Memory-bounded A* | O(bd) | Yes |
| **AD*** | Informed | Anytime, dynamic replanning | O(b^d) | Bounded suboptimal |
| **Hill Climbing** | Local | Fast local optimization | O(1) | No (local optima) |
| **Enforced Hill Climbing** | Local | Escape plateaus via BFS | O(b^d) | No |
| **Multiobjective** | Multi | Pareto-optimal frontiers | O(b^d) | Pareto-optimal |

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
  constructor(initialNode, expander, heuristic) {
    super(initialNode, expander);
    this.frontier = new PriorityQueue((a, b) => a.f - b.f);  // Min-heap on f
    this.heuristic = heuristic;

    initialNode.g = 0;
    initialNode.h = heuristic.estimate(initialNode.state);
    initialNode.f = initialNode.g + initialNode.h;
    this.frontier.add(initialNode);
  }

  next() {
    const current = this.frontier.remove();

    for (const transition of this.expander.successorsOf(current.state)) {
      const child = this.expander.makeNode(current, transition);
      const tentativeG = current.g + this.expander.cost(transition);

      if (!this.visited.has(child.state) || tentativeG < this.visited.get(child.state).g) {
        child.g = tentativeG;
        child.h = this.heuristic.estimate(child.state);
        child.f = child.g + child.h;
        child.parent = current;
        this.visited.set(child.state, child);
        this.frontier.add(child);
      }
    }

    return current;
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

## Cost Function Patterns

| Pattern | Formula | Use Case |
|---------|---------|----------|
| **Uniform** | `cost(t) = 1` | Unweighted graphs (BFS equivalent) |
| **Weighted** | `cost(t) = t.weight` | Standard shortest path |
| **Composite** | `cost(t) = w₁·f₁(t) + w₂·f₂(t)` | Weighted multi-criteria |
| **Dynamic** | `cost(t) = f(t, context)` | Context-dependent (AD*) |

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
