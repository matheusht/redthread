---
title: Orchestration Runtime Hardening Pass
type: research
status: active
summary: Research and execution log for tightening runtime truth, degraded execution reporting, and operator-facing orchestration evidence.
source_of_truth:
  - README.md
  - docs/PHASE_REGISTRY.md
  - docs/REDTHREAD_STATUS_AUDIT.md
  - docs/wiki/systems/subsystem-focus-map.md
  - src/redthread/engine.py
  - src/redthread/runtime_modes.py
  - src/redthread/orchestration/supervisor.py
  - src/redthread/orchestration/runtime_summary.py
  - src/redthread/dashboard.py
  - tests/test_runtime_truth.py
  - tests/test_supervisor.py
updated_by: codex
updated_at: 2026-04-15
---

# Orchestration Runtime Hardening Pass

## Research question

How do we make RedThread's orchestration and engine runtime easier to trust without adding more workflow complexity than needed?

## Current synthesis

This subsystem is structurally one of the stronger parts of the repo.

Main truth gaps are:
- degraded runtime was too quiet for operators
- transcript summary needed worker-failure counts
- live runtime path still has less proof than dry-run path
- operator surfaces need clearer runtime truth

## Milestones

### Milestone 1 — Runtime degradation metadata and transcript truth
Status: complete

Shipped:
- added `src/redthread/orchestration/runtime_summary.py`
- supervisor now records attack/judge/defense worker counts and failures
- finalized campaigns now carry `runtime_summary`, `degraded_runtime`, and `error_count`
- transcript summary now includes degraded-runtime truth
- added regression coverage in `tests/test_runtime_truth.py` and `tests/test_supervisor.py`

Verification:
- focused: `./scripts/test_then_ci.sh tests/test_runtime_truth.py tests/test_supervisor.py -q`
- local PR-CI mirror: passed
- full suite in mirror: passed (`199 passed` + golden `25 passed`)

### Milestone 2 — Dashboard/operator runtime truth surface
Status: pending

Planned:
- show runtime mode and degraded-runtime signal in dashboard/history surfaces
- expose worker-failure summary without forcing operators to open raw JSONL

### Milestone 3 — Judge passthrough truth + docs closeout
Status: pending

Planned:
- make judge failure passthrough easier to interpret
- add focused runtime truth tests around degraded judge semantics
- close the wiki/docs loop once runtime behavior is final

## Acceptance line

This pass is done when an operator can tell:
- sealed vs live
- clean vs degraded
- where worker failures happened
- what still needs live smoke proof
