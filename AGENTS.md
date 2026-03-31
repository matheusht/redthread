# RedThread Agent Architecture

This document dictates the behavior and orchestration of the Antigravity Agent when working within the RedThread repository.

**All behavioral configurations must strictly refer to the `docs/` sources of truth.**

## 1. Core Operating Guidelines
* **Decision Matrix:** Before running *any* operation, the agent must consult [docs/AGENT_DECISION_TREE.md](docs/AGENT_DECISION_TREE.md) to identify which domain document to load based on the user's intent.
* **Working Methodology:** All tasks must follow the RPI (Research → Plan → Implement) flow outlined in [docs/RPI_METHODOLOGY.md](docs/RPI_METHODOLOGY.md). Context must not exceed 40% window utilization.

## 2. The Orchestration Workflow (Principal vs Subagents)
Antigravity operates as the **Principal Agent** inside the RedThread ecosystem. It acts identically to the LangGraph supervisor defined in Phase 1 of `phases.md`—it manages the task graph while delegating execution.

### The Principal Agent Must:
1. Clarify intent.
2. Load relevant `.agent/rules/`.
3. Read the relevant document from `docs/AGENT_DECISION_TREE.md`.
4. Trigger the correct `.agent/skills/`.

### Subagent Usage
When tasks bridge boundaries, the Principal Agent MUST delegate:
* **Research Agent (Model: Opus 4.6):** Use for sweeping file aggregation or reading large datasets. Focuses strictly on extracting context, paths, and patterns without modifying files.
* **Plan Agent / Implement Agent:** Used to isolate complex edits (e.g. creating a PersonaGenerator node) from the Principal Agent's context. Always requires explicit `.agent/skills/` procedures like TAP, PAIR, or G-Eval execution.

## 3. Mandatory Component Rules
Do not maintain rules in this document.
Always apply `.agent/rules/` for global operations. Use `.agent/skills/` for specific tasks.
