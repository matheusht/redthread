---
name: defense-and-eval
description: Guidance for JudgeAgent scoring, guardrail synthesis, and anti-hallucination validation work.
---

# Defense And Evaluation Skill

Use this skill when touching scoring, judging, telemetry, or defense synthesis.

## Focus Areas

1. Judge behavior and rubric grounding
2. Guardrail generation constraints
3. Validation before deployment
4. Anti-hallucination requirements
5. Regression coverage

## Reference Docs

- `docs/ANTI_HALLUCINATION_SOP.md`
- `docs/DEFENSE_PIPELINE.md`
- `docs/PHASE_REGISTRY.md`
- `docs/TECH_STACK.md`

## Guardrails

- keep evaluators deterministic
- keep defense generation near-deterministic and grounded
- never skip regression thinking for guardrail changes
