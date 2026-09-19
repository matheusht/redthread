---
name: add-new-research-module
description: Workflow command scaffold for add-new-research-module in redthread.
allowed_tools: ["Bash", "Read", "Write", "Grep", "Glob"]
---

# /add-new-research-module

Use this workflow when working on **add-new-research-module** in `redthread`.

## Goal

Implements a new research module or phase, including code, tests, and plumbing for new GEPA phases or components.

## Common Files

- `src/redthread/research/*.py`
- `tests/test_*.py`

## Suggested Sequence

1. Understand the current state and failure mode before editing.
2. Make the smallest coherent change that satisfies the workflow goal.
3. Run the most relevant verification for touched files.
4. Summarize what changed and what still needs review.

## Typical Commit Signals

- Create or modify one or more new Python modules under src/redthread/research/ (e.g., gepa_phase.py, gepa_adapter.py, gepa_pareto.py, etc.)
- Update or add corresponding test files under tests/ (e.g., test_gepa_phase0.py, test_gepa_adapter.py, test_gepa_pareto.py)
- Update or create any necessary supporting files (e.g., models.py, workspace.py) to integrate the new module
- Ensure ruff and mypy pass, and all relevant tests are green

## Notes

- Treat this as a scaffold, not a hard-coded script.
- Update the command if the workflow evolves materially.