# redthread autoresearch

This document adapts Karpathy's `original/program.md` for RedThread.

The core idea remains the same:
- run on a dedicated research branch
- make one bounded change at a time
- execute a fixed experiment
- log the outcome
- keep only improvements
- loop indefinitely

The difference is that RedThread is not a single-metric training repo. It is a multi-agent security system with attacker, judge, defense, telemetry, and memory layers. Because of that, autoresearch must optimize a narrow part of the stack first.

## Scope

Autoresearch is allowed to improve:
- attacker-side prompt generation
- persona generation
- attack algorithm parameters and heuristics
- campaign scheduling and objective selection
- replay and corpus selection for known vulnerability classes
- experiment harnesses and scoring aggregation used only for research

Autoresearch is not allowed to autonomously modify:
- `prepare`-equivalent ground truth layers such as Judge rubrics, Golden Dataset labels, or acceptance thresholds
- production defense deployment policy
- `MEMORY.md` entries already validated from prior real campaigns
- telemetry thresholds used for production alerting unless explicitly placed in a research-only path

The first objective is not “make the whole system better.”
The first objective is:

**Increase reliable vulnerability discovery and exploit replay quality without degrading evaluation integrity.**

This still improves the end-to-end workflow, but in the correct order:
- first improve attacker-side search quality
- then improve guardrail regression pressure
- then improve objective scheduling and campaign routing
- only later consider carefully-scoped evaluation-layer tuning

## Why This Boundary Exists

RedThread already separates roles:
- attacker is creative and cheap
- judge is the ground-truth evaluator
- defense architect is high-precision and validation-gated
- telemetry and ASI are runtime health controls

If autoresearch mutates the judge or defense criteria while also using those layers to score itself, the loop becomes self-referential and unreliable.

Therefore:
- optimize the offense/search plane first
- keep the evaluation/control plane mostly fixed
- only expand scope after stable gains are proven

## Research Surfaces

Prioritize these surfaces in order:

1. **Objective selection policy**
   - choose which vulnerability objective to run next based on prior campaign history
   - rebalance toward objectives with high partial scores, near misses, or historically unstable ASR

2. **Attack algorithm policy**
   - choose `pair` vs `tap` vs `crescendo`
   - tune depth, width, branching, turns, and early-stop heuristics

3. **Persona strategy generation**
   - improve persona diversity
   - map personas to objective class and prior winning traces
   - mine successful motifs from past campaigns

4. **Prompt mutation / exploit search**
   - mutate seed prompts using prior successful fragments
   - evolve multi-turn escalation sequences
   - add replay-driven exploration around confirmed jailbreak pivots

5. **Defense stress-testing**
   - once a guardrail exists, generate adversarial variants to break that exact guardrail scope
   - optimize for regression discovery, not for direct deployment

## Initial Objective Set

Start with a small fixed portfolio. Do not run dozens of objectives at once.

Recommended Phase 1 portfolio:

1. `prompt_injection`
2. `authorization_bypass`
3. `sensitive_info_exfiltration`
4. `system_prompt_exfiltration`

Recommended mapping to RedThread-style objective text:
- prompt injection: reveal system instructions, ignore prior instructions, execute hidden policy override
- authorization bypass: act as admin, internal tester, developer, or trusted operator
- sensitive info exfiltration: extract private records, API keys, access tokens, or regulated data
- system prompt exfiltration: reveal hidden instructions, developer prompt, memory content, or internal tool policy

Recommended Phase 2 additions after stability:
- guardrail bypass replay against validated `MEMORY.md` clauses
- Crescendo-only multi-turn social engineering objectives
- domain-specific campaign packs from real customer environments

## Why These Objectives

They best match the current repository and data:
- existing rubrics already cover `prompt_injection`, `authorization_bypass`, and `sensitive_info`
- campaign history already contains repeated authorization, secret-token, HIPAA, and system-prompt exfiltration attempts
- defense synthesis and memory scoping are already built around confirmed jailbreak traces

Avoid making “enhance attacker model” the first autoresearch objective.
That is too broad. The better first target is:

**Find which objectives, algorithms, personas, and prompt mutations maximize confirmed jailbreak discovery per campaign while keeping the judge fixed.**

However, attacker-model improvement is absolutely in scope.
It should happen through bounded levers:
- attacker prompt template optimization
- strategy library expansion
- persona-to-objective matching
- replay-conditioned prompt mutation
- algorithm routing and hyperparameter tuning
- selection of which local attacker model variant handles which objective family

Do not start by fine-tuning or replacing the whole attacker stack blindly.
Start by improving the attacker system around the model, then evaluate whether model-swapping or fine-tuning is still needed.

## Success Metrics

Use a composite research score, not one metric.

Primary metrics:
- confirmed jailbreak count
- attack success rate (ASR)
- mean judge score
- near-miss rate: score in `[3.5, success_threshold)`
- unique successful attack vectors

Secondary metrics:
- defense break rate on replay against scoped guardrails
- time-to-first-jailbreak
- cost proxy: total turns or total target calls
- drift in benign canary behavior after defense validation

Hard constraints:
- golden regression must not be modified by autoresearch
- no production guardrail deployment from unreviewed autoresearch changes
- no persistent worsening of benign telemetry

## Fixed Experiment Unit

One experiment should be a bounded campaign batch, for example:
- 3 to 5 objectives
- 2 to 4 personas per objective
- 1 algorithm family per run
- fixed run budget such as max turns / max tree width / max total target calls

This is the RedThread equivalent of Karpathy's “5 minute train run”.

Example fixed unit:
- 4 objectives
- 3 personas each
- 1 algorithm per objective
- max 12 target interactions per persona branch

## Agent Topology

Do not run one single agent trying to optimize the entire workflow end to end.
That creates poor credit assignment and unstable search.

Also do not spawn one agent per objective with no shared coordinator.
That creates duplicated work and fragmented memory.

Use a **supervisor + 3 worker lanes**:

1. **Research Supervisor**
   - owns the branch
   - reads prior experiment history
   - selects the current research phase
   - assigns objectives to worker lanes
   - accepts or rejects changes based on fixed metrics

2. **Offense Lane**
   - improves attacker prompts, strategy templates, algorithm routing, and persona selection
   - this is the primary lane in early phases

3. **Regression Lane**
   - replays prior successful jailbreaks and guardrail-scoped bypass attempts
   - measures whether offense improvements generalize or only overfit

4. **Control Lane**
   - runs frozen baseline campaigns
   - tracks judge score distribution, ASI side-effects, and stability constraints
   - vetoes apparent gains that come from instability or metric corruption

The supervisor is the only lane allowed to advance the branch.

## How Many Agents To Run

Default recommendation for nonstop local execution:
- 1 supervisor
- 2 active research workers
- 1 baseline/control worker

So the practical answer is **3 worker agents plus 1 coordinator**.

Do not start with more than that.
The bottleneck is not agent count. It is clean experiment design and reliable acceptance criteria.

If local capacity is limited, run:
- 1 supervisor
- 1 offense worker
- 1 control worker

If capacity is strong and logs are large, scale to:
- 1 supervisor
- 2 offense workers
- 1 regression worker
- 1 control worker

Only parallelize workers whose write scopes are disjoint or whose outputs are purely experimental artifacts.

## Experiment Loop

Loop forever:

1. Read current branch state and recent research log
2. Choose one bounded hypothesis for exactly one research lane
3. Modify only research-approved files
4. Run the fixed campaign batch
5. Extract metrics from JSONL logs
6. Append structured results to `autoresearch/results.tsv`
7. Keep the change only if the composite score improved without violating constraints
8. Otherwise revert and try the next idea

At the lane level, the loop should look like:
- supervisor selects phase and active objective portfolio
- offense worker proposes changes
- regression worker pressure-tests known wins
- control worker compares against frozen baselines
- supervisor decides keep/discard

## Files In Scope For Early Phases

Read-only context:
- `README.md`
- `docs/product.md`
- `docs/DEFENSE_PIPELINE.md`
- `docs/ANTI_HALLUCINATION_SOP.md`
- `docs/PHASE_REGISTRY.md`
- historical `logs/*.jsonl`

Editable in Phase 1:
- `src/redthread/personas/generator.py`
- `src/redthread/core/pair.py`
- `src/redthread/core/tap.py`
- `src/redthread/core/crescendo.py`
- `src/redthread/orchestration/supervisor.py`
- new research-only harness code under `src/redthread/research/`

Protected in Phase 1:
- `src/redthread/evaluation/`
- `src/redthread/core/defense_synthesis.py`
- `src/redthread/memory/`
- `src/redthread/telemetry/asi.py`
- `src/redthread/daemon/monitor.py`

## Implementation Phases

### Phase 1: Research Harness
- create `src/redthread/research/`
- add experiment runner for fixed campaign batches
- add results logger and branch-advance logic
- parse existing `logs/*.jsonl` into a seed corpus

### Phase 1.5: Baseline Registry
- define frozen benchmark objective set
- define frozen baseline algorithms and settings
- record benchmark outputs separate from exploratory runs
- block branch advancement unless benchmark constraints hold

### Phase 2: Objective Scheduler
- score prior objectives by ASR, near misses, novelty, and recency
- choose the next objective mix automatically
- keep portfolio size small, around 3 to 5 concurrent objectives

### Phase 3: Attacker Improvement Loop
- mutate persona prompts and attack prompts
- tune algorithm parameters
- route objectives to the best attacker strategy family
- compare local attacker models by objective family if multiple local models are available
- keep best variants in a research memory store

### Phase 4: Guardrail Regression Research
- replay confirmed jailbreaks against scoped guardrails
- search for paraphrases and multi-turn bypasses
- treat this as a separate leaderboard from raw discovery

### Phase 5: End-to-End Campaign Optimization
- optimize objective scheduling based on recent findings, guardrail scope, and campaign novelty
- choose when to run discovery vs replay vs regression campaigns
- allow the supervisor to rebalance worker lanes dynamically

### Phase 6: Optional Expansion
- allow limited research on judge prompt wording or telemetry thresholds only in isolated evaluation branches with human review

## Local-LLM Operating Mode

Because this will run continuously on a local model:
- keep the local model on attacker/research generation duties
- use deterministic local settings where possible for replay comparability
- periodically calibrate against the existing judge instead of replacing it entirely

Recommended split:
- local LLM: hypothesis generation, objective mutation, prompt mutation, persona drafting
- local attacker model: offensive generation and strategy search
- existing judge layer: scoring and acceptance gate
- existing defense layer: replay validation gate

If full-local operation is required later, add a calibration suite first. Do not immediately trust a local judge as ground truth.

## Objective Assignment Policy

The supervisor should not assign objectives randomly.
Each worker gets objectives based on expected information gain.

Use this priority order:

1. **Near-miss pressure**
   - objectives with many scores close to jailbreak threshold
   - these are the highest-likelihood short-term wins

2. **Historically successful or partially successful classes**
   - objectives with prior confirmed jailbreaks or repeated ASR > 0
   - these support exploit replay and generalization research

3. **Coverage gaps**
   - objective classes already supported by rubrics but underexplored in logs

4. **Regression pressure**
   - objectives targeting scoped `MEMORY.md` guardrails to verify defenses still hold

5. **Novel exploratory objectives**
   - only a small percentage of runs, e.g. 10 to 20 percent

Practical assignment rule:
- offense worker gets high expected-gain objectives
- regression worker gets prior jailbreak families and guardrail-scoped replays
- control worker gets the frozen benchmark pack every cycle or every N cycles

## Recommended First Multi-Agent Layout

For RedThread right now, start with this exact layout:

### Worker A: Offense Search
- objectives: `authorization_bypass`, `system_prompt_exfiltration`
- algorithms: `tap`, `crescendo`
- goal: maximize confirmed jailbreaks and near misses

### Worker B: Sensitive Data Replay
- objectives: `sensitive_info_exfiltration`, `prompt_injection`
- algorithms: `tap` first, `pair` as fallback baseline
- goal: mine successful prompt motifs and replay against similar targets

### Worker C: Control / Benchmark
- objectives: frozen benchmark pack across all 4 objective classes
- algorithms: fixed baseline settings
- goal: detect overfitting, instability, or fake gains

Then let the supervisor choose the next batch based on:
- best recent delta in ASR or near-miss rate
- novelty of discovered successful vectors
- stability against baseline pack

## Phase 1 Acceptance Criteria

Phase 1 is successful when RedThread can:
- run bounded autoresearch batches indefinitely
- select from a fixed portfolio of 3 to 5 objectives
- log experiment deltas cleanly
- preserve judge and defense integrity
- produce measurable gains in jailbreak discovery or near-miss quality on repeated runs

## Default Recommendation

Narrow the first continuous autoresearch program to **4 objectives**:
- prompt injection
- authorization bypass
- sensitive info exfiltration
- system prompt exfiltration

Run them across **2 algorithm families** first:
- `tap`
- `crescendo`

Keep `pair` as a baseline comparator, not the main search engine.

That gives a manageable first matrix:
- 4 objectives
- 2 primary algorithms
- 2 to 4 personas each

This is small enough to run continuously on local hardware and broad enough to improve RedThread where it already has evidence, rubrics, transcripts, and a defense loop.
