---
title: Telemetry and Monitoring
type: system
status: active
summary: How RedThread tracks drift, stability, and continuous health monitoring after campaign execution.
source_of_truth:
  - docs/DEFENSE_PIPELINE.md
  - docs/PHASE_REGISTRY.md
updated_by: codex
updated_at: 2026-04-13
---

# Telemetry and Monitoring

## Scope

This page summarizes RedThread's telemetry, drift detection, and continuous monitoring stack.

## Core idea

RedThread does not stop at finding jailbreaks. It also tracks whether target behavior is drifting or degrading over time.

## Main components

### Drift detection
The documented telemetry stack uses embedding-based drift detection.

Key ideas:
- establish a benign baseline
- embed later responses
- compare them against the baseline manifold
- treat large distance increases as potential drift

### ARIMA and ASI
The phase history records a later hardening step that adds:
- ARIMA-based anomaly detection
- ASI as a composite agent stability score

This turns telemetry from passive observation into a more operational health signal.

### Continuous monitoring daemon
The monitoring layer adds recurring health checks and can trigger follow-up behavior when the target appears degraded.

## Why it matters

This protects against a narrow view of success.

A newly injected guardrail might block a jailbreak but still damage normal behavior. Telemetry exists to catch that tradeoff instead of treating refusal alone as a win.

## Risks

- over-triggering on noise
- weak baselines
- hidden utility regressions if benign probes are too shallow

## Related pages

- [evaluation-and-anti-hallucination.md](evaluation-and-anti-hallucination.md)
- [../../DEFENSE_PIPELINE.md](../../DEFENSE_PIPELINE.md)
- [../../PHASE_REGISTRY.md](../../PHASE_REGISTRY.md)
