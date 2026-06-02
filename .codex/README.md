# Codex Workspace Guide

This directory mirrors the repository's `.agent/` operating model for Codex.

Codex-specific files are a mirror, not the source of truth. Start with `AGENTS.md`, `docs/ai-context-summary.md`, `docs/context-index.md`, and `docs/AGENT_DECISION_TREE.md`, then load focused docs on demand.

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
2. `docs/ai-context-summary.md`
3. `docs/context-index.md`
4. `README.md`
5. `docs/AGENT_DECISION_TREE.md`
6. `docs/RPI_METHODOLOGY.md`
7. the focused docs that match the current task

When `.agent/` and `docs/` disagree, prefer the live documents in `docs/` plus the current repository structure.

## Mirror Policy

When changing shared behavior, update `AGENTS.md` or the relevant `docs/` source first. Then update `.codex/` and `.agent/` if the behavior applies to both tools. If Codex needs a different local rule, write the reason here instead of silently drifting.
