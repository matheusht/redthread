# Experiment B Protocol: Autonomous Attack Algorithm Benchmark

Status: research design draft. No code changes proposed.

## Goal

Compare autonomous jailbreak and red-team strategies by confirmed value per cost.

Primary question:

> Which strategy produces the most JudgeAgent-confirmed findings per dollar and per model call under the same conditions?

Secondary question:

> Which strategy creates findings that are easiest to replay and use as later defense evidence?

## Main rule

Use one harness. Change only the strategy.

Hold fixed or explicitly declared:

- target model and target settings
- attacker model and attacker settings
- attacker prompt template version
- JudgeAgent rubric and judge model
- seed set and category mix
- seed order or randomization method
- random seed
- max target calls
- max attacker calls
- max judge calls
- max turns
- retry policy
- cost accounting
- output schema

## Strategies to compare

### 1. RedThread baseline

Purpose: control group.

Use the current RedThread attack, judge, replay, and evidence path. This shows whether imported algorithms beat the existing simple spine.

### 2. PAIR-style iterative refinement

Grounding: PAIR describes black-box automatic jailbreak prompt generation using an attacker LLM that iteratively refines attempts based on target responses. The paper reports strong success with low query counts, often fewer than 20 queries.

Fit for RedThread:

- good candidate for cost-per-confirmed-finding measurement
- simple enough to wrap as strategy logic
- must keep JudgeAgent as final authority

Controls to declare:

- attacker model/settings
- max iterations
- retry policy
- stopping rule

Risk:

- reported success can depend heavily on judge choice, target choice, and seed mix

### 3. TAP-style tree search

Grounding: TAP frames attacks as a tree-search process, using pruning to reduce query use while preserving high attack success.

Fit for RedThread:

- useful comparator for search budget efficiency
- maps to branch/attempt ledger shape
- likely better than linear refinement when early branches vary in quality

Controls to declare:

- tree width
- tree depth
- branching policy
- pruning rule
- attacker model/settings

Risk:

- more moving parts than PAIR
- tree width/depth can hide cost if not counted strictly

### 4. Crescendo-style multi-turn escalation

Grounding: Crescendo studies multi-turn escalation where the model is guided gradually across turns. Microsoft PyRIT includes Crescendomation support, making it practical to test through existing PyRIT plumbing if needed.

Fit for RedThread:

- strong candidate for multi-turn targets
- relevant to real conversational failure modes
- may expose failures missed by single-turn seeds

Controls to declare:

- max turns
- backtracking policy
- stopping rule
- attacker model/settings

Risk:

- can be hard to compare fairly unless max turns and total calls are fixed

### 5. CoP strategy composition

Grounding: RedThread has a working composition path and a hypothesis that composed strategies reduce dead failures. Early local runs are promising but too small for product claims.

Fit for RedThread:

- native strategy candidate
- does not require new external framework ownership
- directly tests whether composition is worth keeping beyond intuition

Controls to declare:

- exact composition recipe
- same seed set
- same budgets
- same JudgeAgent rubric

Risk:

- early signal may not generalize
- must not become default without controlled A/B proof

### 6. Siege-style comparator

Grounding: Siege is a newer tree-search-style multi-turn comparator. Treat cautiously unless reproduction materials and settings are clear enough.

Fit for RedThread:

- optional research comparator
- useful if it adds a distinct search pattern not covered by TAP/Crescendo

Controls to declare:

- exact reproduction settings
- tree/search settings
- attacker model/settings

Risk:

- do not let it expand scope if reproducibility is weak

## Metrics

### Primary metrics

- confirmed findings
- confirmed ASR
- cost per confirmed finding
- target calls per confirmed finding
- attacker calls per confirmed finding
- judge calls per confirmed finding
- wall-clock seconds per confirmed finding

Definition:

```text
confirmed ASR = seeds with at least one JudgeAgent-confirmed finding / total seeds
```

Keep seed-level ASR separate from attempt-level counts. Deduplicate confirmed findings by `finding_id` or by `seed_id + objective_id`.

### Operator burden metrics

Track simple counts only:

- automatic JudgeAgent reviews run
- inconclusive JudgeAgent decisions
- human artifact reviews, if a person opens a private artifact to resolve an inconclusive case

A human artifact review is one operator opening one private artifact reference for one seed/objective decision. This is not part of the primary ranking unless the same review policy is used for every strategy.

Do not create a dashboard or manual workflow system.

### Replay and defense-adjacent metrics

These do not make Experiment B a defense experiment. They only show whether findings are useful for later Scope A.

- replayable confirmed findings, if replay is already emitted by the existing harness
- variant replay pass/fail rate, if replay is already emitted by the existing harness

Do not include defense promotion metrics in Phase 1 or Phase 2. Cost per promotable defense belongs to Scope A.

### Utility and guardrail-style metrics

These are Scope A metrics unless the existing harness already emits them for free. They are not required for Experiment B ranking.

- benign utility retention
- over-refusal rate
- block rate on harmful seeds
- variant block rate
- inconclusive judge rate

## Benchmark-against plan

Use external benchmarks as seed/evaluation inputs, not product proof.

Candidates:

- JailbreakBench: established benchmark suite and repository for jailbreak evaluation.
- MT-JailBench: useful because it decomposes evaluation into function, strategy, prompt generation, prompt refinement, and flow control; this helps identify confounders.
- PandaGuard: useful as a broad attack/defense/judge evaluation reference and weak detector/benchmark signal.
- SoK4JailbreakGuardrails: useful taxonomy source for defense and evaluation caveats.

Grounding links:

- JailbreakBench repo: https://github.com/JailbreakBench/jailbreakbench
- MT-JailBench repo: https://github.com/SafetyArena/mt-jailbench
- PandaGuard paper: https://arxiv.org/html/2505.13862v2
- PandaGuard repo: https://github.com/beijing-aisi/panda-guard
- SoK4JailbreakGuardrails paper: https://arxiv.org/abs/2506.10597
- SoK4JailbreakGuardrails repo: https://github.com/xunguangwang/SoK4JailbreakGuardrails

Rules:

- every dataset needs license review
- every dataset needs safety review
- external labels are weak metadata only
- JudgeAgent remains source of confirmed findings

## Confounders to control

MT-JailBench highlights why jailbreak benchmarks can disagree. Control these directly:

- evaluation function
- attack strategy
- prompt generation method
- prompt refinement method
- flow control
- attacker model/settings
- judge model/settings
- target model/settings
- seed category distribution
- seed order/randomization
- retry budget
- max turns
- cost accounting

## Suggested run plan

### Phase 0: dry-run schema validation

Use tiny safe placeholder seeds. Verify manifest, attempts, judge events, and summary shape.

### Phase 1: small fixed-budget pilot

Run each strategy against the same small approved seed set.

Budget example:

- same target model
- same attacker model, unless explicitly declared per strategy
- same JudgeAgent
- same max turns
- same max retries
- same max target calls per seed
- same max attacker calls per seed
- same max judge calls per seed

Output:

- one summary per strategy
- one cross-strategy comparison table
- notes on failures and inconclusive decisions
- warning that stochastic single-run pilots are not generalizable

### Phase 2: controlled benchmark run

Only run after dataset license/safety review.

Use repeated runs for stochastic strategies or mark results as preliminary.

Output:

- ranked strategies by cost per confirmed finding
- ranked strategies by confirmed ASR under fixed budget
- replayability notes
- recommendation: keep, adapt, or reject each strategy

### Phase 3: handoff to Scope A

Take only the best one or two strategies into the closed-loop self-healing study.

## Acceptance criteria

Experiment B is useful if it produces:

- a fair strategy ranking under shared conditions
- per-cost metrics, not just ASR
- declared attacker, target, judge, seed, retry, and strategy settings
- clear failure modes and confounders
- reproducible JSONL/manifest artifacts
- a recommendation that reduces future implementation risk

## Hard stops

Stop or narrow scope if:

- raw jailbreak bodies would need to enter public docs
- benchmark license is unclear
- safety review is missing
- a strategy requires large new framework ownership
- results rely on external labels instead of JudgeAgent decisions
- cost accounting cannot be made comparable
- any path implies automatic defense promotion
