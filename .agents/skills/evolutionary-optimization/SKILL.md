---
name: evolutionary-optimization
description: Implement evolutionary and metaheuristic optimization systems — genetic algorithms, genetic programming, symbolic regression, particle swarm, differential evolution, and multi-objective optimization. Based on the HeuristicLab/HEAL research ecosystem architecture — plugin-based, operator-graph driven, with programmable problem definitions. Use this skill for fitness-driven optimization, population-based search, operator composition, solution encoding, and benchmark evaluation. Covers both single-objective and Pareto multi-objective scenarios.
---

<!-- EDITORIAL GUIDELINES
Correction layer for evolutionary/metaheuristic optimization. Every line costs context.
- Be terse. Tables and code over prose.
- Focus on composable operator patterns and problem encodings.
- Single consolidated examples over fragments.
-->

Evolutionary optimization evolves populations of candidate solutions through selection, variation (mutation + crossover), and fitness evaluation. The key insight: algorithms are **compositions of operators**, not monolithic procedures. Each operator is swappable, composable, and independently testable.

## Algorithm Catalog

| Algorithm | Type | Key Operators | Best For |
|-----------|------|---------------|----------|
| **Genetic Algorithm (GA)** | Population | Selection + Crossover + Mutation | Combinatorial, discrete |
| **Genetic Programming (GP)** | Population | Tree crossover + subtree mutation | Symbolic regression, program synthesis |
| **Evolution Strategy (ES)** | Population | Gaussian mutation + (μ,λ) selection | Continuous optimization |
| **Differential Evolution (DE)** | Population | Vector difference mutation | Continuous, multimodal |
| **Particle Swarm (PSO)** | Swarm | Velocity + Position update | Continuous, fast convergence |
| **Simulated Annealing (SA)** | Trajectory | Metropolis acceptance | Combinatorial, escape local optima |
| **Tabu Search** | Trajectory | Tabu list + aspiration | Combinatorial, avoid cycling |
| **NSGA-II** | Multi-objective | Non-dominated sorting + crowding | Pareto frontier discovery |
| **ALPS** | Age-layered | Age-based population layering | Diversity maintenance |
| **Offspring Selection GA** | Population | Fitness-based offspring acceptance | Quality control |

## Core Type System

```
Solution          — Encoded candidate (bit string, real vector, tree, permutation)
Fitness           — Evaluation result (single number, or vector for multi-objective)
Operator          — Transforms solution(s): selection, crossover, mutation, evaluation
Problem           — Defines encoding + fitness function + constraints
Population        — Collection of solutions with associated fitness values
OperatorGraph     — DAG of operators defining algorithm flow
```

## Operator Composition Pattern

Algorithms are built by composing operators into a directed graph — not by writing monolithic loops.

```javascript
// Each operator is a standalone, composable unit
class Operator {
  constructor(name) { this.name = name; }
  execute(scope) { throw new Error('implement in subclass'); }
}

class TournamentSelection extends Operator {
  constructor(tournamentSize = 3) {
    super('TournamentSelection');
    this.k = tournamentSize;
  }

  execute(population) {
    const tournament = sample(population, this.k);
    return tournament.reduce((best, ind) =>
      ind.fitness < best.fitness ? ind : best
    );
  }
}

class SinglePointCrossover extends Operator {
  execute(parent1, parent2) {
    const point = randInt(0, parent1.genes.length);
    return {
      child1: [...parent1.genes.slice(0, point), ...parent2.genes.slice(point)],
      child2: [...parent2.genes.slice(0, point), ...parent1.genes.slice(point)]
    };
  }
}

class GaussianMutation extends Operator {
  constructor(sigma = 0.1) {
    super('GaussianMutation');
    this.sigma = sigma;
  }

  execute(solution) {
    return solution.genes.map(g => g + gaussian(0, this.sigma));
  }
}
```

## Algorithm as Operator Graph

```javascript
// Algorithm = ordered composition of operators
class EvolutionaryAlgorithm {
  constructor({ problem, populationSize, maxGenerations, operators }) {
    this.problem = problem;
    this.popSize = populationSize;
    this.maxGen = maxGenerations;
    this.selector = operators.selection;
    this.crossover = operators.crossover;
    this.mutator = operators.mutation;
    this.evaluator = operators.evaluation || (s => problem.evaluate(s));
  }

  run() {
    let population = this.initialize();
    population.forEach(ind => ind.fitness = this.evaluator(ind));

    for (let gen = 0; gen < this.maxGen; gen++) {
      const offspring = [];

      while (offspring.length < this.popSize) {
        // Select parents
        const p1 = this.selector.execute(population);
        const p2 = this.selector.execute(population);

        // Vary
        let { child1, child2 } = this.crossover.execute(p1, p2);
        child1 = this.mutator.execute(child1);
        child2 = this.mutator.execute(child2);

        // Evaluate
        child1.fitness = this.evaluator(child1);
        child2.fitness = this.evaluator(child2);

        offspring.push(child1, child2);
      }

      population = this.replace(population, offspring);
      this.onGeneration?.(gen, population);  // Hook for logging/analysis
    }

    return population.reduce((best, ind) => ind.fitness < best.fitness ? ind : best);
  }

  initialize() {
    return Array.from({ length: this.popSize }, () => this.problem.createRandom());
  }

  replace(parents, offspring) {
    return [...parents, ...offspring]
      .sort((a, b) => a.fitness - b.fitness)
      .slice(0, this.popSize);
  }
}
```

## Problem Definition Pattern (Programmable)

Problems are defined by encoding + evaluation — completely decoupled from algorithms.

```javascript
// Single-objective problem
class OptimizationProblem {
  constructor({ dimensions, bounds, evaluate }) {
    this.dimensions = dimensions;
    this.bounds = bounds;    // [[min, max], ...] per dimension
    this.evaluate = evaluate;
  }

  createRandom() {
    return {
      genes: this.bounds.map(([lo, hi]) => lo + Math.random() * (hi - lo)),
      fitness: null
    };
  }
}

// Multi-objective problem
class MultiObjectiveProblem extends OptimizationProblem {
  constructor({ dimensions, bounds, objectives }) {
    super({ dimensions, bounds, evaluate: null });
    this.objectives = objectives;  // Array of evaluation functions
  }

  evaluate(solution) {
    return this.objectives.map(obj => obj(solution.genes));
  }
}
```

### Standard Test Functions

| Function | Dims | Optimum | Properties |
|----------|------|---------|------------|
| **Sphere** | n | f(0,...,0) = 0 | Unimodal, separable |
| **Rastrigin** | n | f(0,...,0) = 0 | Multimodal, separable |
| **Rosenbrock** | n | f(1,...,1) = 0 | Unimodal, non-separable (banana valley) |
| **Ackley** | n | f(0,...,0) = 0 | Multimodal, nearly flat outer region |
| **Schwefel** | n | f(420.97,...) = 0 | Deceptive, global far from local optima |
| **Griewank** | n | f(0,...,0) = 0 | Many local optima, large scale |

```javascript
const testFunctions = {
  sphere: genes => genes.reduce((s, x) => s + x * x, 0),
  rastrigin: genes => 10 * genes.length + genes.reduce((s, x) => s + x * x - 10 * Math.cos(2 * Math.PI * x), 0),
  rosenbrock: genes => genes.slice(0, -1).reduce((s, x, i) => s + 100 * (genes[i + 1] - x * x) ** 2 + (1 - x) ** 2, 0),
  ackley: genes => {
    const n = genes.length;
    const sumSq = genes.reduce((s, x) => s + x * x, 0);
    const sumCos = genes.reduce((s, x) => s + Math.cos(2 * Math.PI * x), 0);
    return -20 * Math.exp(-0.2 * Math.sqrt(sumSq / n)) - Math.exp(sumCos / n) + 20 + Math.E;
  }
};
```

## Genetic Programming (Tree-Based)

For symbolic regression and program synthesis — solutions are expression trees.

```javascript
// Tree node types
class TerminalNode {
  constructor(value) { this.value = value; }  // constant or variable
  evaluate(vars) { return typeof this.value === 'string' ? vars[this.value] : this.value; }
  depth() { return 0; }
}

class FunctionNode {
  constructor(op, children) { this.op = op; this.children = children; }
  evaluate(vars) {
    const args = this.children.map(c => c.evaluate(vars));
    return this.op.fn(...args);
  }
  depth() { return 1 + Math.max(...this.children.map(c => c.depth())); }
}

// Operator set
const gpOps = {
  add: { arity: 2, fn: (a, b) => a + b, symbol: '+' },
  sub: { arity: 2, fn: (a, b) => a - b, symbol: '-' },
  mul: { arity: 2, fn: (a, b) => a * b, symbol: '*' },
  div: { arity: 2, fn: (a, b) => Math.abs(b) < 1e-10 ? 1 : a / b, symbol: '/' },
  sin: { arity: 1, fn: Math.sin, symbol: 'sin' },
  cos: { arity: 1, fn: Math.cos, symbol: 'cos' },
  exp: { arity: 1, fn: x => Math.min(Math.exp(x), 1e15), symbol: 'exp' },
  log: { arity: 1, fn: x => Math.log(Math.abs(x) + 1e-10), symbol: 'log' }
};

// Subtree crossover
function subtreeCrossover(parent1, parent2) {
  const p1Copy = deepClone(parent1);
  const p2Copy = deepClone(parent2);
  const point1 = randomNode(p1Copy);
  const point2 = randomNode(p2Copy);
  replaceSubtree(p1Copy, point1, getSubtree(p2Copy, point2));
  return p1Copy;
}

// Subtree mutation: replace random subtree with new random tree
function subtreeMutation(tree, maxDepth = 3) {
  const copy = deepClone(tree);
  const point = randomNode(copy);
  replaceSubtree(copy, point, generateRandomTree(maxDepth));
  return copy;
}
```

## Symbolic Regression

Find mathematical expressions that fit data — the intersection of GP and optimization.

```javascript
// Fitness = how well the tree predicts target values
function symbolicRegressionFitness(tree, dataset) {
  let totalError = 0;
  for (const { inputs, target } of dataset) {
    const predicted = tree.evaluate(inputs);
    totalError += (predicted - target) ** 2;
  }
  return totalError / dataset.length;  // MSE
}

// Complexity penalty (Occam's razor — prefer simpler expressions)
function parsimonyFitness(tree, dataset, parsimonyCoeff = 0.01) {
  const mse = symbolicRegressionFitness(tree, dataset);
  const complexity = countNodes(tree);
  return mse + parsimonyCoeff * complexity;
}
```

## Particle Swarm Optimization (PSO)

Swarm intelligence — particles fly through solution space, guided by personal and global bests.

```javascript
class ParticleSwarmOptimizer {
  constructor({ problem, swarmSize = 50, w = 0.729, c1 = 1.49445, c2 = 1.49445 }) {
    this.problem = problem;
    this.w = w;      // Inertia weight
    this.c1 = c1;    // Cognitive coefficient (personal best attraction)
    this.c2 = c2;    // Social coefficient (global best attraction)

    this.particles = Array.from({ length: swarmSize }, () => {
      const position = problem.createRandom().genes;
      return {
        position,
        velocity: position.map(() => (Math.random() - 0.5) * 0.1),
        fitness: problem.evaluate({ genes: position }),
        bestPosition: [...position],
        bestFitness: Infinity
      };
    });

    this.globalBest = null;
    this.updateGlobalBest();
  }

  step() {
    for (const p of this.particles) {
      // Update velocity
      for (let d = 0; d < p.position.length; d++) {
        const r1 = Math.random(), r2 = Math.random();
        p.velocity[d] = this.w * p.velocity[d]
          + this.c1 * r1 * (p.bestPosition[d] - p.position[d])
          + this.c2 * r2 * (this.globalBest.position[d] - p.position[d]);
      }

      // Update position
      p.position = p.position.map((x, d) => x + p.velocity[d]);
      p.fitness = this.problem.evaluate({ genes: p.position });

      // Update personal best
      if (p.fitness < p.bestFitness) {
        p.bestFitness = p.fitness;
        p.bestPosition = [...p.position];
      }
    }
    this.updateGlobalBest();
  }

  updateGlobalBest() {
    const best = this.particles.reduce((b, p) => p.bestFitness < b.bestFitness ? p : b);
    if (!this.globalBest || best.bestFitness < this.globalBest.fitness) {
      this.globalBest = { position: [...best.bestPosition], fitness: best.bestFitness };
    }
  }
}
```

## Differential Evolution (DE)

Powerful for continuous optimization — uses vector differences for mutation.

```javascript
class DifferentialEvolution {
  constructor({ problem, popSize = 50, F = 0.8, CR = 0.9 }) {
    this.problem = problem;
    this.F = F;    // Differential weight (mutation scale)
    this.CR = CR;  // Crossover probability
    this.population = Array.from({ length: popSize }, () => {
      const ind = problem.createRandom();
      ind.fitness = problem.evaluate(ind);
      return ind;
    });
  }

  step() {
    for (let i = 0; i < this.population.length; i++) {
      const target = this.population[i];

      // Select 3 distinct random individuals (not target)
      const [a, b, c] = sampleExcluding(this.population, 3, i);

      // DE/rand/1/bin: mutant = a + F * (b - c)
      const trial = {
        genes: target.genes.map((x, d) => {
          if (Math.random() < this.CR || d === randInt(0, target.genes.length)) {
            return a.genes[d] + this.F * (b.genes[d] - c.genes[d]);
          }
          return x;  // Keep target gene
        })
      };

      trial.fitness = this.problem.evaluate(trial);

      // Greedy selection: keep better of target and trial
      if (trial.fitness <= target.fitness) {
        this.population[i] = trial;
      }
    }
  }
}
```

## Multi-Objective: NSGA-II

Non-dominated Sorting Genetic Algorithm II — the standard for Pareto optimization.

```javascript
function nsgaIISort(population) {
  // 1. Non-dominated sorting into fronts
  const fronts = [[]];
  const dominationCount = new Map();  // How many dominate me
  const dominatedSet = new Map();     // Who I dominate

  for (const p of population) {
    dominationCount.set(p, 0);
    dominatedSet.set(p, []);

    for (const q of population) {
      if (p === q) continue;
      if (dominates(p.fitness, q.fitness)) {
        dominatedSet.get(p).push(q);
      } else if (dominates(q.fitness, p.fitness)) {
        dominationCount.set(p, dominationCount.get(p) + 1);
      }
    }

    if (dominationCount.get(p) === 0) {
      p.rank = 0;
      fronts[0].push(p);
    }
  }

  // Build subsequent fronts
  let i = 0;
  while (fronts[i].length > 0) {
    const nextFront = [];
    for (const p of fronts[i]) {
      for (const q of dominatedSet.get(p)) {
        dominationCount.set(q, dominationCount.get(q) - 1);
        if (dominationCount.get(q) === 0) {
          q.rank = i + 1;
          nextFront.push(q);
        }
      }
    }
    fronts.push(nextFront);
    i++;
  }

  // 2. Crowding distance within each front
  for (const front of fronts) {
    assignCrowdingDistance(front);
  }

  return fronts;
}

function assignCrowdingDistance(front) {
  if (front.length <= 2) {
    front.forEach(p => p.crowding = Infinity);
    return;
  }

  front.forEach(p => p.crowding = 0);
  const numObjectives = front[0].fitness.length;

  for (let m = 0; m < numObjectives; m++) {
    front.sort((a, b) => a.fitness[m] - b.fitness[m]);
    front[0].crowding = Infinity;
    front[front.length - 1].crowding = Infinity;

    const range = front[front.length - 1].fitness[m] - front[0].fitness[m];
    if (range === 0) continue;

    for (let i = 1; i < front.length - 1; i++) {
      front[i].crowding += (front[i + 1].fitness[m] - front[i - 1].fitness[m]) / range;
    }
  }
}
```

## Offspring Selection (Quality-Gated)

From HeuristicLab's Offspring Selection GA — only accept offspring better than parents.

```javascript
function offspringSelectionStep(population, operators, successRatio = 0.5, comparisonFactor = 0.5) {
  const offspring = [];
  let successCount = 0;
  let totalAttempts = 0;
  const targetSuccesses = Math.floor(population.length * successRatio);

  while (successCount < targetSuccesses) {
    const p1 = operators.selection.execute(population);
    const p2 = operators.selection.execute(population);
    let child = operators.crossover.execute(p1, p2);
    child = operators.mutation.execute(child);
    child.fitness = operators.evaluate(child);

    const parentFitness = Math.min(p1.fitness, p2.fitness);
    const threshold = parentFitness * (1 + comparisonFactor);

    if (child.fitness <= threshold) {
      offspring.push(child);
      successCount++;
    }

    totalAttempts++;
    if (totalAttempts > population.length * 10) break;  // Prevent infinite loop
  }

  return { offspring, actualSuccessRatio: successCount / totalAttempts };
}
```

## Plugin Architecture Pattern

From HeuristicLab — algorithms, problems, and operators are plugins that discover each other at runtime.

```javascript
// Plugin registry — operators register themselves by interface
class PluginRegistry {
  constructor() { this.plugins = new Map(); }

  register(interfaceType, implementation) {
    if (!this.plugins.has(interfaceType)) this.plugins.set(interfaceType, []);
    this.plugins.get(interfaceType).push(implementation);
  }

  getAll(interfaceType) { return this.plugins.get(interfaceType) || []; }
  get(interfaceType, name) { return this.getAll(interfaceType).find(p => p.name === name); }
}

// Self-registering operators
const registry = new PluginRegistry();
registry.register('ISelector', new TournamentSelection(3));
registry.register('ISelector', new RouletteWheelSelection());
registry.register('ICrossover', new SinglePointCrossover());
registry.register('ICrossover', new UniformCrossover());
registry.register('IMutator', new GaussianMutation(0.1));
registry.register('IMutator', new BitFlipMutation(0.01));
registry.register('IProblem', sphereProblem);
registry.register('IProblem', rastriginProblem);
```

## Solution Encodings

| Encoding | Representation | Operators | Use Case |
|----------|---------------|-----------|----------|
| **Binary** | `[0,1,1,0,1]` | Bit flip, single-point crossover | Discrete, knapsack |
| **Real-valued** | `[0.5, -1.2, 3.7]` | Gaussian mutation, BLX-α crossover | Continuous optimization |
| **Permutation** | `[3,1,4,2,5]` | Swap, inversion, order crossover | TSP, scheduling |
| **Tree** | Expression tree | Subtree crossover/mutation | GP, symbolic regression |
| **Integer** | `[5, 2, 8, 1]` | Random reset, uniform crossover | Combinatorial |

## Anti-Patterns

| WRONG | CORRECT |
|-------|---------|
| Monolithic algorithm loop | Composable operator graph |
| Hardcoded selection/crossover | Pluggable operators via interfaces |
| Evaluate fitness inside algorithm | Separate Problem with evaluate() |
| No diversity management | Crowding distance, niching, or ALPS |
| Premature convergence without detection | Track population diversity metrics |
| GP trees grow unbounded | Max depth limit + parsimony pressure |
| PSO without velocity clamping | Clamp velocity to prevent explosion |
| DE with fixed F and CR | Self-adaptive or jDE variant |

## Integration with Heuristic Search & Meta-Loop

This skill connects to the other two QURA skills:

- **Heuristic Search** provides local refinement within evolutionary operators (memetic algorithms)
- **This skill** provides the population-based diversification and genetic operators
- **Self-Optimizing Meta-Loop** uses evolutionary operators to generate mutation candidates, then benchmarks to keep winners

Together: **search** refines locally → **evolution** explores globally → **meta-loop** verifies improvements.
