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
