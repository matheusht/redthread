---
name: gap-check
description: Audit a plan for missing architecture, evaluation, safety, or verification coverage before implementation.
---

# Gap-Check Skill

Use this skill before executing a complex plan.

## Check For Gaps In

1. Architecture boundaries from `AGENTS.md`
2. Algorithm alignment from `docs/algorithms.md`
3. Agent orchestration expectations from `docs/AGENT_ARCHITECTURE.md`
4. Evaluation and anti-hallucination requirements from `docs/ANTI_HALLUCINATION_SOP.md`
5. Phase consistency from `docs/PHASE_REGISTRY.md`

## Output

- confirmed assumptions
- missing risks or edge cases
- missing tests or validation
- any reason to split the work further
