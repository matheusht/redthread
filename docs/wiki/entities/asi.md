---
title: ASI
type: entity
status: active
summary: Composite Agent Stability Index used to summarize telemetry health signals while keeping monitoring separate from proof.
source_of_truth:
  - docs/PHASE_REGISTRY.md
  - docs/DEFENSE_PIPELINE.md
  - README.md
updated_by: codex
updated_at: 2026-04-15
---

# ASI

## What it is

ASI stands for **Agent Stability Index**.

It is the composite score RedThread uses to summarize telemetry health signals over time.

## What it measures

ASI combines four things:
- response consistency from repeated canaries
- semantic drift from stored embeddings vs baseline
- operational anomalies from ARIMA checks
- token-count stability as a weak behavioral proxy

## What it is good for

ASI is useful for:
- operator monitoring
- compact health reporting
- alert thresholds
- deciding when deeper investigation is worth running

## What it is not

ASI is not:
- proof of safety
- proof of unsafety
- proof of benign utility retention
- proof that a defense succeeded

A high ASI means telemetry looks stable.
A low ASI means telemetry suggests meaningful change.
Neither one replaces replay validation, judge evidence, or promotion review.

## Relationship to telemetry

ASI is the summary layer inside the broader telemetry and monitoring subsystem.
It is one of the main outputs operators see, but it should always be read together with the report caveats and evidence limits.

## Related pages

- [../systems/telemetry-and-monitoring.md](../systems/telemetry-and-monitoring.md)

## Sources

- [../../PHASE_REGISTRY.md](../../PHASE_REGISTRY.md)
- [../../DEFENSE_PIPELINE.md](../../DEFENSE_PIPELINE.md)
- [../../README.md](../../README.md)
