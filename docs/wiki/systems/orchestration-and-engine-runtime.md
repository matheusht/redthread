---
title: Orchestration and Engine Runtime
type: system
status: active
summary: How RedThread's engine facade, LangGraph supervisor, worker flow, and runtime artifacts behave in sealed dry-run versus degraded or live execution.
source_of_truth:
  - README.md
  - docs/PHASE_REGISTRY.md
  - docs/REDTHREAD_STATUS_AUDIT.md
  - src/redthread/engine.py
  - src/redthread/runtime_modes.py
  - src/redthread/orchestration/supervisor.py
  - src/redthread/orchestration/runtime_summary.py
  - src/redthread/orchestration/graphs/attack_graph.py
  - src/redthread/orchestration/graphs/judge_graph.py
  - src/redthread/orchestration/graphs/defense_graph.py
  - tests/test_runtime_truth.py
  - tests/test_supervisor.py
updated_by: codex
updated_at: 2026-04-15
---

# Orchestration and Engine Runtime

## Scope

This page covers the runtime path from CLI to transcript:
- `src/redthread/engine.py`
- `src/redthread/orchestration/supervisor.py`
- attack, judge, and defense worker boundaries
- runtime-mode labels and degraded-runtime reporting

## Runtime flow

Current runtime flow is:
1. CLI builds `CampaignConfig`
2. `RedThreadEngine.run()` calls `RedThreadSupervisor.invoke()`
3. supervisor injects scoped guardrails into the prompt copy
4. personas are generated
5. attack workers fan out in parallel via LangGraph `Send`
6. results are collected
7. judge workers run over collected results
8. defense synthesis runs only for confirmed jailbreaks
9. supervisor finalizes `CampaignResult`
10. engine writes JSONL transcript
11. optional telemetry runs after the campaign

## What is parallel vs serial

Current truth:
- **attack workers** are parallel fan-out workers
- **judge evaluation** is currently a sequential loop
- **defense synthesis** is currently a sequential loop

So the runtime is a real supervisor-worker system, but it is **not** fully parallel end to end.

## Runtime modes

Files:
- `src/redthread/runtime_modes.py`
- `src/redthread/engine.py`
- `tests/test_runtime_truth.py`

Campaign execution currently labels runtime mode explicitly:
- `sealed_dry_run`
- `live_provider`

Telemetry execution currently labels:
- `skipped_in_dry_run`
- `live_provider`

This means dry-run and live execution are now distinguishable in:
- campaign metadata
- transcript summary lines

## Degraded runtime reporting

Files:
- `src/redthread/orchestration/runtime_summary.py`
- `src/redthread/orchestration/supervisor.py`
- `src/redthread/engine.py`

The runtime now records a compact summary for operators:
- `attack_worker_total`
- `attack_worker_failures`
- `judge_worker_total`
- `judge_worker_failures`
- `defense_worker_total`
- `defense_worker_failures`
- `defense_deployments`
- `degraded_runtime`
- `error_count`
- `error_samples`

This is important because the runtime is currently **best-effort**, not fail-closed.

## Current failure semantics

### Attack worker failure
- failed worker returns `result_dict=None`
- supervisor records an error
- campaign continues with surviving results

### Judge worker failure
- worker records an error
- judged result still passes through for continuity
- per-trace metadata marks this as `live_judge_error_passthrough`
- transcript attack-result lines expose both `judge_runtime_status` and `judge_error`
- runtime should be read as degraded, not clean live proof

### Defense worker failure
- worker records an error
- campaign still finalizes
- defense deployment count can stay below defense input count

## Operator surfaces

Current operator-visible runtime surfaces are:
- transcript summary JSONL line
- dashboard history table
- guardrail injection audit JSONL

The dashboard now shows:
- runtime mode
- telemetry mode
- clean vs degraded runtime state
- compact worker-failure counts as `A/J/D`

## What transcripts and dashboard prove

Current transcript summary and dashboard now prove:
- whether the campaign was sealed or live
- whether telemetry ran or was skipped
- whether runtime degraded due to worker failures
- compact failure counts across attack, judge, and defense stages
- whether a trace stayed on sealed passthrough or degraded into live judge error passthrough

Current transcript summary and dashboard do **not** prove:
- that live providers were healthy across every stage unless a live smoke path also succeeded
- that a green campaign had no runtime degradation unless `degraded_runtime=false`
- that telemetry is proof of benign utility

## Open trust gaps

Still open:
- small opt-in live smoke path for real provider workflow
- stronger operator surfaces beyond raw transcript summary
- more explicit judge-failure passthrough labeling per trace

## Bottom line

RedThread's runtime structure is strong.

The main remaining trust work is not architecture sprawl. It is:
- making degraded execution obvious
- proving a tiny live path end to end
- keeping operator artifacts honest about what runtime really did
