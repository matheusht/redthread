# General — Context

**Last Updated:** 2026-04-10
**Status:** Active
**Next Task ID:** TP-003

---

## Current State

This is the default task area for RedThread. Tasks that don't belong
to a specific domain area are created here.

Taskplane is configured and ready for task execution. Use `/task` for single
tasks or `/orch all` for parallel batch execution.

Taskplane is the repo's autonomous engineering orchestration layer for scoped work packets.
It should complement, not replace, RedThread's product runtime orchestration in LangGraph.

---

## Key Files

| Category | Path |
|----------|------|
| Tasks | `docs/taskplane-tasks/` |
| Package registry | `.pi/settings.json` |
| Taskplane install marker | `.pi/taskplane.json` |
| Taskplane config | `.pi/taskplane-config.json` |
| Supervisor prompt | `.pi/agents/supervisor.md` |
| Worker prompt | `.pi/agents/task-worker.md` |
| Reviewer prompt | `.pi/agents/task-reviewer.md` |
| Merger prompt | `.pi/agents/task-merger.md` |

---

## Operating Guidance

- Start from `README.md`, `AGENTS.md`, and `docs/PHASE_REGISTRY.md` before defining or running a task packet.
- Prefer one bounded objective per task packet with explicit verification commands and acceptance criteria.
- Use Taskplane for durable multi-agent execution with review/merge checkpoints.
- Use `pi-subagents` for ad hoc delegation inside an interactive Pi session when you want quick research/planning/parallel spot checks rather than a full orchestrated batch.

## Technical Debt / Future Work

- Add RedThread-specific task packet templates for research-daemon changes, evaluation changes, and orchestration-node work.
- Add area-specific task roots if the team wants separate queues for `research`, `evaluation`, or `telemetry`.
- Tune supervisor/worker/reviewer model selections once the preferred provider mix is decided.
- Queue follow-up packets for live smoke validation and richer sealed Phase 6 replay fixtures after TP-002.
