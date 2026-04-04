---
name: mini-rpi
description: Lightweight research-plan-implement workflow for small tweaks, isolated bugfixes, copy edits, and low-blast-radius polish in this repo. Use when the change can be understood from 1-3 files and stays inside one subsystem without changing shared data flow.
---

# Mini RPI

Use this skill to keep small changes fast without skipping repo rules or opening unnecessary context.

## Start

- Open [README.md](../../../README.md).
- Open [docs/TECH_STACK.md](../../../docs/TECH_STACK.md).
- Open [docs/RPI_METHODOLOGY.md](../../../docs/RPI_METHODOLOGY.md).
- Open [AGENTS.md](../../../AGENTS.md) (RedThread Engineering Standards).
- Open only the focused subsystem doc that matches the tweak.

## Research

- Inspect 1-3 directly relevant files.
- Confirm the change stays inside one subsystem.
- Confirm the tweak does not change shared data flow, persistence, or public interfaces.

## Plan

- State the intended change in one short plan.
- Name the impact surface and quick verification.
- Keep the edit local unless the task proves otherwise.

## Implement

- Patch the smallest affected slice.
- Keep the changed files under the 200-line limit.
- Stop and escalate to [`feature-rpi`](../feature-rpi/SKILL.md) if the change stops being local.
- Run the smallest meaningful verification for the touched behavior.

## Escalate To Feature RPI When

- the tweak touches more than one subsystem
- the tweak changes data flow, persistence, API shape, or tool behavior
- the current file needs structural cleanup before the tweak is safe
- the change risks regressions outside the original area

## Keep Context Lean

- Do not preload unrelated docs or directories.
- Prefer targeted search over broad reads.
- Summarize the current behavior before editing.
- Link to source files instead of duplicating their contents.