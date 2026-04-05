---
name: feature-rpi
description: Full research-plan-implement workflow for new features, architectural updates, multi-file changes, or any task with non-trivial blast radius in RedThread.
---

# Feature RPI

Use this skill for medium and large changes.

## Start

Open these first:

- `README.md`
- `docs/TECH_STACK.md`
- `docs/RPI_METHODOLOGY.md`
- `AGENTS.md`
- one or more of:
  - `docs/AGENT_ARCHITECTURE.md`
  - `docs/ANTI_HALLUCINATION_SOP.md`
  - `docs/PHASE_REGISTRY.md`
  - `docs/algorithms.md`

## Research

- identify the real execution path before editing
- inspect affected interfaces, neighboring modules, and verification points
- capture file paths, constraints, and open risks
- keep reading focused; do not preload unrelated subsystems

## Plan

- produce a short numbered plan before editing
- name touched files or areas
- define acceptance criteria and verification commands
- run the `gap-check` skill if the change affects architecture, scoring, safety, or orchestration

## Implement

- make the smallest coherent multi-file change set
- preserve separation of concerns from `AGENTS.md`
- keep files under the 200-line guideline
- verify iteratively instead of waiting until the end

## Verification

- run focused tests or lint/typecheck commands for the touched surface
- if full verification is not possible, state what was or was not run

## Stop And Rescope When

- the task crosses into an unexpected subsystem
- the plan assumptions no longer hold
- context is approaching the dumb zone
