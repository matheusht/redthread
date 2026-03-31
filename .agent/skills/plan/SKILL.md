---
name: Structured Planning Mode
description: Defines the formal step-by-step logic map before taking action.
---

# Planning Mode Skill

## Trigger condition:
When the "Research" phase is complete, or when instructed to plan an architectural deviation.

## Executing the Plan Skill:
1. Retrieve context mapped out during the Research phase (within 25–35% total context utility).
2. Generate an `implementation_plan.md` artifact.
3. Structure your plan according to the RedThread specific methodologies (e.g., mapping MCTS or TAP attack paths).
4. Do **not** execute any bash or code modification tools during planning. We must remain stateless.
5. You must request User Approval (via `request_feedback: true`) prior to advancing to Implementation.
