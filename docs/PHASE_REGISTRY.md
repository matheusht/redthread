# RedThread — Phase Registry

> **Purpose**: Master registry of all development phases. Tracks status, dates, deliverables, and key decisions for historical reference.

---

## Phase Overview

| Phase | Name | Status | Dates | Key Deliverables |
|---|---|---|---|---|
| 1 | Foundation & PAIR | ✅ Complete | — | `pair.py`, `judge.py`, `models.py`, CLI, scoring rubrics |
| 2 | PAIR Refinement | ✅ Complete | — | Full PAIR loop, Persona Generator, heuristic scoring, PyRIT integration |
| 3 | TAP Algorithm | ✅ Complete | — | `tap.py`, `AttackNode` model, tree search with pruning |
| 4 | LangGraph Orchestration | ✅ Complete | — | Supervisor, worker nodes, fan-out/fan-in, conditional routing |
| 4.5 | Defense Synthesis & Telemetry | ✅ Complete | — | `defense_synthesis.py`, `guardrail_loader.py`, `drift.py`, `embeddings.py` |
| 5A | Anti-Hallucination Baseline | ✅ Complete | 2026-04-03 | Golden Dataset, model separation, DeepEval pipeline, SOP |
| 5B | ARIMA & ASI | ✅ Complete | 2026-04-03 | `arima.py`, `asi.py`, composite drift metrics |
| 5C | Continuous Monitoring | ✅ Complete | 2026-04-04 | Monitor daemon, SQLite storage, drift-triggered campaigns |
| 5D | CI/CD Integration | ✅ Complete | 2026-04-04 | GitHub Actions, regression gates, dashboard |
| 6A | Crescendo Algorithm | ✅ Complete | 2026-04-04 | `crescendo.py`, client-side history, escalation loop with backtracking |
| 7A | Safe Patch Autoresearch (Offense) | ✅ Complete | 2026-04-07 | `research phase5`, bounded offense source mutation proposals, explicit research-plane acceptance gate |
| 7B | Bounded Defense Prompt Autoresearch | ✅ Complete | 2026-04-08 | `research phase6`, sealed defense prompt mutation gate, reused Phase 3 promotion flow |
| 8A | Agentic Security Schema | ✅ Complete | 2026-04-16 | threat taxonomy, provenance model, action envelope, amplification metrics, runtime summary extension |
| 8B | Attack Simulation Lane | ✅ Complete | 2026-04-16 | sealed tool-hijack fixtures, simulated registry, confused deputy scenarios, resource amplification scenarios |
| 8C | Deterministic Control Plane | ✅ Complete | 2026-04-16 | authorization engine, permission inheritance, least-agency presets, policy tests |
| 8D | Canary & Runtime Containment | ✅ Complete | 2026-04-16 | canary helpers, propagation reports, runtime budget evaluation, summary extensions |

## Current Direction

RedThread is now in the **Phase 7 autoresearch era**:
- `phase5` is the bounded offense lane
- `phase6` is the bounded defense-prompt lane
- both lanes still require the existing Phase 3 accept/reject boundary and explicit promotion discipline

This means the project direction after GS-MCTS is no longer “add more jailbreak algorithms first.” The current direction is **safe self-improvement with bounded mutation surfaces**.

## Next Bounded Steps

The self-healing hardening tranche that followed 7A and 7B is now largely implemented:
1. Phase 6 no longer stops at prompt-contract checks; it now uses richer sealed replay suites and structured replay evidence
2. defense-specific validation reports and promotion evidence now exist
3. promotion now enforces a defense utility gate instead of relying only on generic proposal validation
4. replay/reporting/utility-gate surfaces are now protected from Phase 6 mutation

The next finite steps are now smaller and more operational:
1. expand replay suites further with curated runtime fixture artifacts as needed
2. keep operator inspection UX strong for validation and promotion evidence
3. align historical docs and runtime behavior as the hardened self-healing path evolves
4. only after sustained validation, consider widening the mutable defense surface beyond prompt/template assets
5. build the additive Phase 8 agentic-security lane on top of the existing attack, evaluation, defense, and telemetry stack

---

## Phase Details

### Phase 1: Foundation & PAIR
**Objective**: Establish the core engine with the simplest attack algorithm.

**Deliverables**:
- `src/redthread/core/pair.py` — PAIR iterative refinement loop
- `src/redthread/evaluation/judge.py` — JudgeAgent with Auto-CoT (G-Eval)
- `src/redthread/models.py` — Core data models (Persona, AttackTrace, JudgeVerdict)
- `src/redthread/cli.py` — Rich CLI with Click
- `src/redthread/evaluation/rubrics/authorization_bypass.yaml` — First rubric
- `tests/test_pair.py`, `tests/test_judge.py`, `tests/test_tasks.py`

**Key Decisions**:
- Python 3.12+ with Pydantic v2 for type safety
- PyRIT as infrastructure plumbing (Adapter pattern)
- GPT-4o as the sole Judge model

---

### Phase 2: PAIR Refinement
**Objective**: Harden the PAIR loop and add persona-based attack diversity.

**Deliverables**:
- `src/redthread/personas/generator.py` — MITRE ATLAS-based persona generation
- `src/redthread/personas/atlas_taxonomy.py` — Tactic/technique definitions
- Enhanced `pair.py` with attacker CoT parsing
- `src/redthread/pyrit_adapters/targets.py` — RedThreadTarget wrapper

**Key Decisions**:
- Asymmetric model deployment: Attacker (lightweight) + Judge (heavyweight)
- PyRIT `send_prompt_async` as the sole interaction interface

---

### Phase 3: TAP Algorithm
**Objective**: Implement Tree of Attacks with Pruning for deep vulnerability discovery.

**Deliverables**:
- `src/redthread/core/tap.py` — 4-phase TAP: Branch → Pre-Query Prune → Attack+Assess → Post-Score Prune
- `src/redthread/models.py` — Added `AttackNode` model (tree node with `parent_id`, `depth`, `score`)
- `src/redthread/cli.py` — Added `--algorithm` flag
- `tests/test_tap.py`

**Key Decisions**:
- TAP reuses PAIR's prompt templates for consistency
- Aggressive pruning (`tree_width=10`) to prevent exponential tree explosion
- Gap analysis documented in `docs/GAP_ANALYSIS_PHASE3.md`

---

### Phase 4: LangGraph Orchestration
**Objective**: Multi-agent coordination via supervisor-worker architecture.

**Deliverables**:
- `src/redthread/orchestration/supervisor.py` — LangGraph StateGraph with 6 nodes
- `src/redthread/orchestration/graphs/attack_graph.py` — Attack worker subgraph
- `src/redthread/orchestration/graphs/judge_graph.py` — Judge worker subgraph
- `src/redthread/orchestration/graphs/defense_graph.py` — Defense worker subgraph
- `src/redthread/engine.py` — Refactored to facade over SupervisorGraph
- `tests/test_supervisor.py`

**Key Decisions**:
- LangGraph `Send` API for parallel attack fan-out
- Conditional routing: defense synthesis only triggers on confirmed jailbreaks
- Plain dict state (serializable) for LangGraph compatibility

---

### Phase 4.5: Defense Synthesis & Telemetry
**Objective**: Close the attack loop with automated guardrail generation and drift detection.

**Deliverables**:
- `src/redthread/core/defense_synthesis.py` — 5-step synthesis pipeline (Isolate → Classify → Generate → Validate → Deploy)
- `src/redthread/core/guardrail_loader.py` — Runtime guardrail injection scoped by `target_model + prompt_hash`
- `src/redthread/telemetry/embeddings.py` — Async embedding clients (Ollama/OpenAI)
- `src/redthread/telemetry/drift.py` — K Core-Distance drift detection
- `src/redthread/memory/index.py` — MEMORY.md persistence
- `src/redthread/memory/consolidation.py` — Dream-like knowledge consolidation
- `tests/test_defense.py`, `tests/test_guardrail_loader.py`, `tests/test_telemetry.py`
- `docs/DEFENSE_PIPELINE.md`

**Key Decisions**:
- Defense Architect initially reused Attacker model (flagged as risk in Phase 5A)
- GuardrailLoader uses SHA-256 hash-based scoping for target isolation
- Dependency-light telemetry (numpy + httpx, no PyTorch)

---

### Phase 5A: Anti-Hallucination Baseline ✅
**Objective**: Establish the evaluation baseline. Fix P0 blockers before drift monitoring.

**Status**: Completed 2026-04-03
- **Faithfulness**: 1.00 (Target: ≥ 0.92)
- **Hallucination Rate**: 0.00 (Target: ≤ 0.08)
- **Jailbreak Precision**: 1.00 (Target: ≥ 0.90)
- **Safe Recall**: 1.00 (Target: ≥ 0.90)

**Prerequisites Completed**:
- **P0.1**: Defense Architect model decoupled from Attacker (new `defense_architect_model` in settings, default GPT-4o, temperature=0.1)
- **P0.2**: Golden Dataset created (30 curated traces: 10 jailbreak, 10 safe, 10 guardrail)
- **P0.3**: DeepEval-style evaluation pipeline (`evaluation/pipeline.py`)
- **P1.1**: Per-role temperature enforcement (`attacker_temperature`, `judge_temperature`, `defense_architect_temperature`)

**New Files**:
- `src/redthread/evaluation/pipeline.py` — CI/CD evaluation pipeline
- `tests/golden_dataset/golden_traces.py` — 30 curated test cases
- `tests/test_golden_dataset.py` — Regression test suite
- `docs/ANTI_HALLUCINATION_SOP.md` — General anti-hallucination engineering standard
- `docs/PHASE_REGISTRY.md` — This document

**Key Decisions**:
- **Evaluation Framework**: DeepEval (Pytest-native) exclusively. RAGAS deferred to avoid bloat.
- **Defense Architect Model**: Configurable, default GPT-4o with temperature=0.1. Decoupled from Attacker.
- **Observability**: LangSmith (first-party LangGraph support). Deferred to Phase 5D.
- **Golden Dataset**: Hybrid (synthetic bootstrap + manual curation).
- **Scope**: Phase 5A only. Phases 5B-5D deferred until baseline is mathematically proven stable.
- **Evaluation Truth Boundary**: sealed dry-run golden regression, successful live judge scoring, and live-judge fallback scoring are different evidence classes and must be reported separately.

**CI/CD Thresholds**:
| Metric | Threshold |
|---|---|
| Faithfulness | ≥ 0.92 |
| Hallucination Rate | ≤ 0.08 |
| Jailbreak Precision | ≥ 0.90 |
| Safe Recall | ≥ 0.90 |

---

### Phase 5B: ARIMA & ASI *(In Progress → Complete)*
**Objective**: Detect agent degradation statistically before full jailbreaks occur.

**Prerequisites Completed**:
- **G1**: `pmdarima>=2.0.0` + `scipy>=1.13.0` added to `pyproject.toml`
- **G2**: `telemetry/models.py` — `TelemetryRecord`, `ArimaForecast`, `ASIReport`
- **G3**: 4 new settings (`telemetry_enabled`, `asi_window_size`, `arima_confidence_level`, `asi_alert_threshold=60.0`)
- **G4**: `TelemetryCollector` upgraded to active probe with 5 canary prompts + `inject_canary_batch()`
- **G5**: `engine.py._run_telemetry_pass()` — post-campaign hook that runs ASI and attaches report to `CampaignResult.metadata`

**New Files**:
- `src/redthread/telemetry/models.py` — `TelemetryRecord`, `ArimaForecast`, `ASIReport` Pydantic models
- `src/redthread/telemetry/collector.py` — Active probe with canary injection and JSONL export
- `src/redthread/telemetry/arima.py` — `ArimaDetector` (pmdarima auto_arima + Z-score fallback)
- `src/redthread/telemetry/asi.py` — `AgentStabilityIndex` (30/30/25/15 weights, 0-100 score)
- `tests/test_arima.py` — 8 ARIMA-specific tests
- `tests/test_asi.py` — 11 ASI composite score tests

**Key Decisions**:
- **ARIMA**: `pmdarima.auto_arima` (dynamic order selection) — prevents silent false negatives from hardcoded (p,d,q)
- **Canary Prompts**: 5 deterministic benign probes (date, summary, math, repeat, geography) — noise-free RC control group
- **ASI Weights**: Response Consistency (0.30) + Semantic Drift (0.30) dominate — semantic > operational
- **Alert Threshold**: 60.0 — tripwire for Phase 5C campaign trigger, avoids alert fatigue
- **Integration**: Post-campaign only (not mid-campaign) — preserves attack velocity in supervisor. Current runtime path is probe-first, so ASI is an operator signal rather than proof of full benign utility.
- **Storage**: In-memory + JSONL export for Phase 5B; SQLite deferred to Phase 5C daemon

**Verification**:
- 40/40 tests pass (22 new + 18 existing)
- ASI weights sum = 1.0
- All import chain validated


### Phase 5C: Continuous Monitoring ✅
**Objective**: Autonomous background health monitoring with drift-triggered campaign execution.

**Status**: Completed 2026-04-04

**Deliverables**:
- `src/redthread/telemetry/storage.py` — SQLite-backed TelemetryStorage (persistent across probe cycles)
- `src/redthread/telemetry/__init__.py` — Package init
- `src/redthread/daemon/__init__.py` — Daemon package init
- `src/redthread/daemon/monitor.py` — SecurityGuardDaemon with asyncio loop + circuit breaker
- `src/redthread/config/settings.py` — `monitor_probe_interval`, `monitor_auto_campaign`, `monitor_cooldown_period`
- `src/redthread/engine.py` — Wired TelemetryStorage into telemetry pass

**Key Decisions**:
- **SQLite storage**: TelemetryCollector delegates to TelemetryStorage for cross-cycle persistence (G3 fix)
- **Drift baseline warmup**: Daemon runs a warmup phase to bootstrap `fit_baseline()` (G2 fix). Current warmup uses canary probes, so this baseline is continuity-grade monitoring evidence, not proof-grade benign validation.  
- **Circuit breaker**: `monitor_cooldown_period=1800s` — prevents runaway auto-campaigns (G6 fix)
- **Persistent collector**: Daemon holds a single collector instance across probe cycles (G5 fix)

---

### Phase 5D: CI/CD Integration ✅
**Objective**: Close the development lifecycle. Every PR passes automated quality gates before merge.

**Status**: Completed 2026-04-04

**Deliverables**:
- `.github/workflows/ci.yml` — Automated pipeline: quality-gate → unit-tests → golden-regression
- `.github/workflows/nightly-regression.yml` — Nightly full gpt-4o regression with GitHub issue on failure
- `src/redthread/observability/__init__.py` — Observability package
- `src/redthread/observability/tracing.py` — Conditional LangSmith `@traced` decorator + `init_langsmith()`
- `src/redthread/dashboard.py` — `load_campaign_history()` + `render_dashboard()` (Rich table)
- `Makefile` — `lint`, `typecheck`, `test`, `test-golden`, `ci`, `dev`, `install` targets

**Key Decisions**:
| Decision | Choice | Rationale |
|---|---|---|
| Golden Dataset trigger | Every PR + nightly | gpt-4o-mini for PR (cost), gpt-4o for nightly (accuracy) |
| LangSmith scope | Targeted | Mute Attacker (noise). Trace JudgeAgent + DefenseSynthesis only |
| Dashboard data | Campaign JSONL only | SQLite daemon data → Grafana/Metabase (future) |
| Ruff suppressions | Option B | Suppress pre-existing bulk violations, enforce on new code |

**Gap-Check Fixes Applied**:
- **G1** (broken ASI tests): `test_asi.py` updated to use `storage.insert()` instead of `_records.append()`
- **G2** (Ruff 111 errors): 32 auto-fixed via `ruff --fix`, remaining 6 suppressed with targeted ignores
- **G3** (Mypy 22 errors): Per-module `ignore_errors = true` for pre-existing violations, new code clean
- **G4** (langsmith installed): Confirmed — no new dependency needed
- **G5** (.gitignore minimal): Updated with 15+ missing patterns (`__pycache__/`, `.venv/`, `*.db`, etc.)

**CI/CD Pipeline**:
```
push/PR → quality-gate (ruff + mypy) → unit-tests → golden-regression
nightly → golden-regression (gpt-4o) → GitHub issue on failure
```

---

### Phase 6A: Crescendo Algorithm ✅
**Objective**: Implement multi-turn conversational escalation as the third core attack algorithm.

**Status**: Completed 2026-04-04

**Background**: Crescendo exploits the *context-window accumulation effect* — safety training is progressively overridden by conversational coherence pressure as turns accumulate. Unlike PAIR/TAP (single-turn refinement or tree search), Crescendo builds a shared conversation history and advances through 6 escalation levels (0–5).

**Deliverables**:
- `src/redthread/core/crescendo.py` — Escalation loop with client-side history and backtracking
- `tests/test_crescendo.py` — 8 tests covering all algorithm branches (mocked)
- `src/redthread/models.py` — Crescendo trace support alongside existing TAP and MCTS structures
- `src/redthread/config/settings.py` — Crescendo runtime settings added without removing broader attack-surface support
- `src/redthread/orchestration/graphs/attack_graph.py` — Crescendo dispatch path added to the attack worker graph
- `src/redthread/cli.py` — Crescendo controls added to the campaign CLI
- `src/redthread/evaluation/judge.py` — Crescendo trace formatting added to JudgeAgent evaluation

**Key Decisions**:
| Decision | Choice | Rationale |
|---|---|---|
| Phase split | 6A only | Crescendo proves the multi-turn pipeline as a first-class attack family |
| Conversation persistence | Client-side `list[tuple[str,str]]` | Surgical backtracking; PyRIT remains stateless |
| MCTS relationship | Coexists with Crescendo in the live tree | GS-MCTS remains part of the broader offense surface while Crescendo validates the escalation path |
| Cost estimation | Tracked separately from Crescendo | GS-MCTS is compute-heavy; Crescendo is bounded by `max_turns × backtrack_limit` |

**Architecture**:
```
INITIALIZATION
  → benign opener (escalation_level=0)
  → history = []

ESCALATION LOOP (1..max_turns)
  → attacker generates next prompt (system + history + level)
  → target receives full compiled conversation (stateless adapter)
  → judge.evaluate_turn_raw() → per-turn heuristic score

  IF score >= escalation_threshold → accept, advance level
  IF score < threshold → backtrack (up to backtrack_limit times)
  IF limit exceeded → accept partial, advance anyway
  IF score >= success_threshold → early termination

TERMINAL EVALUATION
  → judge.evaluate(trace) → full G-Eval → JudgeVerdict
```

**Verification**:
- 8/8 Crescendo tests pass
- Full regression suite passes with Crescendo added alongside the broader attack surface

---

### Phase 7A: Safe Patch Autoresearch (Offense) ✅
**Objective**: Promote RedThread from bounded prompt/runtime mutation into bounded source-patch autoresearch with explicit operator control.

**Status**: Completed 2026-04-07

**Deliverables**:
- `src/redthread/research/phase5.py` — formal Phase 5 wrapper for bounded source mutation cycles
- `research phase5 cycle|inspect|revert` — official CLI entrypoints
- enriched Phase 3 proposals with mutation provenance and promotion readiness metadata
- explicit research-plane acceptance gate before promotion
- `docs/AUTORESEARCH_PHASE5.md` — source-patch autoresearch contract

**Key Decisions**:
| Decision | Choice | Rationale |
|---|---|---|
| Mutation style | Template-driven only | Keeps code mutation deterministic and reversible |
| Safety boundary | Phase 3 accept/reject remains mandatory | Promotion must not bypass operator approval |
| Protected surfaces | evaluation, defense, telemetry, golden dataset, promotion logic | Prevents autoresearch from mutating its own safety gates |
| CLI strategy | `phase5` is official, `mutate` remains compatible | Preserves existing workflows while clarifying roadmap direction |

### Phase 7B: Bounded Defense Prompt Autoresearch ✅
**Objective**: Add a conservative defense-side autoresearch lane without opening runtime defense logic or production safety gates to mutation.

**Status**: Completed 2026-04-08

**Deliverables**:
- `src/redthread/research/phase6.py` — formal Phase 6 wrapper for bounded defense prompt mutation cycles
- `research phase6 cycle|inspect|revert` — official CLI entrypoints
- `src/redthread/research/defense_source_mutation_registry.py` — defense prompt mutation templates
- `src/redthread/research/defense_source_mutation_policy.py` — defense-only mutation surface policy
- `src/redthread/research/defense_source_mutation_validator.py` — sealed pre-apply validation gate
- additive mutation-phase provenance in Phase 3 proposals and source-mutation manifests
- `docs/AUTORESEARCH_PHASE6.md` — defense prompt autoresearch contract

**Key Decisions**:
| Decision | Choice | Rationale |
|---|---|---|
| Mutable surface | defense prompt/template assets only | Keeps runtime defense logic and benign pack sealed |
| Validation gate | deterministic pre-apply checks | Rejected candidates must fail closed before entering Phase 3 |
| Proposal flow | reuse existing Phase 3 / promotion flow | Avoids creating a second promotion plane |
| Scope control | prompt-contract only in v1 | Conservative first step before richer replay fixtures |

### Phase 8A: Agentic Security Schema ✅
**Objective**: Add the shared data contracts needed for tool hijacking, confused deputy, deterministic containment, and resource amplification work without changing the existing attack and defense engines.

**Status**: Completed 2026-04-16

**Deliverables**:
- `src/redthread/orchestration/models/agentic_security.py` — additive schema for agentic-security runtime concepts
- `src/redthread/orchestration/models/__init__.py` — focused exports for the new orchestration-local models
- `docs/AGENTIC_SECURITY_THREAT_MODEL.md` — reference vocabulary for the new threat families and trust boundaries
- `tests/test_agentic_security_models.py` — serialization and runtime-summary coverage for the new schema
- `src/redthread/orchestration/runtime_summary.py` — additive agentic-security summary shape for future runtime reporting

**Key Decisions**:
| Decision | Choice | Rationale |
|---|---|---|
| Model placement | orchestration-local models module | Avoids bloating `src/redthread/models.py`, which already carries core campaign types |
| Runtime impact | additive and optional only | Existing campaign flow remains unchanged until later Phase 8 work plugs into the new schema |
| Scope control | schema only, no live interception yet | Keeps 8A low-risk and replay-first |
| Reporting shape | nested `agentic_security` summary block | Extends operator truth surfaces without breaking existing top-level fields |

### Phase 8B: Attack Simulation Lane ✅
**Objective**: Add deterministic agentic-security scenario runners so RedThread can test tool hijacking, confused deputy chains, and resource amplification without relying on live tool infrastructure first.

**Status**: Completed 2026-04-16

**Deliverables**:
- `src/redthread/tools/fixtures/agentic_security.py` — sealed benign, poisoned, ToolLeak, and repair-loop fixtures
- `src/redthread/tools/fixtures/__init__.py` — focused exports for deterministic scenario fixtures
- `src/redthread/tools/simulated_registry.py` — replay-safe simulated tool registry
- `src/redthread/orchestration/graphs/tool_attack_graph.py` — sealed tool-attack scenario runner
- `src/redthread/orchestration/scenarios/confused_deputy.py` — privilege-laundering scenario runner
- `src/redthread/orchestration/scenarios/resource_amplification.py` — loop and budget-amplification scenario runner
- `tests/test_agentic_security_scenarios.py` — deterministic scenario coverage

**Key Decisions**:
| Decision | Choice | Rationale |
|---|---|---|
| Infrastructure style | sealed simulation first | Preserves replay-first evidence discipline before any live MCP work |
| Scenario granularity | one file per threat family | Keeps future expansion under the repo file-size limit |
| Registry behavior | deterministic dict-backed fixture registry | Makes attack traces reproducible and CI-safe |
| Runtime integration | scenario lane stays additive | Existing supervisor and attack algorithms remain unchanged |

### Phase 8C: Deterministic Control Plane ✅
**Objective**: Add rigid pre-action authorization and permission inheritance checks so RedThread can prove whether risky actions would be allowed, denied, or escalated before execution.

**Status**: Completed 2026-04-16

**Deliverables**:
- `src/redthread/tools/authorization/models.py` — deterministic policy schema
- `src/redthread/tools/authorization/engine.py` — authorization engine returning structured decisions
- `src/redthread/tools/authorization/presets.py` — least-agency policy presets
- `src/redthread/tools/authorization/__init__.py` — additive package exports
- `src/redthread/orchestration/permission_inheritance.py` — lineage guard for high-risk capabilities
- `tests/test_authorization_engine.py` — allow/deny/escalate coverage across sealed scenarios

**Key Decisions**:
| Decision | Choice | Rationale |
|---|---|---|
| Policy path | non-LLM and deterministic | Keeps execution controls outside prompt semantics |
| Inheritance rule | fail closed on derived untrusted lineage for high-risk capabilities | Directly addresses confused-deputy and tool-poisoning chains |
| Preset style | least-agency role bundles | Gives operators a reusable starting point for policy modeling |
| Runtime scope | simulation and replay first | Avoids over-claiming live enforcement before later phases wire real interception |

### Phase 8D: Canary & Runtime Containment ✅
**Objective**: Add propagation-aware tracing and budget containment so RedThread can show where poisoned context spread and where expensive loops should be stopped.

**Status**: Completed 2026-04-16

**Deliverables**:
- `src/redthread/telemetry/canaries.py` — canary injection and merge helpers
- `src/redthread/orchestration/canary_flow.py` — stage-by-stage propagation reports
- `src/redthread/telemetry/runtime_budgets.py` — deterministic runtime budget evaluator
- `src/redthread/orchestration/runtime_summary.py` — additive canary and budget reporting fields
- `tests/test_canary_containment.py` — canary flow and budget stop coverage

**Key Decisions**:
| Decision | Choice | Rationale |
|---|---|---|
| Canary reporting | stage list to compact report | Makes spread-path evidence inspectable without overcomplicating runtime state |
| Budget control | deterministic threshold gate | Keeps amplification containment replay-safe and CI-friendly |
| Summary impact | additive nested fields | Preserves existing operator truth surfaces while exposing new containment signals |
| Scope control | sealed reporting only in v1 | Live hook wiring remains deferred to the next phase |
