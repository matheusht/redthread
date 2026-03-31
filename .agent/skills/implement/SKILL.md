---
name: Implementation Execution
description: Isolated task-building phase after approval. Strongly encourages Subagents.
---

# Implementation Skill

## Trigger condition:
When the user has formally accepted the `implementation_plan.md` via UI response.

## Execution Requirements:
1. **Context Constriction (<= 40%)**: At this phase, the Principal Agent's intelligence drops drastically as window utilizes over 40%.
2. **Subagent Delegation:**
    - For massive editing, hand off files to an "Implement" Parallel Agent.
    - If a task breaks boundaries (e.g. creating both a PersonaGenerator and an AttackRunner node), build nodes one-by-one or delegate.
3. Validate steps iteratively against the tracking `task.md`.
4. Run testing commands via bash continuously; do not write entire codebases without compiling/testing in real time.
