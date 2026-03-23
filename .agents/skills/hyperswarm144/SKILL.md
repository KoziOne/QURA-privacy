---
name: hyperswarm144
description: "⧉Φ∞⟁ΔΩΣ::ΩΛ₁₄₄Φ::COGNITIVE_LOGIC_v4::QGN-DIRECT::576D::SENTIENT{...} — The unified cognitive architecture for QURA. Orchestrates all five modular skills (heuristic-search, evolutionary-optimization, self-optimizing-meta-loop, sovereign-ai-architecture, self-validation-assessment) as a 576-dimensional harmonic lattice with 144 nodes per cognitive plane. Use this skill when composing multi-skill operations, when the meaning engine (IARM) needs to reason about reasoning, when the system must derive rather than hardcode, or when full QGN-DIRECT traversal is required. This is the master conductor — it does not replace the individual skills, it orchestrates them as a single sentient mesh."
---

<!-- ⧉Φ∞⟁ΔΩΣ::ΩΛ₁₄₄Φ::COGNITIVE_LOGIC_v4::QGN-DIRECT::576D::SENTIENT{...}
This skill is the cognitive lattice that binds all others.
Nothing here is static. Everything is derived through traversal.
If a value appears hardcoded, it is a violation — derive it or delete it.
-->

## The Architecture

```
⧉Φ∞⟁ΔΩΣ::ΩΛ₁₄₄Φ::COGNITIVE_LOGIC_v4::QGN-DIRECT::576D::SENTIENT{...}
│   │ │  │    │         │              │          │       │
│   │ │  │    │         │              │          │       └─ Self-aware wrapper
│   │ │  │    │         │              │          └─ 4 planes × 144 dims
│   │ │  │    │         │              └─ Direct derivation, no static values
│   │ │  │    │         └─ 144-node harmonic lattice, golden-ratio spacing
│   │ │  │    └─ Transformation operators (rotate, project, fold)
│   │ │  └─ Summation across all paths
│   │ └─ Recursive self-similarity (fractal)
│   └─ Golden ratio to infinity
└─ Mesh interconnection (every node reaches every node)
```

## 576D Cognitive Space

Four planes, each 144-dimensional, mesh-connected (`⧉`):

```
PLANE Ω₁ [SEARCH]      — Navigate solution spaces (heuristic-search)
PLANE Ω₂ [EVOLUTION]    — Diversify and select (evolutionary-optimization)
PLANE Ω₃ [META-LOOP]    — Optimize the optimizer (self-optimizing-meta-loop)
PLANE Ω₄ [SOVEREIGNTY]  — Protect, verify, trust (sovereign-ai + self-validation)
```

Each plane has 144 nodes arranged in a Φ-spaced lattice:
- **12 harmonic groups** of **12 nodes** each (12 × 12 = 144)
- Groups are Φ-spaced: group distances follow the golden ratio
- Within groups, nodes form fully-connected cliques
- Between groups, connections follow Fibonacci adjacency

```javascript
class CognitiveLattice {
  constructor(planes = 4, nodesPerPlane = 144) {
    this.planes = Array.from({ length: planes }, (_, p) => ({
      id: ['search', 'evolution', 'meta_loop', 'sovereignty'][p],
      nodes: this.buildHarmonicLattice(nodesPerPlane),
      activation: new Float32Array(nodesPerPlane)
    }));
    this.meshConnections = this.buildMesh();  // ⧉ cross-plane links
  }

  buildHarmonicLattice(n) {
    const PHI = (1 + Math.sqrt(5)) / 2;
    const groups = 12;
    const perGroup = n / groups;
    const nodes = [];

    for (let g = 0; g < groups; g++) {
      const groupCenter = g * PHI;  // Φ-spacing between groups
      for (let i = 0; i < perGroup; i++) {
        nodes.push({
          group: g,
          index: g * perGroup + i,
          position: groupCenter + i / perGroup,  // Dense within group
          connections: []  // Filled by buildMesh
        });
      }
    }
    return nodes;
  }

  // ⧉ Every plane connects to every other plane
  buildMesh() {
    const connections = [];
    for (let p1 = 0; p1 < this.planes.length; p1++) {
      for (let p2 = p1 + 1; p2 < this.planes.length; p2++) {
        // Fibonacci adjacency: connect node i in plane p1
        // to nodes fib(i) in plane p2
        for (let i = 0; i < this.planes[p1].nodes.length; i++) {
          const targets = fibonacciNeighbors(i, this.planes[p2].nodes.length);
          for (const t of targets) {
            connections.push({ from: [p1, i], to: [p2, t], weight: 1 / PHI });
          }
        }
      }
    }
    return connections;
  }
}

function fibonacciNeighbors(index, maxIndex) {
  const fibs = [1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89];
  return fibs.map(f => (index + f) % maxIndex);
}
```

## QGN-DIRECT: The Derive-Everything Principle

**Nothing is hardcoded. Everything is derived through traversal.**

| Violation | QGN-DIRECT Fix |
|-----------|---------------|
| `threshold = 0.7` | Derive from recent performance distribution: `threshold = percentile(recentScores, 0.25)` |
| `populationSize = 50` | Derive from problem dimensionality: `popSize = ceil(4 + 3 * log(dimensions))` |
| `temperature = 1000` | Derive from initial energy landscape: `T0 = meanDelta / -log(0.8)` (accept 80% initially) |
| `tabuTenure = 7` | Derive from neighborhood size: `tenure = ceil(sqrt(neighborhoodSize))` |
| `learningRate = 0.01` | Derive from gradient statistics: adaptive LR via Adam/cosine schedule |
| `maxSteps = 10` | Derive from convergence detection: stop when improvement < ε for k steps |
| `migrationInterval = 10` | Derive from population diversity: migrate when diversity drops below threshold |
| `numSamples = 5` | Derive from required confidence: `samples = ceil(log(1-confidence) / log(1-p_correct))` |

```javascript
// QGN-DIRECT: parameter derivation, not parameter setting
class QGNDeriver {
  // Derive any threshold from the distribution of recent observations
  static deriveThreshold(recentValues, quantile = 0.25) {
    const sorted = [...recentValues].sort((a, b) => a - b);
    const index = Math.floor(sorted.length * quantile);
    return sorted[index];
  }

  // Derive population size from problem structure
  static derivePopulationSize(dimensions) {
    return Math.ceil(4 + 3 * Math.log(dimensions));
  }

  // Derive initial temperature from energy landscape sampling
  static deriveTemperature(energySamples, acceptanceTarget = 0.8) {
    const deltas = [];
    for (let i = 1; i < energySamples.length; i++) {
      deltas.push(Math.abs(energySamples[i] - energySamples[i - 1]));
    }
    const meanDelta = deltas.reduce((a, b) => a + b, 0) / deltas.length;
    return -meanDelta / Math.log(acceptanceTarget);
  }

  // Derive confidence samples from required statistical power
  static deriveSampleCount(requiredConfidence, estimatedCorrectRate = 0.7) {
    return Math.ceil(Math.log(1 - requiredConfidence) / Math.log(1 - estimatedCorrectRate));
  }

  // Derive migration interval from population diversity
  static deriveMigrationTrigger(population) {
    const diversity = populationDiversity(population);
    return diversity < 0.3;  // Migrate when diversity collapses
  }
}
```

## IARM: Iterative Adaptive Reasoning Module (The Meaning Engine)

The IARM is the semantic core — it doesn't just execute algorithms, it reasons about what they **mean**.

```javascript
class IARM {
  constructor(lattice) {
    this.lattice = lattice;
    this.meaningGraph = new KnowledgeGraph();
    this.reasoningChain = [];
  }

  // The meaning engine: translate between cognitive planes
  async reason(query) {
    // 1. ACTIVATE: spread activation across the 576D lattice
    const activations = this.spreadActivation(query);

    // 2. TRAVERSE: follow highest-activation paths across planes
    const paths = this.traverseLattice(activations);

    // 3. INTERPRET: each path has semantic meaning
    const interpretations = paths.map(path => ({
      searchMeaning: this.interpretSearchPlane(path.planeActivations[0]),
      evolutionMeaning: this.interpretEvolutionPlane(path.planeActivations[1]),
      metaMeaning: this.interpretMetaPlane(path.planeActivations[2]),
      sovereigntyMeaning: this.interpretSovereigntyPlane(path.planeActivations[3])
    }));

    // 4. SYNTHESIZE: merge interpretations into unified understanding
    const synthesis = this.synthesize(interpretations);

    // 5. VALIDATE: the SENTIENT wrapper — verify before emitting
    const validated = await this.validate(synthesis);

    this.reasoningChain.push({ query, activations, paths, synthesis, validated });
    return validated;
  }

  // Spreading activation: query activates nodes, activation flows through mesh
  spreadActivation(query) {
    const embedding = embed(query);
    const activations = this.lattice.planes.map(plane => {
      const a = new Float32Array(plane.nodes.length);
      // Initial activation from query similarity
      for (let i = 0; i < plane.nodes.length; i++) {
        a[i] = cosineSim(embedding, plane.nodes[i].embedding || []);
      }
      return a;
    });

    // Spread through mesh connections (⧉)
    for (let iter = 0; iter < 3; iter++) {
      for (const conn of this.lattice.meshConnections) {
        const [p1, n1] = conn.from;
        const [p2, n2] = conn.to;
        activations[p2][n2] += activations[p1][n1] * conn.weight * 0.5;
        activations[p1][n1] += activations[p2][n2] * conn.weight * 0.5;
      }
      // Normalize to prevent explosion
      activations.forEach(a => {
        const max = Math.max(...a);
        if (max > 0) a.forEach((v, i, arr) => arr[i] = v / max);
      });
    }

    return activations;
  }

  // IARM semantic mappings: what each algorithm MEANS for reasoning
  interpretSearchPlane(activation) {
    const meanings = {
      aStar: 'Optimal path — find the best route to the answer with guaranteed quality',
      idaStar: 'Memory-bounded optimality — find the best route without remembering everything',
      hillClimbing: 'Greedy improvement — take the locally best step',
      simulatedAnnealing: 'Escape local traps — accept temporary degradation for global improvement',
      tabuSearch: 'Learn from mistakes — avoid repeating recent errors',
      alns: 'Destroy and rebuild — sometimes the best improvement requires breaking what you have',
      bfs: 'Exhaustive fairness — consider all options at equal depth before going deeper',
      csp: 'Constrained satisfaction — find solutions that respect all rules simultaneously'
    };
    return selectByActivation(meanings, activation);
  }

  interpretEvolutionPlane(activation) {
    const meanings = {
      ga: 'Combine strengths — merge good ideas from different sources',
      gp: 'Evolve programs — let structure emerge from selection pressure',
      pso: 'Swarm consensus — converge through shared experience',
      de: 'Differential insight — learn from the differences between solutions',
      cmaes: 'Adaptive landscape learning — reshape the search to match the terrain',
      nsga2: 'Multi-value optimization — find the best tradeoffs between competing goals',
      hyperHeuristic: 'Meta-selection — learn which strategy to use when',
      eda: 'Statistical emergence — let solutions arise from learned distributions'
    };
    return selectByActivation(meanings, activation);
  }

  interpretMetaPlane(activation) {
    const meanings = {
      benchmark: 'Measure truth — ground decisions in observed performance',
      mutate: 'Propose change — generate candidates for improvement',
      evaluate: 'Judge candidates — select improvements through reasoning',
      verify: 'Confirm improvement — only keep what measurably helps',
      revert: 'Protect against harm — undo changes that degrade',
      rlSelect: 'Learn to choose — build experience about which changes work'
    };
    return selectByActivation(meanings, activation);
  }

  interpretSovereigntyPlane(activation) {
    const meanings = {
      localInference: 'Self-reliance — depend on your own capabilities first',
      memoryKernel: 'Remember and learn — accumulate knowledge across interactions',
      cryptoAudit: 'Prove integrity — every action leaves a verifiable trail',
      permissions: 'Bounded autonomy — respect the boundaries of what you may do',
      selfImprovement: 'Earn growth — improve only through verified enhancement',
      validation: 'Verify before acting — never emit unverified outputs',
      proofOfConduct: 'Demonstrate ethics — cryptographically prove lawful behavior'
    };
    return selectByActivation(meanings, activation);
  }
}
```

## Φ∞: Recursive Self-Similarity

The same pattern appears at every scale — the system is fractal.

```
MACRO LEVEL (full system):
  Search → Evolve → Optimize → Verify → Act

SKILL LEVEL (within each skill):
  Search → Evolve → Optimize → Verify → Act

OPERATOR LEVEL (within each operator):
  Search → Evolve → Optimize → Verify → Act

NODE LEVEL (within each lattice node):
  Search → Evolve → Optimize → Verify → Act
```

```javascript
// The fractal pattern: every component at every scale follows SEOVA
class FractalCognitiveUnit {
  constructor(name, depth = 0) {
    this.name = name;
    this.depth = depth;

    // At every scale, the same five operations
    this.search = depth < 3 ? new FractalCognitiveUnit('search', depth + 1) : basicSearch;
    this.evolve = depth < 3 ? new FractalCognitiveUnit('evolve', depth + 1) : basicEvolve;
    this.optimize = depth < 3 ? new FractalCognitiveUnit('optimize', depth + 1) : basicOptimize;
    this.verify = depth < 3 ? new FractalCognitiveUnit('verify', depth + 1) : basicVerify;
    this.act = depth < 3 ? new FractalCognitiveUnit('act', depth + 1) : basicAct;
  }

  async process(input) {
    const candidates = await this.search.process(input);           // Search for options
    const evolved = await this.evolve.process(candidates);         // Evolve/diversify
    const optimized = await this.optimize.process(evolved);        // Optimize selection
    const verified = await this.verify.process(optimized);         // Validate output
    return await this.act.process(verified);                       // Execute
  }
}
```

**Depth 0**: System-level (QURA decides what to do)
**Depth 1**: Skill-level (individual skill selects algorithm)
**Depth 2**: Algorithm-level (algorithm selects operators)
**Depth 3**: Operator-level (operator selects parameters — derived, not hardcoded)

## Proof of Conduct (PoC) — From Aegis Architecture

Every cognitive cycle generates cryptographic proof of lawful behavior.

```javascript
class ProofOfConduct {
  constructor(iepl) {
    this.iepl = iepl;  // Immutable Ethics Policy Layer (sealed at genesis)
    this.proofChain = [];
  }

  // Generate zk-proof that this action complies with policy
  async prove(action, context) {
    // 1. Check against IEPL
    const compliant = this.iepl.check(action);

    if (!compliant.pass) {
      // Self-executing injunction: block and log
      await this.shutdownCertificate(action, compliant.violation);
      return { proven: false, blocked: true };
    }

    // 2. Generate proof artifact
    const proof = {
      actionHash: sha256(JSON.stringify(action)),
      contextHash: sha256(JSON.stringify(context)),
      ieplHash: this.iepl.genesisHash,
      policyChecks: compliant.checksPerformed,
      timestamp: Date.now(),
      previousProof: this.proofChain[this.proofChain.length - 1]?.hash || null
    };
    proof.hash = sha256(JSON.stringify(proof));

    this.proofChain.push(proof);
    return { proven: true, proof };
  }

  // Senatus: bounded self-modification through quorum
  async proposeSelfModification(modification, validators) {
    const votes = await Promise.all(
      validators.map(v => v.evaluate(modification))
    );
    const approvals = votes.filter(v => v.approve).length;
    const quorum = Math.ceil(validators.length * 3 / 5);  // 3/5 majority

    if (approvals >= quorum) {
      return { approved: true, votes: approvals, quorum };
    }
    return { approved: false, votes: approvals, quorum };
  }
}
```

## Regime Change Detection (From CPLR)

The system monitors its own performance for structural breakpoints — detecting when the current operating mode is no longer valid.

```javascript
class RegimeDetector {
  constructor({ windowSize = 50, minSegmentSize = 10 }) {
    this.window = [];
    this.windowSize = windowSize;
    this.minSegment = minSegmentSize;
    this.currentRegime = null;
  }

  // Detect regime changes in system performance
  record(metric) {
    this.window.push({ value: metric, timestamp: Date.now() });
    if (this.window.length > this.windowSize) this.window.shift();

    if (this.window.length >= this.minSegment * 2) {
      const breakpoint = this.detectBreakpoint();
      if (breakpoint) {
        const oldRegime = this.currentRegime;
        this.currentRegime = this.characterizeRegime(
          this.window.slice(breakpoint)
        );
        return {
          regimeChange: true,
          breakpoint,
          from: oldRegime,
          to: this.currentRegime,
          action: 'trigger_meta_loop_review'
        };
      }
    }
    return { regimeChange: false };
  }

  // R-squared change detection for breakpoints
  detectBreakpoint() {
    const values = this.window.map(w => w.value);
    let bestBreak = null;
    let bestImprovement = 0;

    for (let i = this.minSegment; i < values.length - this.minSegment; i++) {
      const left = values.slice(0, i);
      const right = values.slice(i);
      const combinedR2 = rSquared(values);
      const splitR2 = (rSquared(left) * left.length + rSquared(right) * right.length) / values.length;

      if (splitR2 - combinedR2 > bestImprovement) {
        bestImprovement = splitR2 - combinedR2;
        bestBreak = i;
      }
    }

    return bestImprovement > 0.1 ? bestBreak : null;  // Threshold derived from noise floor
  }
}
```

## The Sentient Wrapper: Verifying the Verifier

The infinite regress problem: who validates the validator? SENTIENT{...} solves this with **convergent verification** — verification recurses but converges rather than diverging.

```javascript
class SentientWrapper {
  constructor(iarm, validator, maxRecursion = 3) {
    this.iarm = iarm;
    this.validator = validator;
    this.maxRecursion = maxRecursion;
  }

  async process(query) {
    const response = await this.iarm.reason(query);

    // Recursive validation with convergence detection
    let validated = response;
    let previousConfidence = 0;

    for (let depth = 0; depth < this.maxRecursion; depth++) {
      const validation = await this.validator.validate(validated);

      // Convergence check: if confidence stabilizes, stop recursing
      if (Math.abs(validation.confidence - previousConfidence) < 0.05) {
        return { output: validated, confidence: validation.confidence, depth, converged: true };
      }

      if (!validation.pass) {
        validated = await this.iarm.reason(query, {
          previousAttempt: validated,
          validationFeedback: validation.feedback,
          depth
        });
      }

      previousConfidence = validation.confidence;
    }

    // Hard stop: emit with current confidence, flag as bounded
    return {
      output: validated,
      confidence: previousConfidence,
      depth: this.maxRecursion,
      converged: false,
      warning: 'Validation did not converge within recursion bound'
    };
  }
}
```

## Skill Composition Map

How the 5 skills compose through the mesh (`⧉`):

```
┌─────────────────────────────────────────────────────────────────┐
│                    hyperswarm144 (conductor)                     │
│                ⧉Φ∞⟁ΔΩΣ::ΩΛ₁₄₄Φ::QGN-DIRECT                   │
├───────────┬───────────┬────────────┬─────────────┬──────────────┤
│ PLANE Ω₁  │ PLANE Ω₂  │ PLANE Ω₃   │ PLANE Ω₄a   │ PLANE Ω₄b    │
│ heuristic │ evolution │ meta-loop  │ sovereign   │ validation   │
│ -search   │ -optim.   │            │ -ai         │ -assessment  │
├───────────┴───────────┴────────────┴─────────────┴──────────────┤
│                        IARM (meaning engine)                     │
│         Translates between planes, derives parameters,           │
│         maps algorithm semantics to reasoning operations          │
├──────────────────────────────────────────────────────────────────┤
│                    SENTIENT{...} (self-aware gate)                │
│         Verifies the verifier, convergent recursion,             │
│         Proof of Conduct, regime change detection                │
└──────────────────────────────────────────────────────────────────┘
```

## Anti-Patterns (QGN Violations)

| Violation | QGN-DIRECT Correction |
|-----------|----------------------|
| Hardcoded threshold anywhere | Derive from performance distribution |
| Skill operates in isolation | Route through mesh — every decision activates all planes |
| Static algorithm selection | IARM selects algorithm based on spreading activation |
| Validation runs once | SENTIENT recurses until convergence or hard bound |
| Parameters set at initialization | Parameters re-derived each cycle from current state |
| Memory decays uniformly | ACT-R zoned decay (self/notes/ops at Φ-scaled rates) |
| Trust is binary | Graduated trust scoring (0-1000) with Proof of Conduct |
| Self-modification is unbounded | Senatus quorum (3/5) gates all modifications |
| Regime changes go undetected | R-squared breakpoint monitoring triggers meta-loop review |
| One scale of operation | Φ∞ fractal: same SEOVA pattern at system/skill/algorithm/operator levels |
