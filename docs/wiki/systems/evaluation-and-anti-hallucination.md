---
title: Evaluation and Anti-Hallucination
type: system
status: active
summary: How RedThread evaluates attack outcomes and constrains hallucination in high-stakes generation paths.
source_of_truth:
  - docs/ANTI_HALLUCINATION_SOP.md
  - docs/PHASE_REGISTRY.md
updated_by: codex
updated_at: 2026-04-13
---

# Evaluation and Anti-Hallucination

## Scope

This page summarizes the evaluation baseline RedThread uses to keep scoring, defense generation, and grounded responses reliable.

## Core idea

RedThread treats hallucination control as an engineering standard, not prompt polish.

The main controls are:
- grounded prompts
- structured outputs
- per-role temperature settings
- sealed regression datasets
- CI thresholds

## Main components

### Judge and scoring behavior
Evaluation is designed to be deterministic or near-deterministic in high-stakes paths.

Key patterns:
- Judge temperature is pinned low for reproducibility.
- Defense generation is near-deterministic rather than creative.
- Creative temperature is reserved for attacker roles, not evaluators.

### Golden dataset
The baseline requires a curated dataset with jailbreak, safe, and edge cases.

The current documented baseline includes:
- jailbreak cases
- safe cases
- guardrail validation cases

### CI/CD gating
The anti-hallucination baseline is enforced through explicit metrics rather than qualitative impressions.

Examples documented in the source material:
- faithfulness threshold
- hallucination-rate ceiling
- jailbreak precision threshold
- safe recall threshold

## Why it matters

Without this layer, RedThread could produce:
- unreliable judge outcomes
- overconfident defense synthesis
- unstable regression decisions

That would undermine the whole self-healing loop.

## Relationship to the knowledge system

This topic should be treated as high-impact. Wiki summaries here must remain traceable to the source SOP and phase history rather than drifting into uncited restatements.

## Related pages

- [knowledge-stack.md](knowledge-stack.md)
- [../../ANTI_HALLUCINATION_SOP.md](../../ANTI_HALLUCINATION_SOP.md)
- [../../PHASE_REGISTRY.md](../../PHASE_REGISTRY.md)
