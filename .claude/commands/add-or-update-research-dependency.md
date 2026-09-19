---
name: add-or-update-research-dependency
description: Workflow command scaffold for add-or-update-research-dependency in redthread.
allowed_tools: ["Bash", "Read", "Write", "Grep", "Glob"]
---

# /add-or-update-research-dependency

Use this workflow when working on **add-or-update-research-dependency** in `redthread`.

## Goal

Adds or updates an optional research dependency (e.g., gepa, litellm) and ensures it is properly pinned and grouped in pyproject.toml and lockfile.

## Common Files

- `pyproject.toml`
- `uv.lock`
- `src/redthread/research/*.py`

## Suggested Sequence

1. Understand the current state and failure mode before editing.
2. Make the smallest coherent change that satisfies the workflow goal.
3. Run the most relevant verification for touched files.
4. Summarize what changed and what still needs review.

## Typical Commit Signals

- Edit pyproject.toml to add or update the dependency under an [optional] group (e.g., [research-gepa])
- Update uv.lock to reflect the new/updated dependency
- Ensure that the dependency is imported lazily or optionally in the relevant research module
- Verify that core installs do not require the optional dependency

## Notes

- Treat this as a scaffold, not a hard-coded script.
- Update the command if the workflow evolves materially.