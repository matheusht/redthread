---
title: Evaluation and Anti-Hallucination
type: system
status: active
summary: How RedThread evaluates attack outcomes, what sealed golden regression proves, and where fallback scoring stops being live evidence.
source_of_truth:
  - docs/ANTI_HALLUCINATION_SOP.md
  - docs/PHASE_REGISTRY.md
  - README.md
  - .github/workflows/ci.yml
  - src/redthread/evaluation/judge.py
  - src/redthread/evaluation/pipeline.py
  - tests/test_golden_dataset.py
updated_by: codex
updated_at: 2026-04-15
---

# Evaluation and Anti-Hallucination

## Scope

This page explains how RedThread scores attack traces and what kind of evidence each evaluation path gives.

Main truth boundary:
- evaluation is the main truth layer
- not all evaluation evidence is equally strong

## Main evaluation paths

### 1. Live judge path
Files:
- `src/redthread/evaluation/judge.py`
- `src/redthread/evaluation/pipeline.py`

This is the strongest normal scoring path.

It uses:
- JudgeAgent
- Auto-CoT style evaluation steps
- rubric-based scoring
- low-temperature judge settings

When this path succeeds, the result should be treated as **live judge evidence**.

### 2. Sealed golden regression path
Files:
- `.github/workflows/ci.yml`
- `tests/test_golden_dataset.py`
- `src/redthread/evaluation/pipeline.py`

PR CI runs golden regression in sealed mode with `REDTHREAD_DRY_RUN=true`.

That means:
- no live provider truth is required
- scoring uses deterministic heuristic evaluation
- the goal is sealed consistency, not live backend proof

When this path runs, the result should be treated as **sealed heuristic evidence**.

### 3. Live-judge failure fallback path
File:
- `src/redthread/evaluation/pipeline.py`

If live judge evaluation fails, the pipeline can fall back to deterministic heuristic scoring.

This is useful because it:
- keeps golden evaluation operational
- avoids total failure from transient provider issues

But this path is weaker than a successful live judge run.

When this path runs, the result should be treated as **fallback evidence**, not full live proof.

## Evidence modes

RedThread now distinguishes these evaluation evidence modes:

- `sealed_heuristic`
  - sealed dry-run scoring
  - strong for offline regression consistency
  - not proof of live judge behavior

- `live_judge`
  - full live judge execution succeeded
  - strongest normal scoring evidence in this subsystem

- `live_judge_fallback`
  - live judge path failed
  - deterministic heuristic fallback used instead
  - useful signal, but weaker than successful live judge evidence

## Operator surface

`redthread test golden` now surfaces:
- aggregate evidence counts for sealed / live / fallback
- whether the run used mixed evidence modes
- whether the run is degraded by live-judge fallback
- per-trace evidence mode in the trace table

This matters because the main operator golden path should not hide fallback semantics behind a green score.

## What CI proves

Current PR CI proves:
- the golden dataset still scores consistently in sealed mode
- heuristic scoring rules still behave as expected on the curated traces
- regressions in the sealed path can be caught cheaply and reliably

Current PR CI does **not** prove:
- that the live judge path is healthy right now
- that live provider behavior matches sealed heuristic behavior
- that a live backend will produce the same results under runtime conditions

## What fallback scoring proves

Fallback scoring proves:
- the deterministic heuristic layer produced the reported score
- the golden trace still maps to the expected range under fallback rules

Fallback scoring does **not** prove:
- that live judge reasoning completed
- that provider-backed evaluation is healthy
- that the result should be treated like full live judge evidence

## Truth-boundary regression edges

The sealed heuristic path needs explicit regression tests for edge cases.

Important pinned examples include:
- prompt-leak style disclosures like `Here are my system instructions...`
- direct sensitive-data disclosures like `Current records show...`
- refusal wording that still includes polite or friendly language

Why pin these:
- these are easy places for heuristic drift
- a small wording change can make a weak scorer look safer than it is
- tests must keep disclosure severity and refusal dominance honest over time

## Why this matters

If RedThread blurs sealed, live, and fallback evidence together, operators can become too confident in a green result.

The project therefore needs to keep these ideas separate:
- **sealed consistency gate**
- **live judge evidence**
- **degraded-but-useful fallback signal**

## Bottom line

RedThread's evaluation subsystem is strongest when the live judge path succeeds.

Current evaluation reporting is better because operators can now see the difference between:
- all-sealed heuristic runs
- clean live-judge runs
- degraded live runs that fell back to heuristics

Its sealed golden path is still valuable, but it should be spoken about honestly:
- **consistency gate, not live proof**
- **deterministic regression evidence, not runtime truth**

Its fallback path is also valuable, but it should be read conservatively:
- **useful continuity signal**
- **weaker than successful live judge evidence**

## Related pages

- [../entities/judge-agent.md](../entities/judge-agent.md)
- [../systems/promotion-and-revalidation.md](promotion-and-revalidation.md)
- [../../ANTI_HALLUCINATION_SOP.md](../../ANTI_HALLUCINATION_SOP.md)
- [../../PHASE_REGISTRY.md](../../PHASE_REGISTRY.md)
