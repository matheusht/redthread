# RPI Methodology & Context Protocols

This source of truth dictates how the Antigravity Agent interacts with RedThread configuration files and codebase. Maintain Context Budget below 40% at all times.

## 1. Research (0–25% Context)
* **Goal**: Find specific files, code snippets, and metrics.
* **Requirements**:
  * Use Semantic Search and selective reading.
  * Delegate extensive searches to Subagents (using Opus 4.6).
  * Output: Paths, lines, and an objective summary. No code modification.

## 2. Plan (25–35% Context)
* **Goal**: Define behavior before execution.
* **Requirements**:
  * Map out specific algorithmic logic (e.g., TAP branching or MCTS escalation steps).
  * Identify testing metrics via the JudgeAgent or G-Eval rubrics.
  * Use the Gap-Check skill prior to concluding the plan.
* **Output**: A structured plan artifact requesting User Approval.

## 3. Implement (35–40% Context)
* **Goal**: Execute using constrained, highly-isolated context.
* **Requirements**:
  * Apply step-by-step diffs.
  * Test components iteratively (e.g., test a single PAIR node before mapping LangGraph).
  * Do not inflate principal agent context. Offload complex implementations to Subagents.

### The Dumb Zone (>40% Context)
If context utilization reaches 40%, the agent is required to halt operations, summarize current understandings, discard irrelevant background, or push the task to a parallel scoped subagent.
