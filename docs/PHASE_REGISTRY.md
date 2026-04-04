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
| 5B | ARIMA & ASI | ⬜ Planned | — | `arima.py`, `asi.py`, composite drift metrics |
| 5C | Continuous Monitoring | ⬜ Planned | — | Monitor daemon, drift-triggered campaigns |
| 5D | CI/CD Integration | ⬜ Planned | — | GitHub Actions, regression gates, dashboard |

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
- **Integration**: Post-campaign only (not mid-campaign) — preserves attack velocity in supervisor
- **Storage**: In-memory + JSONL export for Phase 5B; SQLite deferred to Phase 5C daemon

**Verification**:
- 40/40 tests pass (22 new + 18 existing)
- ASI weights sum = 1.0
- All import chain validated


### Phase 5C: Continuous Monitoring *(Planned)*
- Background monitor daemon polling agent responses
- Drift-triggered automatic campaign execution
- Webhook alerting for auto-deployed guardrails

### Phase 5D: CI/CD Integration *(Planned)*
- GitHub Actions: lint → typecheck → test → baseline attack suite
- Block merges if ASR > 0% after guardrail deployment
- Golden Dataset regression on every PR
- LangSmith observability instrumentation
