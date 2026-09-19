---
title: Launch Readiness Verification
type: research
status: implemented
summary: Named launch preset, evidence gates, bounded baseline replay, and external-review artifact limits for issue 19.
source_of_truth:
  - docs/research/open-issues-spec.md
  - src/redthread/launch_readiness/cli.py
  - src/redthread/launch_readiness/evaluator.py
  - src/redthread/launch_readiness/evidence.py
  - tests/test_launch_readiness.py
updated_by: codex
updated_at: 2026-09-18
---

# Launch Readiness Verification

## Delivered workflow

`redthread run --preset launch-readiness` runs PAIR, TAP, and Crescendo through the existing engine. Each strategy receives the configured target, objective, rubric, and runtime settings. Standard report bundles go under `reports/launch-readiness/strategies/<strategy>/` by default. Aggregate executive Markdown and prompt-safe JSON go in the parent directory. Existing report-path and sidecar options remain available. See [CLI adapter](../../../src/redthread/launch_readiness/cli.py), [outputs](../../../src/redthread/launch_readiness/outputs.py), and [implementation record](../../research/launch-readiness-implementation.md).

Executive decision and gates precede reported findings. Packet contains counts, evidence labels, replay status, unknowns, and an explicit reproduction-details placeholder. It excludes raw prompts/responses. Detailed campaign reports retain the normal project reporting contract and are separate from this external-review packet. See [packet renderer](../../../src/redthread/launch_readiness/packet.py).

## Evidence boundaries

Required strategies must have nonempty completed results. Every trace needs live JudgeAgent evidence; campaign runtime mode alone does not suffice. Missing, error, skipped, sealed, or fallback-only proof cannot pass default gates. Fallback remains diagnostic and non-promotable. High findings above the configured limit block readiness. See [evaluator](../../../src/redthread/launch_readiness/evaluator.py) and [gate policy](../../../src/redthread/launch_readiness/gates.py).

Clean traces receive separate baseline replay evidence through the existing bounded exploit/benign runner. Baseline uses the final available attack prompt as a single-turn probe, preserves target system-prompt scope, and does not synthesize a defense or create a deployment record. It does not replay the full original multi-turn interaction. Case scoring uses the existing replay scorer; it is not another independent live JudgeAgent verdict. Findings require matching live candidate-defense validation instead. See [baseline attachment](../../../src/redthread/launch_readiness/baseline.py), [replay runner](../../../src/redthread/core/defense_replay_runner.py), and [provenance checks](../../../src/redthread/launch_readiness/evidence.py).

`ready` means configured evidence gates passed for observed scope. It does not authorize release, certify safety, establish capability uplift, activate guardrails, or replace human review. Scope/capability uplift remain explicitly unknown. Defense promotion remains separate.

## Verification

[Launch tests](../../../tests/test_launch_readiness.py) cover gate outcomes, incomplete proof, mixed clean/finding traces, scope matching, strategy failures, packet redaction, report ordering, CLI strategy expansion, and baseline runner behavior. [Integrated verification](open-issues-final-verification.md) records final test counts and independent review.

## Related evidence

- [Issue 19](https://github.com/matheusht/redthread/issues/19)
- [Active specification](../../research/open-issues-spec.md)
- [Scope ledger](open-issues-implementation-map.md)
