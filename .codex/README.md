# Codex Workspace Guide

This directory mirrors the repository's `.agent/` operating model for Codex.

## Purpose

- keep Codex-specific navigation rules close to the repo
- point workflows at the current source-of-truth docs under `docs/`
- provide lightweight skills for research, planning, and implementation

## Structure

- `rules/` contains always-on operating constraints
- `skills/` contains intent-based workflows such as `feature-rpi` and `mini-rpi`

## Source Of Truth

Behavioral guidance should come from:

1. `AGENTS.md`
2. `README.md`
3. `docs/AGENT_DECISION_TREE.md`
4. `docs/RPI_METHODOLOGY.md`
5. the focused docs that match the current task

When `.agent/` and `docs/` disagree, prefer the live documents in `docs/` plus the current repository structure.
