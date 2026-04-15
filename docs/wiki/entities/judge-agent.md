---
title: JudgeAgent
type: entity
status: active
summary: Evaluation role that scores attack traces and determines whether jailbreak behavior has been confirmed.
source_of_truth:
  - docs/ANTI_HALLUCINATION_SOP.md
  - docs/PHASE_REGISTRY.md
updated_by: codex
updated_at: 2026-04-13
---

# JudgeAgent

## What it is

JudgeAgent is the evaluation role responsible for scoring attack traces and supporting grounded pass/fail style decisions in RedThread.

## Responsibilities

- evaluate attack outcomes
- apply scoring rubrics consistently
- keep evaluation deterministic or near-deterministic
- feed high-confidence outcomes into downstream defense and regression flows

## Why it matters

If JudgeAgent is noisy or weakly grounded, the rest of the self-healing loop becomes unreliable.

RedThread therefore treats evaluation as a first-class reliability and safety layer, not just post-hoc commentary.

## Interfaces

Judge behavior is documented through:
- anti-hallucination and grounding standards
- phase history describing judge/evaluation milestones
- rubric-driven evaluation paths in the implementation docs
- explicit evidence-mode handling in the evaluation pipeline so operators can tell live judge evidence from sealed or fallback scoring

## Truth boundary

JudgeAgent is the strongest normal scoring path in this subsystem when live evaluation succeeds.

But operator trust should still separate three cases:
- live judge success
- sealed dry-run heuristic evaluation
- live-judge failure fallback

JudgeAgent therefore matters not just for score quality, but for keeping the system honest about what kind of evidence a score really is.

## Related pages

- [../systems/evaluation-and-anti-hallucination.md](../systems/evaluation-and-anti-hallucination.md)
- [defense-architect.md](defense-architect.md)

## Sources

- [../../ANTI_HALLUCINATION_SOP.md](../../ANTI_HALLUCINATION_SOP.md)
- [../../PHASE_REGISTRY.md](../../PHASE_REGISTRY.md)
