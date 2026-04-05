---
name: mini-rpi
description: Lightweight research-plan-implement workflow for small tweaks, isolated bugfixes, copy edits, and low-blast-radius polish in this repo.
---

# Mini RPI

Use this skill to keep small changes fast without skipping repo rules.

## Start

- Open `README.md`.
- Open `docs/TECH_STACK.md`.
- Open `docs/RPI_METHODOLOGY.md`.
- Open `AGENTS.md`.
- Open only the focused subsystem doc that matches the tweak.

## Research

- Inspect 1-3 directly relevant files.
- Confirm the change stays inside one subsystem.
- Confirm it does not change shared data flow, persistence, or public interfaces.

## Plan

- State the intended change in one short plan.
- Name the impact surface and quick verification.
- Keep the edit local unless the task proves otherwise.

## Implement

- Patch the smallest affected slice.
- Keep changed files under the 200-line limit where possible.
- Escalate to `feature-rpi` if the change stops being local.
- Run the smallest meaningful verification for the touched behavior.
