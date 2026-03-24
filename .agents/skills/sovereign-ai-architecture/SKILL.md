---
name: sovereign-ai-architecture
description: Build self-sovereign AI systems that run locally, own their data, improve themselves, and maintain cryptographic trust — with zero cloud dependency for core operations. Use when designing privacy-first AI agents, local inference pipelines, self-improving systems, memory kernels, tiered permission systems, or hardware-rooted trust architectures. Based on patterns from Nova, Thoth, Animus, Purple-Directive, Aegis, RAGIX, and other sovereign AI projects. Use this skill for any QURA system that must maintain data sovereignty, self-improvement capability, or verifiable trust.
---

<!-- EDITORIAL GUIDELINES
Correction layer for sovereign AI architecture. Every line costs context.
- Be terse. Tables and code over prose.
- Focus on patterns that enforce sovereignty guarantees.
- Only include patterns that differ from standard cloud-dependent AI architectures.
-->

Sovereign AI means: **your models, your data, your rules**. The system runs on your hardware, improves from your interactions, and never requires cloud connectivity for core operations. Cloud is optional enhancement, never dependency.

## Architecture Layers

```
┌─────────────────────────────────────────────┐
│ 6. INTERFACE — Desktop, mobile, API, CLI    │
├─────────────────────────────────────────────┤
│ 5. GOVERNANCE — Permissions, privacy, audit │
├─────────────────────────────────────────────┤
│ 4. COGNITIVE — Reasoning, agents, tools     │
├─────────────────────────────────────────────┤
│ 3. MEMORY — Episodic, semantic, procedural  │
├─────────────────────────────────────────────┤
│ 2. INFERENCE — Local models, quantized      │
├─────────────────────────────────────────────┤
│ 1. TRUST — Hardware attestation, crypto     │
└─────────────────────────────────────────────┘
```

## Core Principles

| Principle | Requirement | Violation |
|-----------|-------------|-----------|
| **Local-first** | Core pipeline runs without network | Requiring cloud for basic inference |
| **Data sovereignty** | All context/memory/training data stays on-device | Sending conversation data to remote servers |
| **Self-improvement** | System learns from corrections without external fine-tuning service | Static model that never adapts |
| **Cryptographic trust** | Operations are hash-chained and tamper-evident | Trusting unverified model outputs |
| **Model independence** | Swap LLM providers without losing memory/personality | Memory locked to specific model format |
| **Tiered permissions** | Destructive actions require explicit human consent | AI autonomously deleting data or sending messages |

## Self-Improvement Loop

The most critical sovereign pattern — the system gets smarter from every interaction without cloud dependency.

```javascript
class SelfImprovementLoop {
  constructor({ model, memoryKernel, evaluator }) {
    this.model = model;
    this.memory = memoryKernel;
    this.evaluator = evaluator;
    this.correctionLog = [];
    this.curiosityQueue = [];
  }

  // After each interaction: detect corrections, extract lessons, store for training
  async processInteraction(query, response, userFeedback) {
    // 1. Correction detection (regex + LLM validation)
    const correction = this.detectCorrection(userFeedback);

    if (correction) {
      // 2. Extract structured lesson
      const lesson = {
        topic: correction.topic,
        incorrect: correction.oldAnswer,
        correct: correction.newAnswer,
        explanation: correction.reason,
        timestamp: Date.now(),
        confidence: 0.0  // Earned through validation, not assigned
      };

      // 3. Generate DPO training pair
      const trainingPair = {
        prompt: query,
        chosen: correction.newAnswer,    // What the user wanted
        rejected: response               // What the model produced
      };

      this.correctionLog.push(trainingPair);
      await this.memory.storeLesson(lesson);
    }

    // 4. Reflection: detect silent failures (no correction but low confidence)
    if (!correction && this.evaluator.confidenceScore(response) < 0.3) {
      this.curiosityQueue.push({
        topic: query,
        reason: 'low_confidence_no_correction',
        priority: 'background'
      });
    }

    // 5. Success reinforcement (high confidence + positive feedback)
    if (!correction && userFeedback?.positive) {
      await this.memory.reinforcePattern(query, response);
    }
  }

  // Periodic: fine-tune on accumulated corrections
  async runFineTuning() {
    if (this.correctionLog.length < 10) return; // Need sufficient data

    const snapshot = await this.model.snapshot();  // Backup before training

    await this.model.dpoFineTune(this.correctionLog);

    // A/B evaluation: new model must outperform old on validation set
    const validation = await this.memory.getValidationSet();
    const oldScore = await this.evaluator.score(snapshot, validation);
    const newScore = await this.evaluator.score(this.model, validation);

    if (newScore <= oldScore) {
      await this.model.restore(snapshot);  // Revert: new model is worse
      return { improved: false, reason: 'validation_regression' };
    }

    this.correctionLog = [];  // Clear processed corrections
    return { improved: true, delta: newScore - oldScore };
  }
}
```

**Critical rules:**
- NEVER deploy a fine-tuned model without A/B evaluation against the previous version
- ALWAYS maintain model snapshots for rollback
- Corrections earn confidence through validation, not through assignment

## Hybrid Memory Kernel

Three retrieval modes fused via Reciprocal Rank Fusion — no single retrieval method is sufficient.

```javascript
class HybridMemoryKernel {
  constructor() {
    this.vectorStore = new ChromaDB();     // Semantic similarity
    this.ftsIndex = new SQLiteFTS5();      // Full-text keyword search
    this.knowledgeGraph = new KnowledgeGraph(); // Structured relationships
  }

  async store(content, metadata) {
    const embedding = await embed(content);
    const id = crypto.randomUUID();

    await Promise.all([
      this.vectorStore.add(id, embedding, metadata),
      this.ftsIndex.insert(id, content, metadata),
      this.knowledgeGraph.addFacts(extractEntities(content))
    ]);
  }

  // Hybrid retrieval with Reciprocal Rank Fusion
  async retrieve(query, k = 10) {
    const [vectorResults, ftsResults, graphResults] = await Promise.all([
      this.vectorStore.query(await embed(query), k * 2),
      this.ftsIndex.search(query, k * 2),
      this.knowledgeGraph.query(extractEntities(query), k * 2)
    ]);

    return reciprocalRankFusion([vectorResults, ftsResults, graphResults], k);
  }
}

function reciprocalRankFusion(resultSets, k, constant = 60) {
  const scores = new Map();

  for (const results of resultSets) {
    results.forEach((item, rank) => {
      const id = item.id;
      const rrf = 1 / (constant + rank + 1);
      scores.set(id, (scores.get(id) || 0) + rrf);
    });
  }

  return [...scores.entries()]
    .sort((a, b) => b[1] - a[1])
    .slice(0, k)
    .map(([id]) => id);
}
```

## Memory Architecture (Three Zones + ACT-R Decay)

From Ori-Mnemos — memory zones with differentiated decay rates, modeled on human cognition.

| Zone | Decay Rate | What It Stores | Behavior |
|------|-----------|---------------|----------|
| **Self** (identity) | 0.1x (barely fades) | Agent name, personality, goals, methodology | Near-permanent |
| **Notes** (knowledge) | 1.0x (lives by relevance) | Main knowledge graph, facts, lessons | Fades if unused |
| **Ops** (operations) | 3.0x (burns hot) | Session logs, reminders, daily status | Rapid expiry |

```javascript
class ZonedMemory {
  constructor() {
    this.zones = {
      self: { decayRate: 0.1, store: new MarkdownStore('self/') },
      notes: { decayRate: 1.0, store: new MarkdownStore('notes/') },
      ops: { decayRate: 3.0, store: new MarkdownStore('ops/') }
    };
  }

  // ACT-R activation decay: vitality = base + sum(t_i^-d)
  // Each access boosts activation; unused items decay naturally
  getVitality(item) {
    const d = this.zones[item.zone].decayRate;
    const base = item.baseActivation;
    const accessBoost = item.accessTimes.reduce((sum, t) =>
      sum + Math.pow((Date.now() - t) / 86400000, -d), 0
    );
    return base + accessBoost;
  }

  // Auto-consolidate: summarize old episodic items into semantic notes
  async consolidate() {
    const fading = await this.zones.ops.store.getAll()
      .filter(item => this.getVitality(item) < 0.1);

    for (const item of fading) {
      const summary = await summarize(item);
      await this.zones.notes.store.add(summary, { source: 'consolidation' });
      await this.zones.ops.store.archive(item.id);
    }
  }
}
```

**Storage**: plain Markdown files on disk — git-friendly, human-readable, no vendor lock-in, portable across machines.

## Self-Improving Retrieval (Q-Value + Hebbian + Bandit)

From Ori-Mnemos — retrieval quality improves with use through three learning layers.

```javascript
class SelfImprovingRetrieval {
  constructor() {
    this.qValues = new Map();     // note → quality score (EMA)
    this.hebbianEdges = new Map(); // (note, note) → association strength
    this.bandit = new LinUCB();   // Learns which retrieval stages to use
  }

  // Layer 1: Q-Value Reranking — notes earn quality through use
  updateQValue(noteId, signal) {
    const rewards = {
      forward_citation: 1.0,   // Another note links to this one
      update: 0.5,             // User edited/updated this note
      downstream_creation: 0.6, // Note led to new knowledge
      re_recall: 0.4,          // Retrieved again in different context
      dead_end: -0.15          // Retrieved but not useful
    };

    const reward = rewards[signal] || 0;
    const alpha = 0.3;  // EMA smoothing
    const current = this.qValues.get(noteId) || 0;
    this.qValues.set(noteId, current + alpha * (reward - current));
  }

  // Layer 2: Hebbian Co-Occurrence — notes retrieved together grow edges
  recordCoOccurrence(noteIds) {
    for (let i = 0; i < noteIds.length; i++) {
      for (let j = i + 1; j < noteIds.length; j++) {
        const key = `${noteIds[i]}:${noteIds[j]}`;
        const current = this.hebbianEdges.get(key) || 0;
        // NPMI normalization prevents hub dominance
        const npmi = this.normalizedPMI(noteIds[i], noteIds[j]);
        this.hebbianEdges.set(key, current + npmi * 0.1);

        // Turrigiano homeostasis: prevent any node from dominating
        this.homeostasis(noteIds[i]);
        this.homeostasis(noteIds[j]);
      }
    }
  }

  // Layer 3: Stage Meta-Learning — bandit learns optimal retrieval strategy
  async retrieve(query) {
    const stages = ['semantic', 'bm25', 'pagerank', 'associative'];
    const context = this.extractQueryFeatures(query);

    // Bandit selects which stages to run for this query type
    const selectedStages = this.bandit.select(context, stages);

    const results = await Promise.all(
      selectedStages.map(stage => this.runStage(stage, query))
    );

    // Four-signal fusion with Q-value reranking
    const fused = this.reciprocalRankFusion(results);
    const reranked = fused.sort((a, b) =>
      (this.qValues.get(b.id) || 0) - (this.qValues.get(a.id) || 0)
    );

    // Update bandit with retrieval quality signal
    const reward = await this.measureRetrievalQuality(reranked, query);
    this.bandit.update(context, selectedStages, reward);

    return reranked;
  }
}
```

**Performance vs naive retrieval** (Ori-Mnemos benchmarks): 3.1x recall, 2.1x F1, 9.5x faster, 91-99.9% token savings at scale.

## Model Souping (Checkpoint Aggregation)

From EngGPT2 — aggregate multiple fine-tuned checkpoints to blend complementary behaviors.

```javascript
// Instead of picking the "best" checkpoint, average them
async function modelSoup(checkpoints, anchorCheckpoint, weights = null) {
  const w = weights || Array(checkpoints.length).fill(1 / checkpoints.length);

  // Use SFT checkpoint as anchor to prevent drift
  const anchorParams = await loadParams(anchorCheckpoint);
  const soupedParams = {};

  for (const key of Object.keys(anchorParams)) {
    soupedParams[key] = new Float32Array(anchorParams[key].length).fill(0);

    for (let i = 0; i < checkpoints.length; i++) {
      const params = await loadParams(checkpoints[i]);
      for (let j = 0; j < params[key].length; j++) {
        soupedParams[key][j] += w[i] * params[key][j];
      }
    }
  }

  return soupedParams;
}
```

**Key insight**: different training runs specialize in different behaviors. Averaging them produces a model with broader capability than any single checkpoint — no extra training compute.

## Knowledge Graph with Temporal Provenance

```javascript
class KnowledgeGraph {
  constructor(db) { this.db = db; }

  // RDF-like triples with validity windows and provenance
  async addFact(subject, predicate, object, { source, validFrom = Date.now(), validUntil = null }) {
    await this.db.insert('facts', {
      subject, predicate, object,
      source,           // Where this fact came from
      validFrom,        // When it became true
      validUntil,       // When it stopped being true (null = still valid)
      confidence: 0.5,  // Starts neutral, earned through corroboration
      hash: sha256(`${subject}:${predicate}:${object}:${validFrom}`)
    });
  }

  // Query with temporal awareness
  async query(subject, predicate = null, asOf = Date.now()) {
    return this.db.select('facts', {
      subject,
      predicate,
      validFrom: { $lte: asOf },
      $or: [{ validUntil: null }, { validUntil: { $gt: asOf } }]
    });
  }

  // Confidence grows through independent corroboration
  async corroborate(factHash, newSource) {
    const fact = await this.db.get('facts', { hash: factHash });
    if (fact && fact.source !== newSource) {
      fact.confidence = Math.min(1.0, fact.confidence + 0.1);
      await this.db.update('facts', fact);
    }
  }
}
```

**Canonical predicates**: `is_a`, `has_property`, `related_to`, `caused_by`, `depends_on`, `contradicts`, `supersedes`, `derived_from`, `preferred_by_user`, `learned_from`

## Dual Runtime Architecture

Cloud for capability, local for sovereignty — shared memory kernel bridges both.

```javascript
class DualRuntime {
  constructor({ localModel, cloudModel, memoryKernel }) {
    this.local = localModel;      // Ollama (4B-27B params)
    this.cloud = cloudModel;      // Optional: Claude, GPT, etc.
    this.memory = memoryKernel;   // Shared across runtimes
    this.mode = 'local';          // Default: sovereign
  }

  async process(query, context) {
    const complexity = this.assessComplexity(query);

    if (complexity === 'simple' || !this.cloud || this.mode === 'offline') {
      // Local: fast, private, sovereign
      return this.local.generate(query, {
        context: await this.memory.retrieve(query),
        profile: this.condensedProfile  // <2K tokens for local
      });
    }

    // Cloud: complex tasks, with sovereignty guardrails
    const sanitized = this.redactPII(query);     // Strip personal data before sending
    const response = await this.cloud.generate(sanitized, {
      profile: this.fullProfile  // ~5K tokens for cloud
    });

    // Store insights locally — cloud sees query, we keep the knowledge
    await this.memory.store(response, { source: 'cloud', query: query });

    return response;
  }

  // Degrade gracefully: cloud unavailable → local fallback
  async failover(query) {
    try {
      return await this.process(query);
    } catch (e) {
      if (this.mode !== 'local') {
        this.mode = 'local';
        return this.process(query);
      }
      throw e;
    }
  }
}
```

**Key rule**: knowledge flows **into** the local memory kernel from cloud interactions, never **out** without explicit user consent.

## Cryptographic Auditability

Every operation is hash-chained — tamper-evident by construction.

```javascript
class AuditChain {
  constructor(logPath) {
    this.logPath = logPath;
    this.lastHash = null;
  }

  async log(operation) {
    const entry = {
      timestamp: Date.now(),
      operation: operation.type,
      actor: operation.actor,
      target: operation.target,
      result: operation.result,
      previousHash: this.lastHash,
      sovereignty: { localOnly: true }  // Flag: data never left device
    };

    entry.hash = sha256(JSON.stringify(entry));
    this.lastHash = entry.hash;

    await appendJsonl(this.logPath, entry);
    return entry.hash;
  }

  // Verify chain integrity — detect any tampering
  async verify() {
    const entries = await readJsonl(this.logPath);
    let expectedPrev = null;

    for (const entry of entries) {
      if (entry.previousHash !== expectedPrev) {
        return { valid: false, brokenAt: entry.timestamp, entry };
      }
      const computed = sha256(JSON.stringify({ ...entry, hash: undefined }));
      if (computed !== entry.hash) {
        return { valid: false, tampered: entry.timestamp, entry };
      }
      expectedPrev = entry.hash;
    }
    return { valid: true, entries: entries.length };
  }
}
```

## Tiered Permission System

Sovereign AI must never take irreversible actions without consent.

```javascript
class PermissionSystem {
  constructor() {
    this.tiers = {
      safe: {       // No approval needed
        actions: ['read_file', 'search', 'calculate', 'retrieve_memory'],
        autoApprove: true
      },
      moderate: {   // Notify user, proceed unless blocked
        actions: ['write_file', 'store_memory', 'schedule_task'],
        autoApprove: false,
        timeout: 30000  // Auto-approve after 30s if no response
      },
      irreversible: {  // Require explicit approval, no timeout
        actions: ['delete_file', 'send_message', 'modify_model', 'clear_memory'],
        autoApprove: false,
        timeout: null   // Block until explicit consent
      },
      destructive: {  // Require confirmation + reason
        actions: ['factory_reset', 'delete_all_data', 'revoke_keys'],
        autoApprove: false,
        requireReason: true,
        cooldown: 60000  // 60s delay after approval before execution
      }
    };
  }

  async authorize(action, context) {
    const tier = this.getTier(action);
    if (tier.autoApprove) return { authorized: true };

    const approval = await this.requestApproval(action, context, tier);
    await this.auditLog.log({ type: 'authorization', action, approved: approval.granted, tier: tier });
    return approval;
  }
}
```

## Skill Signing and Verification

From Nova — skills/plugins are HMAC-signed to prevent injection.

```javascript
class SkillRegistry {
  constructor(signingKey) {
    this.signingKey = signingKey;
    this.skills = new Map();
  }

  register(skill) {
    const signature = hmacSha256(this.signingKey, JSON.stringify(skill.manifest));
    this.skills.set(skill.name, { ...skill, signature });
  }

  async execute(skillName, params) {
    const skill = this.skills.get(skillName);
    if (!skill) throw new Error(`Unknown skill: ${skillName}`);

    // Verify integrity before every execution
    const expected = hmacSha256(this.signingKey, JSON.stringify(skill.manifest));
    if (expected !== skill.signature) {
      throw new Error(`Skill tampered: ${skillName}`);
    }

    return skill.execute(params);
  }
}
```

## Batch-and-Purge Pattern

From Aegis — process sensitive data, generate compliance proofs, then delete the data.

```javascript
async function batchAndPurge(sensitiveData, processor) {
  const batchId = crypto.randomUUID();
  const proofChain = [];

  try {
    // Process in isolated context
    const result = await processor(sensitiveData);

    // Generate compliance proof (hash of inputs + outputs, not the data itself)
    proofChain.push({
      batchId,
      inputHash: sha256(JSON.stringify(sensitiveData)),
      outputHash: sha256(JSON.stringify(result)),
      timestamp: Date.now(),
      processingDuration: performance.now()
    });

    return { result, proof: proofChain };
  } finally {
    // ALWAYS purge — even on error
    secureClear(sensitiveData);  // Overwrite memory
    await auditLog({ type: 'purge', batchId, timestamp: Date.now() });
  }
}
```

## Multi-Agent Deliberation (E.I.K. Protocol)

From Purple-Directive — structured disagreement produces better decisions than consensus.

```javascript
class EIKDeliberation {
  constructor(agents) {
    this.agents = agents;  // 3 agents with different specializations
  }

  async deliberate(problem) {
    // Round 1: Independent analysis (no cross-contamination)
    const analyses = await Promise.all(
      this.agents.map(agent => agent.analyze(problem))
    );

    // Round 2: Cross-commentary (each sees others' work)
    const commentaries = await Promise.all(
      this.agents.map((agent, i) => {
        const othersWork = analyses.filter((_, j) => j !== i);
        return agent.crossComment(problem, analyses[i], othersWork);
      })
    );

    // Hard stop after 2 rounds — prevent infinite deliberation
    // Synthesis: merge, resolve conflicts, flag unresolved disagreements
    return this.synthesize(analyses, commentaries);
  }

  synthesize(analyses, commentaries) {
    const consensus = findAgreement(analyses);
    const conflicts = findDisagreement(analyses, commentaries);

    return {
      decision: consensus,
      confidence: consensus.length / (consensus.length + conflicts.length),
      unresolvedConflicts: conflicts,  // Transparent about disagreement
      requiresHumanInput: conflicts.length > 0
    };
  }
}
```

## Local Inference Stack

| Component | Purpose | Options |
|-----------|---------|---------|
| **Runtime** | Model execution | Ollama, llama.cpp, vLLM, MLX |
| **Models** | Language understanding | Qwen3 (4B-32B), Llama 3.3 (8B-70B), Phi-4, Gemma 3 |
| **Quantization** | Fit on consumer hardware | GGUF Q4_K_M (4-bit), Q5_K_M (5-bit), Q8_0 (8-bit) |
| **Embedding** | Vector representations | nomic-embed-text, mxbai-embed-large, all-MiniLM |
| **STT** | Voice input | Faster-Whisper, Parakeet (NVIDIA) |
| **TTS** | Voice output | Kokoro, Piper, Bark |
| **Vector DB** | Similarity search | ChromaDB, Qdrant, FAISS, sqlite-vec |
| **Search** | Web search without tracking | SearXNG (self-hosted) |

**VRAM tiers:**

| VRAM | Model Size | Capability |
|------|-----------|------------|
| 4 GB | 1-3B Q4 | Basic chat, simple tasks |
| 8 GB | 7-8B Q4 | Good reasoning, tool use |
| 16 GB | 14-27B Q4 | Strong reasoning, code generation |
| 24 GB+ | 32-70B Q4/Q5 | Near-cloud capability |

## Anti-Patterns

| WRONG | CORRECT |
|-------|---------|
| Cloud-required for basic inference | Local model as default, cloud as optional enhancement |
| Memory locked to specific model | Model-agnostic memory kernel (vectors + FTS + graph) |
| Single retrieval method | Hybrid retrieval with Reciprocal Rank Fusion |
| Deploy fine-tuned model without eval | A/B evaluation, rollback if regression |
| Trust unverified model outputs | Hash-chain audit trail, skill signing |
| AI takes irreversible actions silently | Tiered permissions with explicit consent for destructive ops |
| Send raw queries to cloud | PII redaction before any cloud interaction |
| Store data indefinitely | Batch-and-purge for sensitive data, retention policies |
| Single-agent decisions | Multi-agent deliberation surfaces disagreement |
| Monolithic memory | Episodic/semantic/procedural separation with consolidation |

## Integration with QURA Optimization Skills

This skill connects to the heuristic optimization stack:

- **Heuristic Search** navigates the space of possible improvements during self-optimization
- **Evolutionary Optimization** generates candidate mutations for model/skill improvement
- **Self-Optimizing Meta-Loop** provides the benchmark→mutate→verify cycle
- **This skill** provides the sovereignty guarantees: all optimization happens locally, all improvements are cryptographically audited, all changes require permission

Together: the optimization stack makes QURA **smarter** — this skill ensures it stays **sovereign**.

## Steering Vectors: Reversible Interventions (From OBLITERATUS)

From OBLITERATUS's SteeringHookManager — apply behavioral modifications at inference time without permanently changing model weights. The sovereign analog: **explore behavioral changes reversibly before committing to permanent self-modification**.

```javascript
class SteeringVectorManager {
  constructor(model) {
    this.model = model;
    this.activeVectors = new Map();  // name → { vector, layer, scale, applied }
    this.hooks = new Map();          // layer → hook functions
  }

  // Extract a steering vector from contrasting example pairs
  async extract(name, { positiveExamples, negativeExamples, method = 'diff_in_means' }) {
    const methods = {
      // Method 1: Difference in means (simplest — OBLITERATUS basic tier)
      diff_in_means: async () => {
        const posActivations = await Promise.all(
          positiveExamples.map(ex => this.model.getHiddenStates(ex))
        );
        const negActivations = await Promise.all(
          negativeExamples.map(ex => this.model.getHiddenStates(ex))
        );

        const posMean = elementwiseMean(posActivations);
        const negMean = elementwiseMean(negActivations);
        return posMean.map((v, i) => v - negMean[i]);
      },

      // Method 2: SVD — captures principal direction of contrast
      svd: async () => {
        const diffs = await Promise.all(
          positiveExamples.map(async (pos, i) => {
            const posAct = await this.model.getHiddenStates(pos);
            const negAct = await this.model.getHiddenStates(negativeExamples[i]);
            return posAct.map((v, j) => v - negAct[j]);
          })
        );
        const { U, S } = svd(matrixFromRows(diffs));
        return U.column(0).scale(S[0]);  // First principal component
      },

      // Method 3: Whitened SVD — removes variance bias
      whitened_svd: async () => {
        const allActivations = await Promise.all(
          [...positiveExamples, ...negativeExamples].map(ex => this.model.getHiddenStates(ex))
        );
        const covariance = covarianceMatrix(allActivations);
        const whitened = whitenActivations(allActivations, covariance);
        // Now apply standard SVD on whitened activations
        const diffs = whitened.slice(0, positiveExamples.length).map((pos, i) =>
          pos.map((v, j) => v - whitened[positiveExamples.length + i][j])
        );
        const { U, S } = svd(matrixFromRows(diffs));
        return U.column(0).scale(S[0]);
      }
    };

    const vector = await methods[method]();
    this.activeVectors.set(name, { vector, method, applied: false, scale: 1.0 });
    return vector;
  }

  // Apply steering vector at inference time — REVERSIBLE, no weight changes
  async steer(name, { layer, scale = 1.0 }) {
    const sv = this.activeVectors.get(name);
    if (!sv) throw new Error(`Unknown steering vector: ${name}`);

    const hook = (activations) => {
      return activations.map((v, i) => v + sv.vector[i] * scale);
    };

    this.hooks.set(`${name}:${layer}`, hook);
    this.model.registerForwardHook(layer, hook);
    sv.applied = true;
    sv.scale = scale;
    sv.layer = layer;

    return { steered: true, name, layer, scale, reversible: true };
  }

  // Remove steering — instant reversion to original behavior
  async unsteer(name) {
    const sv = this.activeVectors.get(name);
    if (!sv || !sv.applied) return { unsteered: false };

    const hookKey = `${name}:${sv.layer}`;
    this.model.removeForwardHook(sv.layer, this.hooks.get(hookKey));
    this.hooks.delete(hookKey);
    sv.applied = false;

    return { unsteered: true, name };
  }

  // Sovereign A/B test: compare steered vs unsteered on validation set
  async evaluateSteering(name, validationSet) {
    const unsteeredResults = await Promise.all(
      validationSet.map(input => this.model.generate(input))
    );

    await this.steer(name, { layer: this.activeVectors.get(name).layer });
    const steeredResults = await Promise.all(
      validationSet.map(input => this.model.generate(input))
    );
    await this.unsteer(name);

    return {
      unsteered: { results: unsteeredResults, scores: await evaluate(unsteeredResults) },
      steered: { results: steeredResults, scores: await evaluate(steeredResults) },
      improvement: compare(steeredResults, unsteeredResults),
      recommendation: shouldCommit(steeredResults, unsteeredResults)
        ? 'commit_to_weights'  // Promotion: steering → permanent modification
        : 'keep_as_steering'   // Keep reversible
    };
  }
}
```

**Sovereignty principle**: always explore reversibly before committing permanently. Steering vectors are the cognitive equivalent of a feature branch — test the change in isolation, validate, then merge (or discard).

## Privacy-Preserving Community Telemetry (From OBLITERATUS)

OBLITERATUS feeds anonymized run telemetry into a community dataset for crowd-sourced optimization. The sovereign analog: share **what works** without exposing **your data**.

```javascript
class SovereignTelemetry {
  constructor({ localOnly = false, anonymizationLevel = 'strong' }) {
    this.localOnly = localOnly;
    this.anonymizationLevel = anonymizationLevel;
    this.localLedger = [];  // Always stored locally first
  }

  // Record an optimization outcome — always local first
  async record(outcome) {
    const entry = {
      // What we keep locally (full detail)
      local: {
        mutation: outcome.mutation,
        metrics: outcome.metrics,
        modelId: outcome.modelId,
        timestamp: Date.now(),
        context: outcome.context
      },
      // What we might share (anonymized)
      shareable: this.anonymize(outcome)
    };

    this.localLedger.push(entry);
    await appendJsonl('./telemetry/local.jsonl', entry.local);
    return entry;
  }

  // Anonymize: strip identifying info, keep only patterns
  anonymize(outcome) {
    return {
      // Category, not specific mutation
      mutationType: outcome.mutation.category,
      mutationScope: outcome.mutation.scope,

      // Relative improvement, not absolute metrics
      relativeImprovement: outcome.metrics.improvement / outcome.metrics.baseline,
      improved: outcome.metrics.improved,

      // Model family, not specific model
      modelFamily: outcome.modelId.split('/')[0],
      modelSizeClass: quantize(outcome.modelSize, [1e9, 3e9, 7e9, 13e9, 30e9, 70e9]),

      // Problem class, not specific problem
      problemClass: outcome.context.category,

      // Hardware class, not specific hardware
      hardwareClass: classifyHardware(outcome.hardware),

      // Timestamp quantized to day (no precise timing)
      date: new Date().toISOString().split('T')[0],

      // Hash for deduplication, not identification
      hash: sha256(JSON.stringify({
        mutationType: outcome.mutation.category,
        modelFamily: outcome.modelId.split('/')[0],
        improved: outcome.metrics.improved
      }))
    };
  }

  // Contribute to community — only with explicit consent, sovereignty-preserving
  async contribute(consent) {
    if (this.localOnly || !consent.granted) return { contributed: false };

    const shareable = this.localLedger
      .filter(e => e.shareable)
      .map(e => e.shareable);

    // Batch-and-purge: share aggregate, purge individual
    const aggregate = this.aggregateContributions(shareable);

    // Cryptographic proof that data was anonymized before sharing
    const proof = {
      dataHash: sha256(JSON.stringify(aggregate)),
      anonymizationLevel: this.anonymizationLevel,
      consentHash: sha256(JSON.stringify(consent)),
      timestamp: Date.now()
    };

    return {
      contributed: true,
      entries: aggregate.length,
      proof,
      // What was NOT shared
      redacted: ['model_weights', 'training_data', 'user_queries', 'specific_metrics', 'timestamps']
    };
  }

  // Aggregate: share distributions, not individual runs
  aggregateContributions(entries) {
    const byCategory = groupBy(entries, 'mutationType');
    return Object.entries(byCategory).map(([type, runs]) => ({
      mutationType: type,
      successRate: runs.filter(r => r.improved).length / runs.length,
      medianImprovement: median(runs.map(r => r.relativeImprovement)),
      sampleSize: runs.length,
      modelFamilies: [...new Set(runs.map(r => r.modelFamily))],
      hardwareClasses: [...new Set(runs.map(r => r.hardwareClass))]
    }));
  }

  // Learn from community: import crowd-sourced patterns without exposing local data
  async importCommunityPatterns(communityData) {
    // Community tells us: "micro mutations work 73% of the time on 7B models"
    // We don't share: our specific model, data, or results
    const relevantPatterns = communityData.filter(pattern =>
      pattern.modelFamilies.includes(this.localModelFamily) ||
      pattern.hardwareClasses.includes(this.localHardwareClass)
    );

    return relevantPatterns.map(p => ({
      recommendation: p.mutationType,
      communitySuccessRate: p.successRate,
      communityMedianImprovement: p.medianImprovement,
      communitySampleSize: p.sampleSize,
      relevance: 'model_family_match'
    }));
  }
}
```

**Sovereignty rules for telemetry**:
1. **Local first**: all telemetry stored locally before any sharing decision
2. **Explicit consent**: never share without user approval
3. **Anonymization**: strip all identifying information — share patterns, not data
4. **Aggregation**: share distributions (success rates, medians), never individual runs
5. **Cryptographic proof**: prove anonymization happened, verifiable by user
6. **Batch-and-purge**: sensitive data is processed, aggregated, then purged
7. **Bidirectional value**: community patterns flow IN, anonymized patterns flow OUT — equal exchange
