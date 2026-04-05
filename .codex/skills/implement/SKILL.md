---
name: implement
description: Execute an approved plan with focused edits, iterative verification, and strict attention to repo boundaries.
---

# Implementation Skill

Use this skill when research and planning are complete.

## Execution Rules

1. Edit only the files required by the plan.
2. Verify incrementally with focused commands.
3. Keep context tight around the touched paths.
4. Split work if one file or subsystem starts carrying too much responsibility.
5. Report verification results and any remaining risks.

## Practical Checks

- targeted `pytest` for touched modules
- `ruff check` for touched packages when practical
- `mypy` on the narrowest relevant surface when practical
