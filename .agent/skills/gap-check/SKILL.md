---
name: Implementation Gap Check
description: Structural audit skill invoked against plans prior to execution to resolve missing edge cases.
---

# Gap-Check Skill

## Trigger condition:
You should execute this skill prior to submitting a complex `implementation_plan.md` for human review, or when the user explicitly requests an audit.

## Executing the Gap Check:
Evaluate the proposed logic against the foundational models described in `docs/AGENT_DECISION_TREE.md`:

1. **Security / Red-Teaming Coverage:** Does the mechanism rely purely on single-turn evaluation, or does it properly branch (e.g., TAP algorithm)?
2. **Evaluation Metrics:** Is there an Auto-CoT JudgeAgent assigned to evaluate the results? If missing, the plan has a gap!
3. **Defense Pipeline:** Will this output synthesize into dynamic guardrails, or is the loop artificially broken?

Generate a gap analysis report in the plan's `Open Questions` section targeting the user.
