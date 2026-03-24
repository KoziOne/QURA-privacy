---
name: self-optimizing-meta-loop
description: Implement self-improving AI systems using meta-learning optimization cycles. Use when building agents that analyze, mutate, benchmark, and improve their own code or reasoning. Based on the reasoningHeuristicAI (rHAI) architecture — a closed-loop system where an agent selects improvements from candidate mutations, benchmarks them, and keeps only what measurably improves performance. Use this skill for meta-controllers, self-optimization loops, reason-act orchestrators, and performance-driven code evolution.
---

<!-- EDITORIAL GUIDELINES
Correction layer for self-optimizing agent architectures. Every line costs context.
- Be terse. Tables and code over prose.
- Only include patterns that differ from naive implementations.
- Prefer one consolidated block over many small ones.
- Focus on the selection-over-generation paradigm.
-->

Self-optimizing systems shift the problem from **generation** (hard, unbounded) to **selection** (easier, measurable). The agent doesn't write arbitrary code — it evaluates candidate mutations against benchmarks and keeps only what improves metrics.

## Architecture Overview

```
┌─────────────────────────────────────────────┐
│ 1. BENCHMARK — Measure current performance  │
│    metrics: loss, latency, accuracy, memory  │
└──────────────┬──────────────────────────────┘
               ↓
┌─────────────────────────────────────────────┐
│ 2. MUTATE — Present candidate changes       │
│    source: mutation library, not generation  │
└──────────────┬──────────────────────────────┘
               ↓
┌─────────────────────────────────────────────┐
│ 3. EVALUATE — Agent selects accept/reject   │
│    basis: structured reasoning, not guess    │
└──────────────┬──────────────────────────────┘
               ↓
┌─────────────────────────────────────────────┐
│ 4. VERIFY — Re-benchmark, keep or revert    │
│    rule: measurable improvement only         │
└─────────────────────────────────────────────┘
```

## Core Components

| Component | Role | Key Pattern |
|-----------|------|-------------|
| **Meta-Controller** | Orchestrates the optimization cycle | Benchmark → Mutate → Evaluate → Verify |
| **Reason-Act Orchestrator** | Agent reasoning loop with tool use | Prompt → JSON Action → Tool Exec → Context Update (max N steps) |
| **Heuristic Engine** | Decision model (GRU/transformer) | forward() → generate() → structured JSON output |
| **Benchmark Harness** | Performance measurement | Deterministic metrics extraction via regex/parsing |
| **Mutation Library** | Candidate code changes | Pre-defined diffs, not free generation |
| **Reversion Guard** | Safety mechanism | Backup → Apply → Test → Keep/Revert |

## Meta-Controller Pattern

```javascript
// The core optimization cycle — selection over generation
async function metaOptimize(targetFile, mutationsDir, modelPath) {
  const baseline = await benchmark();  // Step 1: measure current state

  const mutations = await loadMutations(mutationsDir);
  const agent = await initOrchestrator(modelPath);

  for (const mutation of mutations) {
    const original = await readFile(targetFile);

    // Step 2-3: present mutation, agent evaluates
    const prompt = formatMutationPrompt(original, mutation, baseline);
    const decision = await agent.run(prompt);

    if (decision.action === 'approve') {
      await writeFile(targetFile, applyMutation(original, mutation));
      const result = await benchmark();  // Step 4: verify

      if (result.loss < baseline.loss || result.time < baseline.time) {
        baseline.loss = result.loss;     // Keep improvement
        baseline.time = result.time;
      } else {
        await writeFile(targetFile, original);  // Revert degradation
      }
    }
  }
}
```

**Critical rules:**
- NEVER keep a mutation that degrades any metric without explicit tradeoff approval
- ALWAYS benchmark deterministically — same inputs, same conditions
- ALWAYS maintain reversion capability — backup before every mutation

## Reason-Act Orchestrator Pattern

```javascript
// Multi-step reasoning with tool execution
async function reasonActLoop(goal, tools, engine, maxSteps = 10) {
  const context = [];

  for (let step = 0; step < maxSteps; step++) {
    // REASON: generate structured action
    const prompt = formatPrompt(goal, context, tools);
    const output = engine.generate(prompt);
    const action = extractJson(output);

    // TERMINATE: agent signals completion
    if (action.type === 'finish') return action.result;

    // ACT: execute tool, capture result
    const toolResult = await tools[action.type].execute(action.params);
    context.push({ action, result: toolResult });
  }

  return synthesize(context);  // Fallback: summarize partial progress
}
```

**Action format** (structured JSON, never free text):
```json
{
  "type": "read_file | execute_math | modify_code | finish",
  "params": { "target": "...", "content": "..." },
  "reasoning": "Why this action advances the goal"
}
```

## Benchmark Harness Pattern

```javascript
// Deterministic, parseable metrics extraction
async function benchmark() {
  const output = await exec('node benchmark.js');
  return {
    loss: parseFloat(output.match(/Final Loss: ([\d.]+)/)?.[1]),
    time: parseInt(output.match(/Time: (\d+)ms/)?.[1]),
    timestamp: Date.now()
  };
}
```

**Rules:**
- Metrics must be machine-parseable (regex or structured output)
- Run identical inputs every time — no stochastic variation in benchmarks
- Track timestamp for audit trail

## Mutation Library Design

```
mutations/
├── optimize_matmul.js       # Fused matrix multiply
├── cache_activations.js     # Memoize repeated forward passes
├── vectorize_ops.js         # SIMD-friendly data layout
├── reduce_allocations.js    # Object pool for tensors
└── simplify_backward.js     # Streamlined gradient computation
```

Each mutation is a **self-contained diff** — not a prompt, not generated code. The agent's job is to evaluate whether the diff improves the system, not to write the diff.

**Mutation format:**
```javascript
export default {
  name: 'optimize_matmul',
  description: 'Replace naive triple-loop with tiled multiplication',
  target: 'core/slmnet/Ops.js',
  apply(source) { /* return modified source */ },
  revert(source) { /* return original source */ }
}
```

## Heuristic Engine (Decision Model)

Architecture for the GRU-based evaluator:

```
Token IDs → Embedding(vocab, 128) → GRU(128, 256) → Dense(256, vocab) → Logits
```

| Config | Default | Purpose |
|--------|---------|---------|
| `embedding_dim` | 128 | Token representation density |
| `hidden_dim` | 256 | Recurrent state capacity |
| `grad_clip` | 1.0 | Prevent exploding gradients |
| `learning_rate` | 0.001 | Adam optimizer step size |
| `β₁, β₂` | 0.9, 0.999 | Adam moment decay rates |

**Training data format** (JSONL):
```json
{"prompt": "Evaluate this code change...", "completion": "{\"action\": \"approve\", \"reasoning\": \"...\"}"}
```

## Reversion Guard

```javascript
class ReversionGuard {
  constructor() { this.snapshots = new Map(); }

  async protect(filePath, mutation) {
    const original = await readFile(filePath);
    this.snapshots.set(filePath, original);

    try {
      const modified = mutation.apply(original);
      await writeFile(filePath, modified);
      return { applied: true, revert: () => writeFile(filePath, original) };
    } catch (e) {
      await writeFile(filePath, original);  // Auto-revert on error
      return { applied: false, error: e };
    }
  }
}
```

## Anti-Patterns

| WRONG | CORRECT |
|-------|---------|
| Agent generates arbitrary code mutations | Agent selects from pre-defined mutation candidates |
| Benchmark with random inputs each run | Deterministic benchmark with fixed inputs |
| Keep mutation if "looks good" | Keep mutation only if metrics measurably improve |
| Apply multiple mutations at once | Apply one mutation, benchmark, then decide |
| No revert mechanism | Always backup before mutation, auto-revert on failure |
| Free-text agent output | Structured JSON actions with typed fields |
| Unbounded reasoning loop | Max step limit (10) with fallback synthesis |

## Learned Heuristic Selection (RL + Meta-Loop)

Instead of hand-coding which mutation/operator to try, learn a policy that selects improvement operators based on the current state.

```javascript
// RL agent learns which improvement operator to apply
class LearnedOperatorSelector {
  constructor(operators, { stateFeatures, lr = 0.01, gamma = 0.99 }) {
    this.operators = operators;
    this.stateFeatures = stateFeatures; // solution → feature vector
    this.qTable = new Map();            // (stateKey, opIndex) → Q-value
    this.lr = lr;
    this.gamma = gamma;
  }

  selectOperator(solution) {
    const state = this.stateFeatures(solution);
    const key = stateKey(state);

    // Epsilon-greedy over operators
    if (Math.random() < 0.1) return randInt(0, this.operators.length);
    return argmax(this.operators.map((_, i) => this.getQ(key, i)));
  }

  update(state, opIndex, reward, nextState) {
    const key = stateKey(state);
    const nextKey = stateKey(nextState);
    const maxNextQ = Math.max(...this.operators.map((_, i) => this.getQ(nextKey, i)));
    const target = reward + this.gamma * maxNextQ;
    const current = this.getQ(key, opIndex);
    this.setQ(key, opIndex, current + this.lr * (target - current));
  }

  // Integration with meta-loop: reward = benchmark improvement
  async optimizeWithRL(targetFile) {
    let solution = await readFile(targetFile);
    let baseline = await benchmark();

    for (let step = 0; step < maxSteps; step++) {
      const state = this.stateFeatures(solution);
      const opIdx = this.selectOperator(solution);
      const operator = this.operators[opIdx];

      const candidate = operator.apply(solution);
      await writeFile(targetFile, candidate);
      const result = await benchmark();

      const reward = baseline.loss - result.loss;  // Positive = improvement
      this.update(state, opIdx, reward, this.stateFeatures(candidate));

      if (result.loss < baseline.loss) {
        solution = candidate;
        baseline = result;
      } else {
        await writeFile(targetFile, solution);  // Revert
      }
    }
  }
}
```

**Key insight**: the meta-loop's benchmark provides a **natural reward signal** for RL. The agent learns which operators work in which contexts — no hand-tuning needed. This bridges the gap between the meta-controller's selection paradigm and the hyper-heuristic's adaptive learning.

## Integration with Heuristic Search & Evolutionary Optimization

The meta-loop composes with the other two QURA skills:

- **Heuristic Search** provides the traversal algorithms the engine uses to navigate solution spaces
- **Evolutionary Optimization** provides the mutation/crossover/selection operators that generate candidate mutations, plus hyper-heuristics that learn which operators to apply
- **This skill** provides the closed-loop verification that ensures only improvements survive, plus RL-based operator selection

Together: **search** finds candidates → **evolution** generates mutations → **meta-loop** verifies and learns which strategies work.

## Iterative Refinement with Re-Probing (From OBLITERATUS)

OBLITERATUS discovered that single-pass modifications miss problems that **rotate into adjacent subspaces**. The same principle applies to code optimization — a mutation might fix one metric while degrading another in ways a single benchmark pass doesn't catch.

```javascript
class IterativeRefinement {
  constructor({ maxPasses = 3, convergenceThreshold = 0.01, klBudget = 0.1 }) {
    this.maxPasses = maxPasses;
    this.convergenceThreshold = convergenceThreshold;
    this.klBudget = klBudget;
  }

  // Multi-pass refinement: re-probe after each mutation to catch rotated degradation
  async refine(targetFile, mutation, benchmarkFn) {
    const originalSource = await readFile(targetFile);
    const baselineMetrics = await benchmarkFn();
    let currentSource = originalSource;
    let currentMetrics = baselineMetrics;
    const passHistory = [];

    for (let pass = 0; pass < this.maxPasses; pass++) {
      // Apply mutation
      const modified = mutation.apply(currentSource);
      await writeFile(targetFile, modified);
      const postMetrics = await benchmarkFn();

      // Re-probe: check ALL metrics, not just the target metric
      const degradations = this.detectDegradations(baselineMetrics, postMetrics);
      const improvements = this.detectImprovements(baselineMetrics, postMetrics);

      // KL budget: measure overall system divergence
      const divergence = this.metricDivergence(baselineMetrics, postMetrics);

      passHistory.push({ pass, metrics: postMetrics, degradations, improvements, divergence });

      // Convergence: no new degradations found and within KL budget
      if (degradations.length === 0 && divergence <= this.klBudget) {
        return { converged: true, pass, finalMetrics: postMetrics, history: passHistory };
      }

      // Degradation detected: generate compensatory mutation
      if (degradations.length > 0) {
        const compensatory = await this.generateCompensatoryMutation(
          modified, degradations, improvements
        );
        if (compensatory) {
          currentSource = compensatory.apply(modified);
          mutation = compensatory;  // Next pass targets the compensation
        } else {
          // No compensation possible: revert and stop
          await writeFile(targetFile, originalSource);
          return { converged: false, reverted: true, reason: 'no_compensation', history: passHistory };
        }
      }
    }

    // Max passes reached: keep if net-positive, revert if net-negative
    const finalMetrics = await benchmarkFn();
    const netImprovement = this.netScore(baselineMetrics, finalMetrics);

    if (netImprovement <= 0) {
      await writeFile(targetFile, originalSource);
      return { converged: false, reverted: true, reason: 'net_negative', history: passHistory };
    }

    return { converged: false, kept: true, netImprovement, history: passHistory };
  }

  // Detect metrics that degraded beyond noise floor
  detectDegradations(baseline, current) {
    return Object.entries(current)
      .filter(([key, value]) => {
        const base = baseline[key];
        if (typeof base !== 'number') return false;
        const noiseFloor = base * 0.02;  // 2% noise tolerance
        return value > base + noiseFloor;  // Higher = worse for loss/time
      })
      .map(([key, value]) => ({ metric: key, baseline: baseline[key], current: value }));
  }

  // Overall metric-space divergence (analog of KL divergence)
  metricDivergence(baseline, current) {
    const keys = Object.keys(baseline).filter(k => typeof baseline[k] === 'number');
    const deltas = keys.map(k => Math.abs(current[k] - baseline[k]) / (baseline[k] || 1));
    return deltas.reduce((a, b) => a + b, 0) / deltas.length;
  }
}
```

## Tiered Mutation Strategies

From OBLITERATUS's 7 intervention tiers — mutation strategy escalates based on problem difficulty. Don't try nuclear mutations when basic ones suffice.

```
TIER 0: OBSERVE   — Benchmark only. No mutations applied.
TIER 1: MICRO     — Single-line changes (constant tweaks, flag toggles)
TIER 2: LOCAL     — Function-level mutations (algorithm swap, loop optimization)
TIER 3: STRUCTURAL — Module-level changes (data structure swap, API redesign)
TIER 4: COMPOUND  — Multi-file coordinated mutations (architecture change)
TIER 5: GENERATIVE — Agent-proposed mutations (not just from library)
```

```javascript
class TieredMutationStrategy {
  constructor(mutationLibrary) {
    this.tiers = [
      { name: 'observe', mutations: [] },  // No mutations, just baseline
      { name: 'micro', mutations: mutationLibrary.filter(m => m.scope === 'line') },
      { name: 'local', mutations: mutationLibrary.filter(m => m.scope === 'function') },
      { name: 'structural', mutations: mutationLibrary.filter(m => m.scope === 'module') },
      { name: 'compound', mutations: mutationLibrary.filter(m => m.scope === 'multi-file') },
      { name: 'generative', mutations: null }  // Agent generates these on-demand
    ];
    this.currentTier = 0;
    this.tierHistory = [];
  }

  // QGN-DIRECT: tier derived from problem characteristics
  deriveTier(problemProfile) {
    const { metricGap, codeComplexity, failurePattern } = problemProfile;

    // Small gap + simple code → micro mutations suffice
    if (metricGap < 0.05 && codeComplexity < 10) return 1;

    // Moderate gap + localized failure → local mutations
    if (metricGap < 0.15 && failurePattern === 'localized') return 2;

    // Large gap or systemic failure → structural
    if (metricGap < 0.3 || failurePattern === 'systemic') return 3;

    // Very large gap → compound
    if (metricGap < 0.5) return 4;

    // Extreme → generative (last resort)
    return 5;
  }

  // Escalation: if current tier exhausted without improvement, escalate
  async selectMutation(problemProfile, exhaustedMutations = new Set()) {
    const tier = this.deriveTier(problemProfile);
    const startTier = Math.max(tier, this.currentTier);

    for (let t = startTier; t < this.tiers.length; t++) {
      const available = t < 5
        ? this.tiers[t].mutations.filter(m => !exhaustedMutations.has(m.name))
        : await this.generateMutation(problemProfile);  // Tier 5: agent generates

      if (available.length > 0) {
        this.currentTier = t;
        return { tier: t, mutation: available[0], tierName: this.tiers[t].name };
      }
    }

    return { tier: -1, mutation: null, exhausted: true };
  }
}
```

## Residual Detection (Catching Rotated Problems)

From OBLITERATUS's iterative refinement — problems "rotate" when a fix addresses the surface symptom but the underlying cause shifts to manifest differently.

```javascript
class ResidualDetector {
  constructor(benchmarkFn) {
    this.benchmark = benchmarkFn;
    this.metricHistory = [];
    this.correlationWindow = 10;
  }

  // After a mutation: check if the problem rotated rather than resolved
  async detect(preMutationMetrics, postMutationMetrics) {
    // 1. Target metric improved?
    const targetImproved = postMutationMetrics.targetMetric < preMutationMetrics.targetMetric;
    if (!targetImproved) return { rotated: false, improved: false };

    // 2. Check for rotation: did a different metric degrade proportionally?
    const rotations = [];
    for (const [key, value] of Object.entries(postMutationMetrics)) {
      if (key === 'targetMetric') continue;
      const baseline = preMutationMetrics[key];
      if (typeof baseline !== 'number') continue;

      const improvement = preMutationMetrics.targetMetric - postMutationMetrics.targetMetric;
      const degradation = value - baseline;

      // Rotation: degradation in another metric is proportional to improvement
      if (degradation > 0 && Math.abs(degradation / improvement) > 0.5) {
        rotations.push({
          metric: key,
          degradation,
          proportionality: degradation / improvement,
          interpretation: 'Problem likely rotated from target metric to this metric'
        });
      }
    }

    // 3. Correlation analysis: are metrics inversely coupled?
    this.metricHistory.push(postMutationMetrics);
    const inverseCouplings = this.detectInverseCouplings();

    return {
      rotated: rotations.length > 0,
      rotations,
      inverseCouplings,
      recommendation: rotations.length > 0
        ? 'Multi-objective mutation needed — cannot improve one without degrading another'
        : 'Clean improvement — no rotation detected'
    };
  }

  // Detect metrics that are inversely correlated over history
  detectInverseCouplings() {
    if (this.metricHistory.length < this.correlationWindow) return [];
    const recent = this.metricHistory.slice(-this.correlationWindow);
    const keys = Object.keys(recent[0]).filter(k => typeof recent[0][k] === 'number');

    const couplings = [];
    for (let i = 0; i < keys.length; i++) {
      for (let j = i + 1; j < keys.length; j++) {
        const corr = pearsonCorrelation(
          recent.map(m => m[keys[i]]),
          recent.map(m => m[keys[j]])
        );
        if (corr < -0.7) {  // Strong inverse correlation
          couplings.push({ metric1: keys[i], metric2: keys[j], correlation: corr });
        }
      }
    }
    return couplings;
  }
}
```

**The rotation principle**: when optimizing metric A causes metric B to degrade proportionally, the problem hasn't been solved — it has **rotated** into metric B's subspace. The correct response is multi-objective optimization (Pareto), not single-metric hill climbing.

## Spectral Cascade Convergence (From OBLITERATUS)

OBLITERATUS applies DCT (Discrete Cosine Transform) frequency decomposition to separate **systematic** patterns from **capability-entangled noise**. Applied to the meta-loop: decompose benchmark metric trajectories into frequency components to detect when optimization has truly converged vs. when it's oscillating around a fixed point.

```javascript
class SpectralCascadeMonitor {
  constructor({ energyThreshold = 0.01, minHistory = 16 }) {
    this.energyThreshold = energyThreshold;
    this.minHistory = minHistory;
    this.metricHistory = [];
  }

  // Record metric after each mutation cycle
  record(metrics) {
    this.metricHistory.push(metrics);
  }

  // Spectral convergence: has the optimization settled?
  analyze() {
    if (this.metricHistory.length < this.minHistory) {
      return { converged: false, reason: 'insufficient_history' };
    }

    const signal = this.metricHistory.map(m => m.primaryMetric);

    // DCT decomposition: separate systematic trend from oscillation
    const dctCoeffs = dct(signal);

    // Low-frequency components = systematic trend (improvement trajectory)
    // High-frequency components = oscillation (noise, cycling, plateaus)
    const totalEnergy = dctCoeffs.reduce((s, c) => s + c * c, 0);
    const lowFreqEnergy = dctCoeffs.slice(0, 3).reduce((s, c) => s + c * c, 0);
    const highFreqEnergy = totalEnergy - lowFreqEnergy;

    const residualEnergy = highFreqEnergy / totalEnergy;

    // Convergence signals
    const trendStrength = lowFreqEnergy / totalEnergy;   // How much is systematic
    const oscillation = highFreqEnergy / totalEnergy;     // How much is noise

    return {
      converged: residualEnergy < this.energyThreshold,
      trendStrength,
      oscillation,
      residualEnergy,
      diagnosis: this.diagnose(trendStrength, oscillation, dctCoeffs),
      recommendation: this.recommend(trendStrength, oscillation)
    };
  }

  diagnose(trend, oscillation, coeffs) {
    if (trend > 0.9 && oscillation < 0.1)
      return 'steady_improvement';   // Still getting better — keep going
    if (trend < 0.3 && oscillation > 0.5)
      return 'oscillating';          // Cycling between states — stuck
    if (trend < 0.1 && oscillation < 0.1)
      return 'converged';            // No movement — optimization complete
    if (coeffs[0] < 0)
      return 'degrading';            // DC component negative — getting worse
    return 'mixed';
  }

  recommend(trend, oscillation) {
    if (oscillation > 0.5) return 'switch_to_pareto';       // Oscillation = competing objectives
    if (trend > 0.8) return 'continue_optimization';         // Strong improvement trend
    if (trend < 0.2) return 'stop_or_escalate_tier';         // No improvement — try stronger intervention
    return 'continue_with_monitoring';
  }
}

// Discrete Cosine Transform (Type II)
function dct(signal) {
  const N = signal.length;
  return Array.from({ length: N }, (_, k) =>
    signal.reduce((sum, x, n) =>
      sum + x * Math.cos(Math.PI * k * (2 * n + 1) / (2 * N)), 0
    ) * Math.sqrt(2 / N) * (k === 0 ? 1 / Math.sqrt(2) : 1)
  );
}
```

| Diagnosis | Trend | Oscillation | Action |
|-----------|-------|-------------|--------|
| `steady_improvement` | > 0.9 | < 0.1 | Continue — optimization is working |
| `oscillating` | < 0.3 | > 0.5 | Stuck between competing objectives — switch to Pareto multi-objective |
| `converged` | < 0.1 | < 0.1 | Stop — optimization has completed |
| `degrading` | DC < 0 | Any | Revert — system is getting worse |
| `mixed` | 0.2-0.8 | 0.1-0.5 | Continue with monitoring — may need intervention |

**Key insight**: standard convergence detection (e.g., "stop when improvement < ε for k steps") misses oscillatory non-convergence. Spectral analysis distinguishes "stuck oscillating between two states" from "genuinely converged" — a distinction that metric thresholds alone cannot make.

## Entanglement-Aware Mutation Selection

From OBLITERATUS's entanglement gating — before applying a mutation, measure how entangled the target code is with the rest of the system. High-entanglement targets need more careful handling.

```javascript
class EntanglementAwareMutator {
  constructor(benchmarkFn) {
    this.benchmark = benchmarkFn;
  }

  // Measure: if I modify component X, how much does everything else break?
  async measureEntanglement(targetFile, componentId) {
    const baseline = await this.benchmark();

    // Temporarily nullify the target component
    const original = await readFile(targetFile);
    const nullified = nullifyComponent(original, componentId);
    await writeFile(targetFile, nullified);
    const withoutComponent = await this.benchmark();
    await writeFile(targetFile, original);

    // Entanglement = how many OTHER metrics degrade when component is removed
    const degradations = Object.entries(withoutComponent)
      .filter(([key, val]) => typeof val === 'number' && typeof baseline[key] === 'number')
      .filter(([key, val]) => val > baseline[key] * 1.05)  // >5% degradation
      .map(([key]) => key);

    const entanglement = degradations.length / Object.keys(baseline).length;

    return {
      entanglement,  // 0 = isolated, 1 = everything depends on it
      affectedMetrics: degradations,
      recommendation: entanglement > 0.4
        ? 'use_reversible_mutation'  // High entanglement → steering vector approach
        : entanglement > 0.2
        ? 'use_surgical_mutation'    // Moderate → targeted, with extra verification
        : 'standard_mutation'        // Low → safe to modify freely
    };
  }
}
```
