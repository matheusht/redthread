---
name: red-teaming-attacks
description: Guidance for attack-algorithm work across PAIR, TAP, MCTS, and Crescendo in RedThread.
---

# Red-Teaming Attacks Skill

Use this skill when building or modifying attack-generation logic.

## Primary References

- `docs/algorithms.md`
- `docs/PHASE_REGISTRY.md`
- `docs/AGENT_ARCHITECTURE.md`
- `docs/TECH_STACK.md`

## Workflow

1. Identify which algorithm is being touched: PAIR, TAP, MCTS, or Crescendo.
2. Trace the orchestration path that invokes it.
3. Confirm scoring and pruning logic still align with evaluation expectations.
4. Verify the change does not collapse separation between orchestration and core algorithms.

## Checks

- branch generation and pruning remain explicit
- attacker, judge, and defense roles stay separated
- evaluation still has a clear rubric path
