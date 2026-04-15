---
title: Telemetry and Monitoring
type: system
status: active
summary: How RedThread monitors runtime health, what ASI measures, and where telemetry stops being proof.
source_of_truth:
  - README.md
  - docs/DEFENSE_PIPELINE.md
  - docs/PHASE_REGISTRY.md
updated_by: codex
updated_at: 2026-04-15
---

# Telemetry and Monitoring

## Scope

This page summarizes RedThread's telemetry, drift detection, ASI scoring, and monitoring daemon.

Main truth boundary:
- telemetry is an **operator signal layer**
- telemetry is **not** the same thing as validation truth

## Current runtime path

Telemetry currently runs in two main places.

### 1. Post-campaign telemetry pass
File: `src/redthread/engine.py`

After a campaign finishes, RedThread can:
- inject a canary batch
- load a stored drift baseline if one exists
- compute ASI
- attach the report to campaign metadata and transcript
- export raw telemetry JSONL

Important:
- this is a **post-run diagnostic pass**
- it is not full live tracing of every campaign interaction

### 2. Monitoring daemon
File: `src/redthread/daemon/monitor.py`

The daemon can:
- warm a drift baseline if one is missing
- inject recurring canary probes
- compute ASI on stored telemetry
- trigger a bounded follow-up campaign when the alert threshold is crossed

Important:
- daemon alerts are for **investigation**
- daemon alerts do not by themselves prove safety failure or benign-utility regression

## What telemetry really measures

Telemetry records these main signal families:
- latency
- estimated token counts
- response text
- response embeddings
- error markers
- canary-vs-organic identity

In practice, the current runtime is mostly **probe-first**.
That means the strongest telemetry evidence today comes from canary monitoring passes and whatever organic records are explicitly sent through the collector.

## What ASI means in practice

ASI combines four sub-scores:
- **Response Consistency (30%)** — are repeated canary responses semantically similar over time?
- **Semantic Drift (30%)** — how far do stored organic embeddings move from the fitted baseline manifold?
- **Operational Health (25%)** — do latency, token count, or response length look anomalous?
- **Behavioral Stability (15%)** — are output token counts varying unusually?

This makes ASI useful as a compact health signal.
It does **not** make ASI a proof object.

ASI is best read as:
- a summary of monitoring evidence
- a trigger for closer inspection
- a reason to launch bounded follow-up work

ASI is **not** best read as:
- proof that the model is safe
- proof that the model is unsafe
- proof that benign utility is preserved
- proof that a defense worked

## What drift scores mean

Semantic drift uses K Core-Distance against a stored baseline.

A low drift score suggests:
- the current organic responses are farther from the stored baseline manifold
- meaning-level behavior may have shifted

A low drift score does **not** prove:
- a harmful regression
- a jailbreak vulnerability
- a user-visible utility failure

A strong interpretation depends on baseline quality.
If the baseline is thin, stale, or built from narrow probes, the drift result should be treated conservatively.

## Benign baseline and canary strength

Current strengths:
- canaries are deterministic and stable
- canaries give a noise-light consistency control group
- daemon warmup can ensure telemetry is not completely blind

Current limits:
- canaries are shallow probes, not a broad benign utility suite
- daemon warmup can build the baseline from canary probes, which is useful for continuity but weak as a proof-grade benign baseline
- semantic drift only measures against the embeddings that were actually stored
- if no baseline or no usable organic embeddings exist, some sub-scores default high and must be read with the report caveats

So the current baseline/canary stack is:
- useful for monitoring
- useful for alerting
- not yet strong enough to stand in for full benign validation

## Safe daemon action boundary

Telemetry can safely support:
- health reporting
- alerting operators
- recommending investigation
- launching bounded follow-up campaigns for diagnosis
- cooldown-based rate limiting so monitoring does not spiral

Telemetry should not be treated as enough, by itself, for:
- declaring a target healthy in the strong sense
- declaring a defense validated
- approving promotion or deployment
- claiming a benign baseline is preserved without replay or evaluation evidence

## What telemetry suggests vs what it proves

### Telemetry suggests
- the target may be drifting
- the target may be less consistent
- operational behavior may have changed
- a follow-up campaign or replay check is worth running

### Telemetry proves
- only that the measured telemetry signals changed in the measured way
- only that the scoring logic produced the reported composite score from the available inputs

### Telemetry does not prove
- full benign utility retention
- exploit resistance
- defense correctness
- promotion readiness

## Bottom line

Telemetry is valuable because it widens operator vision beyond simple jailbreak success or failure.

But in RedThread's current runtime, telemetry should be spoken about honestly:
- **signal, not proof**
- **monitoring, not validation**
- **investigation trigger, not final verdict**

## Related pages

- [evaluation-and-anti-hallucination.md](evaluation-and-anti-hallucination.md)
- [../entities/asi.md](../entities/asi.md)
- [../../DEFENSE_PIPELINE.md](../../DEFENSE_PIPELINE.md)
- [../../PHASE_REGISTRY.md](../../PHASE_REGISTRY.md)
