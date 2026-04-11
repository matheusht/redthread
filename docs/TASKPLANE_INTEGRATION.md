# Taskplane & pi-subagents Integration

## Summary

RedThread now has both packages installed project-locally through Pi:

- `taskplane`
- `pi-subagents`

These serve different roles.

## Recommendation

Use **Taskplane as the primary autonomous multi-agent orchestration layer** for engineering tasks in this repository.

Use **pi-subagents as the lightweight interactive delegation layer** inside a Pi session.

In short:

- **Taskplane** = durable task packets, batch orchestration, reviewer/merger checkpoints, git worktree isolation
- **pi-subagents** = fast ad hoc delegation, chains, parallel spot research, TUI agent management

## Why Taskplane fits RedThread better

Taskplane aligns well with RedThread's repo constraints:

1. **Persistent task packets**
   - RedThread already emphasizes Research → Plan → Implement.
   - Taskplane's `PROMPT.md` + `STATUS.md` model gives durable state across long-running work.

2. **Worktree isolation**
   - RedThread has sensitive areas like autoresearch, promotion, telemetry, and evaluation.
   - Taskplane isolates work in git worktrees and merges through a dedicated orchestration flow.

3. **Reviewer and merger roles**
   - This matches RedThread's need for explicit gates around safety-sensitive code.

4. **Autonomous batch execution**
   - Best fit when one larger objective must be decomposed into several bounded coding tasks.

## Why pi-subagents still matters

pi-subagents is still valuable, but mostly for:

- quick researcher/planner/worker delegation in one Pi session
- parallel reconnaissance
- interactive experimentation
- lightweight multi-agent use without creating a full Taskplane task packet

It is better as a tactical helper than as RedThread's main autonomous execution backbone.

## Installed local setup

### Pi package registry

Project-local package registry:

- `.pi/settings.json`

Installed packages:

- `npm:taskplane`
- `npm:pi-subagents`

### Taskplane files

Generated/scaffolded files:

- `.pi/taskplane.json`
- `.pi/taskplane-config.json`
- `.pi/agents/supervisor.md`
- `.pi/agents/task-worker.md`
- `.pi/agents/task-reviewer.md`
- `.pi/agents/task-merger.md`
- `docs/taskplane-tasks/CONTEXT.md`

### Runtime/install paths

Project-local npm packages live under:

- `.pi/npm/`

## Current RedThread-specific Taskplane configuration

Taskplane is configured with:

- task root: `docs/taskplane-tasks`
- verification commands:
  - `uv run pytest`
  - `uv run ruff check src tests`
  - `uv run mypy src`
- standards/docs references:
  - `README.md`
  - `AGENTS.md`
  - `docs/TECH_STACK.md`
  - `docs/RPI_METHODOLOGY.md`
  - `docs/AGENT_ARCHITECTURE.md`
  - `docs/PHASE_REGISTRY.md`

## How to use it

### Taskplane

Run the local CLI binary:

```bash
./.pi/npm/node_modules/.bin/taskplane doctor
./.pi/npm/node_modules/.bin/taskplane dashboard --no-open
```

Open Pi and use orchestrator commands:

```text
/orch
/orch-plan all
/orch all
/orch-status
```

### pi-subagents

After opening `pi`, use commands such as:

```text
/run planner create a plan for the current task
/parallel researcher "inspect docs" -> reviewer "challenge assumptions"
/agents
/subagents-status
```

## Suggested operating model for RedThread

### Best near-term model

1. Human or principal agent defines the engineering objective.
2. Create one or more Taskplane task packets under `docs/taskplane-tasks/`.
3. Use Taskplane to execute workers/reviewers/mergers autonomously.
4. Use pi-subagents only for quick supporting delegation during live investigation.

### Good first use cases

- medium/large refactors in `src/redthread/research/`
- adding new evaluation/reporting surfaces
- scoped orchestration improvements with explicit verification
- documentation-backed implementation work spanning multiple files

### Avoid first

- production runtime behavior that still lacks sealed tests
- broad mutation of safety gates, promotion logic, or review boundaries in one batch
- tasks with unclear acceptance criteria

## Verification completed

The following setup checks were run:

```bash
pi install -l npm:taskplane
pi install -l npm:pi-subagents
./.pi/npm/node_modules/.bin/taskplane doctor
```

Taskplane doctor passed successfully.
